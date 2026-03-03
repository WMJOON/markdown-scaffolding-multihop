"""Ralph ETL state machine coordinator.

Manages step transitions, checkpoint persistence, retry logic,
and HITL gate checks.
"""
from __future__ import annotations

import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ralph.common import (
    BatchInfo,
    Checkpoint,
    GovernanceEvent,
    RunConfig,
    RunMetrics,
    RunState,
    StepName,
    STEP_ORDER,
)
from ralph.idempotency import (
    compute_config_hash,
    compute_idempotency_key,
    compute_input_snapshot_hash,
    find_cached_checkpoint,
)
from ralph.yaml_io import dump_run_state, load_run_state


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_sha(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "git:" + result.stdout.strip()
    except Exception:
        pass
    return ""


def _next_run_id(runs_dir: Path) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"R-{today}-"
    existing = sorted(runs_dir.glob(f"{prefix}*")) if runs_dir.exists() else []
    seq = 1
    for p in existing:
        name = p.name
        if name.startswith(prefix):
            try:
                seq = max(seq, int(name[len(prefix):]) + 1)
            except ValueError:
                pass
    return f"{prefix}{seq:04d}"


# Step handler type: (root, state, config, run_dir, apply) -> state
StepHandler = Callable[[Path, RunState, RunConfig, Path, bool], RunState]

# Will be populated by register_steps() after all step modules are imported
STEP_HANDLERS: Dict[StepName, StepHandler] = {}


def register_step(step: StepName, handler: StepHandler) -> None:
    STEP_HANDLERS[step] = handler


class RalphCoordinator:
    """Orchestrates the 6-step Ralph ETL pipeline."""

    def __init__(
        self,
        root: Path,
        config: RunConfig,
        apply: bool = False,
    ):
        self.root = root
        self.config = config
        self.apply = apply
        self.runs_dir = root / "archive" / "history" / "ralph-runs"

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def init_run(self, manifest_path: Path) -> RunState:
        run_id = _next_run_id(self.runs_dir)
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        input_hash = compute_input_snapshot_hash(manifest_path)
        cfg_hash = compute_config_hash(self.config)
        code_ref = _git_sha(self.root)

        state = RunState(
            ralph_run_id=run_id,
            started_at=_now_iso(),
            status=StepName.RUN_CREATED.value,
            max_retry=self.config.max_retry,
            input_snapshot_hash=input_hash,
            config_hash=cfg_hash,
            code_ref=code_ref,
            config=self.config,
            batch=BatchInfo(batch_id=f"B-{run_id[2:]}"),
        )
        self._save_state(state, run_dir)
        return state

    def resume_run(self, run_id: str) -> RunState:
        run_dir = self.runs_dir / run_id
        state_path = run_dir / "run_state.yaml"
        if not state_path.exists():
            raise FileNotFoundError(f"No run state at {state_path}")
        raw = load_run_state(state_path)
        state = self._dict_to_state(raw)
        return state

    def execute(
        self,
        state: RunState,
        manifest_path: Optional[Path] = None,
        from_step: Optional[StepName] = None,
    ) -> RunState:
        """Run the full pipeline from current position to DONE."""
        run_dir = self.runs_dir / state.ralph_run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # store manifest path for step_intake
        if manifest_path:
            (run_dir / ".manifest_path").write_text(
                str(manifest_path), encoding="utf-8"
            )

        start_idx = 0
        if from_step:
            start_idx = STEP_ORDER.index(from_step)
        elif state.checkpoints:
            last_step_name = state.checkpoints[-1].step
            for i, s in enumerate(STEP_ORDER):
                if s.value == last_step_name:
                    start_idx = i + 1
                    break

        # determine which steps to skip based on run_mode
        skip_steps = self._steps_to_skip()

        for step in STEP_ORDER[start_idx:]:
            if step in skip_steps:
                print(f"[Ralph] {step.value}: skipped (mode={self.config.run_mode})")
                continue
            state = self._execute_step(state, step, run_dir)
            if state.status == StepName.RUN_FAILED.value:
                print(f"[Ralph] RUN_FAILED at step {step.value}")
                self._save_state(state, run_dir)
                return state

        state.status = StepName.DONE.value
        self._save_state(state, run_dir)
        print(f"[Ralph] Pipeline completed: {state.ralph_run_id}")
        return state

    # ------------------------------------------------------------------
    # Step execution with retry
    # ------------------------------------------------------------------

    def _execute_step(
        self, state: RunState, step: StepName, run_dir: Path
    ) -> RunState:
        handler = STEP_HANDLERS.get(step)
        if handler is None:
            print(f"[Ralph] No handler registered for {step.value}, skipping")
            state.status = f"{step.value}_COMPLETED"
            return state

        idem_key = compute_idempotency_key(
            state.batch.batch_id if state.batch else "",
            step.value,
            state.input_snapshot_hash,
            state.config_hash,
        )

        if find_cached_checkpoint(state.checkpoints, step.value, idem_key):
            print(f"[Ralph] {step.value}: cached (idempotency hit)")
            return state

        for attempt in range(1, self.config.max_retry + 1):
            state.attempt = attempt
            state.status = f"{step.value}_IN_PROGRESS"
            self._save_state(state, run_dir)
            print(f"[Ralph] {step.value}: attempt {attempt}/{self.config.max_retry}")

            try:
                state = handler(
                    self.root, state, self.config, run_dir, self.apply
                )
                state.status = f"{step.value}_COMPLETED"
                state.checkpoints.append(
                    Checkpoint(
                        step=step.value,
                        artifact=self._step_artifact_name(step),
                        idempotency_key=idem_key,
                        completed_at=_now_iso(),
                    )
                )
                self._save_state(state, run_dir)

                # check HITL gates after each step
                gate_event = self._check_gates(state, step)
                if gate_event:
                    state.governance_events.append(gate_event)
                    self._save_state(state, run_dir)
                    print(
                        f"[Ralph] HITL gate triggered: {gate_event.gate} "
                        f"— {gate_event.reason}"
                    )

                return state

            except Exception as exc:
                state.status = f"{step.value}_FAILED"
                self._save_state(state, run_dir)
                print(f"[Ralph] {step.value} failed: {exc}")
                traceback.print_exc()
                if attempt >= self.config.max_retry:
                    state.status = StepName.RUN_FAILED.value
                    return state

        return state

    # ------------------------------------------------------------------
    # Mode-based step skipping
    # ------------------------------------------------------------------

    def _steps_to_skip(self) -> set:
        """Determine which steps to skip based on run_mode."""
        mode = self.config.run_mode
        if mode == "local":
            # local files: skip crawl (files already exist)
            return {StepName.B_CRAWL}
        elif mode == "enrich":
            # enrich: skip crawl and preprocess, only parse + place + seal
            return {StepName.B_CRAWL, StepName.C_PREPROCESS}
        return set()

    # ------------------------------------------------------------------
    # HITL gates
    # ------------------------------------------------------------------

    def _check_gates(
        self, state: RunState, step: StepName
    ) -> Optional[GovernanceEvent]:
        m = state.metrics

        # H1: cost/risk
        if m.llm_call_ratio > self.config.llm_call_ratio_limit:
            return GovernanceEvent(
                event_type="hitl_request",
                gate="H1",
                reason=f"LLM call ratio {m.llm_call_ratio:.2%} > {self.config.llm_call_ratio_limit:.0%}",
                timestamp=_now_iso(),
            )
        if m.hold_ratio > self.config.hold_ratio_limit:
            return GovernanceEvent(
                event_type="hitl_request",
                gate="H1",
                reason=f"Hold ratio {m.hold_ratio:.2%} > {self.config.hold_ratio_limit:.0%}",
                timestamp=_now_iso(),
            )
        retry_threshold = self.config.max_retry * 0.7
        if state.attempt >= retry_threshold:
            return GovernanceEvent(
                event_type="hitl_request",
                gate="H1",
                reason=f"Retry attempts {state.attempt} >= 70% of max_retry",
                timestamp=_now_iso(),
            )
        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _save_state(self, state: RunState, run_dir: Path) -> None:
        state_path = run_dir / "run_state.yaml"
        dump_run_state(state, state_path)

    def _step_artifact_name(self, step: StepName) -> str:
        return {
            StepName.A_INTAKE: "intake_manifest.yaml",
            StepName.B_CRAWL: "evidence_corpus/index/",
            StepName.C_PREPROCESS: "evidence_corpus/chunks/",
            StepName.D_PARSE: "entity_candidates.jsonl",
            StepName.E_PLACE: "placement_report.jsonl",
            StepName.F_SEAL: "seed_candidate.yaml",
        }.get(step, "")

    def _dict_to_state(self, d: Dict[str, Any]) -> RunState:
        """Reconstruct RunState from a loaded YAML dict."""
        config_d = d.get("config") or {}
        config = RunConfig(
            batch_size=int(config_d.get("batch_size", 20)),
            max_retry=int(config_d.get("max_retry", 3)),
            ambiguity_threshold=float(config_d.get("ambiguity_threshold", 0.35)),
            chunk_max_words=int(config_d.get("chunk_max_words", 400)),
            chunk_overlap_words=int(config_d.get("chunk_overlap_words", 50)),
            chunk_min_words=int(config_d.get("chunk_min_words", 40)),
            llm_call_ratio_limit=float(config_d.get("llm_call_ratio_limit", 0.05)),
            hold_ratio_limit=float(config_d.get("hold_ratio_limit", 0.20)),
            merge_alias_sim_threshold=float(config_d.get("merge_alias_sim_threshold", 0.92)),
            extend_alias_sim_threshold=float(config_d.get("extend_alias_sim_threshold", 0.80)),
            relation_embed_sim_threshold=float(config_d.get("relation_embed_sim_threshold", 0.75)),
            http_timeout=int(config_d.get("http_timeout", 40)),
        )

        batch_d = d.get("batch") or {}
        batch = BatchInfo(
            batch_id=str(batch_d.get("batch_id", "")),
            urls=batch_d.get("urls", []),
            scope_targets=batch_d.get("scope_targets", []),
            url_fingerprints=batch_d.get("url_fingerprints", []),
        )

        checkpoints = []
        for cp in d.get("checkpoints", []):
            checkpoints.append(
                Checkpoint(
                    step=str(cp.get("step", "")),
                    artifact=str(cp.get("artifact", "")),
                    idempotency_key=str(cp.get("idempotency_key", "")),
                    completed_at=str(cp.get("completed_at", "")),
                )
            )

        metrics_d = d.get("metrics") or {}
        metrics = RunMetrics(
            llm_call_count=int(metrics_d.get("llm_call_count", 0)),
            llm_call_ratio=float(metrics_d.get("llm_call_ratio", 0.0)),
            cache_hit_ratio=float(metrics_d.get("cache_hit_ratio", 0.0)),
            hold_count=int(metrics_d.get("hold_count", 0)),
            hold_ratio=float(metrics_d.get("hold_ratio", 0.0)),
            entities_processed=int(metrics_d.get("entities_processed", 0)),
            relations_processed=int(metrics_d.get("relations_processed", 0)),
        )

        return RunState(
            ralph_run_id=str(d.get("ralph_run_id", "")),
            parent_run_id=d.get("parent_run_id"),
            started_at=str(d.get("started_at", "")),
            status=str(d.get("status", "RUN_CREATED")),
            attempt=int(d.get("attempt", 1)),
            max_retry=int(d.get("max_retry", 3)),
            input_snapshot_hash=str(d.get("input_snapshot_hash", "")),
            config_hash=str(d.get("config_hash", "")),
            code_ref=str(d.get("code_ref", "")),
            batch=batch,
            config=config,
            checkpoints=checkpoints,
            metrics=metrics,
        )
