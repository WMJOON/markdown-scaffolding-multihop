#!/usr/bin/env python3
"""Oracle: maintain_drift_readiness.

Score ∈ [0,1] based on 5 checks:
  1. drift count 0           → +0.40
  2. orphan count 0          → +0.20
  3. evidence coverage avg ≥ 0.80 → +0.20
  4. relation density avg ≥ 0.5   → +0.10
  5. no broken canonical hub (canonical_root_hub.yaml exists + locked=true) → +0.10

Can be invoked standalone:
  python3 maintain_drift_readiness.py --target REPO [--run-id RUN_ID]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

TOOL_VERSION = "msm-maintain/1.0.0"
LOCKED_RE = re.compile(r'^\s*locked\s*:\s*true\s*$', re.MULTILINE)


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def _discover_clusters(target: Path) -> list[str]:
    concept_root = target / "ontology" / "explain" / "concept"
    if not concept_root.exists():
        return []
    return sorted(d.name for d in concept_root.iterdir() if d.is_dir())


def evaluate(target: Path) -> dict:
    clusters = _discover_clusters(target)

    # --- 1. drift count ---
    drift_count = 0
    for cluster in clusters:
        for e in _load_jsonl(target / "ontology" / "explain" / "concept" / cluster / "entities.jsonl"):
            mp = e.get("md_path", "")
            if mp and not (target / mp).exists():
                drift_count += 1

    # --- 2. orphan count ---
    all_md_refs: set[str] = set()
    for cluster in clusters:
        for e in _load_jsonl(target / "ontology" / "explain" / "concept" / cluster / "entities.jsonl"):
            mp = e.get("md_path", "")
            if mp:
                all_md_refs.add(mp)

    orphan_count = 0
    for cluster in clusters:
        md_dir = target / "ontology" / "explain" / "concept" / cluster
        if md_dir.exists():
            for f in md_dir.glob("*.md"):
                if str(f.relative_to(target)) not in all_md_refs:
                    orphan_count += 1

    # --- 3. evidence coverage avg ---
    coverages: list[float] = []
    for cluster in clusters:
        entities = _load_jsonl(target / "ontology" / "explain" / "concept" / cluster / "entities.jsonl")
        ec = len(entities)
        if ec > 0:
            with_refs = sum(1 for e in entities if e.get("source_refs"))
            coverages.append(with_refs / ec)
    cov_avg = sum(coverages) / len(coverages) if coverages else 0.0

    # --- 4. relation density avg ---
    densities: list[float] = []
    for cluster in clusters:
        entities = _load_jsonl(target / "ontology" / "explain" / "concept" / cluster / "entities.jsonl")
        relations = _load_jsonl(target / "ontology" / "explain" / "concept" / cluster / "relations.jsonl")
        ec = len(entities)
        densities.append(len(relations) / max(ec, 1))
    density_avg = sum(densities) / len(densities) if densities else 0.0

    # --- 5. canonical hub check ---
    hub_path = target / "canonical_root_hub.yaml"
    hub_ok = False
    if hub_path.exists():
        text = hub_path.read_text("utf-8")
        hub_ok = bool(LOCKED_RE.search(text))

    breakdown = {
        "drift_zero": 0.40 if drift_count == 0 else 0.0,
        "orphan_zero": 0.20 if orphan_count == 0 else 0.0,
        "evidence_coverage_ok": 0.20 if cov_avg >= 0.80 else 0.0,
        "relation_density_ok": 0.10 if density_avg >= 0.5 else 0.0,
        "hub_ok": 0.10 if hub_ok else 0.0,
    }

    score = sum(breakdown.values())

    return {
        "score": round(score, 3),
        "gate": "pass" if score >= 0.85 else "warn" if score >= 0.70 else "fail",
        "breakdown": breakdown,
        "metrics": {
            "drift_count": drift_count,
            "orphan_count": orphan_count,
            "evidence_coverage_avg": round(cov_avg, 3),
            "relation_density_avg": round(density_avg, 3),
            "canonical_hub_locked": hub_ok,
        },
    }


def _emit_trajectory(target: Path, run_id: str, result: dict) -> None:
    traj_dir = target / "harness" / "trajectory"
    traj_dir.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    event = {
        "run_id": run_id,
        "ts": ts,
        "event_type": "oracle_evaluation",
        "oracle": "maintain_drift_readiness",
        "score": result["score"],
        "gate": result["gate"],
        "breakdown": result["breakdown"],
        "metrics": result["metrics"],
    }
    path = traj_dir / f"run-{run_id}.jsonl"
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="maintain_drift_readiness")
    p.add_argument("--target", required=True)
    p.add_argument("--run-id", default=None)
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()
    result = evaluate(target)

    if args.run_id:
        _emit_trajectory(target, args.run_id, result)

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    gate = result["gate"]
    return 0 if gate == "pass" else 1 if gate == "warn" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
