"""Report generation: cost_report + run_report."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from ralph.common import PlacementLabel
from ralph.yaml_io import dump_yaml, load_run_state, read_jsonl


def generate_cost_report(run_dir: Path) -> str:
    """Generate cost_report.yaml content."""
    state_d = load_run_state(run_dir / "run_state.yaml")
    metrics = state_d.get("metrics", {})

    report = {
        "cost_report": {
            "run_id": state_d.get("ralph_run_id", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "llm_calls": {
                "total": metrics.get("llm_call_count", 0),
                "ratio": metrics.get("llm_call_ratio", 0.0),
                "allowed_tasks": [
                    "entity_normalization_assist",
                    "relation_type_disambiguation_assist",
                    "final_synthesis",
                ],
                "violations": 0,
            },
            "cache": {
                "embedding_hit_ratio": metrics.get("cache_hit_ratio", 0.0),
            },
            "exceptions": [],
        }
    }
    return dump_yaml(report)


def generate_run_report(run_dir: Path) -> str:
    """Generate run_report.yaml content."""
    state_d = load_run_state(run_dir / "run_state.yaml")
    metrics = state_d.get("metrics", {})

    # load placement summary
    placements = read_jsonl(run_dir / "placement_report.jsonl")
    label_counts: Dict[str, int] = {}
    for p in placements:
        label = p.get("label", "unknown")
        label_counts[label] = label_counts.get(label, 0) + 1

    # load validation results
    validations = read_jsonl(run_dir / "validation_results.jsonl")
    val_summary = []
    for v in validations:
        status = "PASS" if v.get("passed") else ("BLOCKED" if v.get("blocking") else "WARN")
        val_summary.append({
            "check": v.get("check_id", ""),
            "name": v.get("name", ""),
            "status": status,
            "details": v.get("details", ""),
        })

    report = {
        "run_report": {
            "run_id": state_d.get("ralph_run_id", ""),
            "status": state_d.get("status", ""),
            "started_at": state_d.get("started_at", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "input_snapshot_hash": state_d.get("input_snapshot_hash", ""),
            "config_hash": state_d.get("config_hash", ""),
            "code_ref": state_d.get("code_ref", ""),
            "state_transitions": [
                cp.get("step", "") for cp in state_d.get("checkpoints", [])
            ],
            "placement_summary": label_counts,
            "metrics": {
                "entities_processed": metrics.get("entities_processed", 0),
                "relations_processed": metrics.get("relations_processed", 0),
                "hold_count": metrics.get("hold_count", 0),
                "hold_ratio": metrics.get("hold_ratio", 0.0),
                "llm_call_count": metrics.get("llm_call_count", 0),
                "cache_hit_ratio": metrics.get("cache_hit_ratio", 0.0),
            },
            "validation": val_summary,
            "governance_events": state_d.get("governance_events", []),
        }
    }
    return dump_yaml(report)


def generate_reports(root: Path, run_dir: Path) -> None:
    """Generate and write both reports."""
    cost = generate_cost_report(run_dir)
    (run_dir / "cost_report.yaml").write_text(cost, encoding="utf-8")
    print(f"[Ralph] Cost report written to {run_dir / 'cost_report.yaml'}")

    run_rep = generate_run_report(run_dir)
    (run_dir / "run_report.yaml").write_text(run_rep, encoding="utf-8")
    print(f"[Ralph] Run report written to {run_dir / 'run_report.yaml'}")
