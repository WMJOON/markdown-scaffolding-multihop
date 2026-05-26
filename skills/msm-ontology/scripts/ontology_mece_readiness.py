#!/usr/bin/env python3
"""Oracle: ontology_mece_readiness

Score = (entity≥1 ? 0.25 : 0)
      + (all_source_refs ? 0.25 : 0)
      + (mece_violations==0 ? 0.25 : 0)
      + (md_projection_complete ? 0.25 : 0)

Output (stdout): JSON oracle_evaluation event.

Usage:
  python ontology_mece_readiness.py --target REPO [--cluster NAME]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import mece as _mece  # noqa: E402


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


def evaluate(target: Path, cluster: str | None = None) -> dict:
    """Return oracle evaluation result."""
    tbox_root = target / "ontology" / "Tbox"
    abox_root = target / "ontology" / "Abox"

    if cluster:
        clusters = [cluster]
    else:
        cluster_set: set[str] = set()
        for root in (tbox_root, abox_root):
            if root.exists():
                for d in root.iterdir():
                    if d.is_dir():
                        cluster_set.add(d.name)
        clusters = sorted(cluster_set)

    all_entities: list[dict] = []
    for cl in clusters:
        all_entities.extend(_load_jsonl(tbox_root / cl / "entities.jsonl"))

    # Condition 1: entity >= 1
    cond_entity = len(all_entities) >= 1

    # Condition 2: all source_refs non-empty
    cond_source_refs = all(bool(e.get("source_refs")) for e in all_entities) if all_entities else False

    # Condition 3: MECE violations == 0
    all_violations: list[dict] = []
    for cl in clusters:
        all_violations.extend(_mece.check_cluster(target, cl))
    # Filter out missing_md for score (it's tracked separately)
    mece_violations = [v for v in all_violations if v.get("kind") != "missing_md"]
    cond_mece = len(mece_violations) == 0

    # Condition 4: md projection complete (all md_path files exist)
    md_complete = True
    for entity in all_entities:
        md_rel = entity.get("md_path")
        if md_rel and not (target / md_rel).exists():
            md_complete = False
            break
    # Also check instances
    for cl in clusters:
        for inst in _load_jsonl(abox_root / cl / "instances.jsonl"):
            md_rel = inst.get("md_path")
            if md_rel and not (target / md_rel).exists():
                md_complete = False
                break
    cond_md = md_complete and bool(all_entities)

    score = (0.25 if cond_entity else 0.0) + \
            (0.25 if cond_source_refs else 0.0) + \
            (0.25 if cond_mece else 0.0) + \
            (0.25 if cond_md else 0.0)

    return {
        "event_type": "oracle_evaluation",
        "oracle": "ontology_mece_readiness",
        "score": round(score, 4),
        "details": {
            "entity_count": len(all_entities),
            "cond_entity_gte1": cond_entity,
            "cond_all_source_refs": cond_source_refs,
            "cond_mece_clean": cond_mece,
            "cond_md_projection_complete": cond_md,
            "mece_violation_count": len(mece_violations),
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="ontology_mece_readiness")
    p.add_argument("--target", required=True)
    p.add_argument("--cluster", default=None)
    return p.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    target = Path(args.target).resolve()
    result = evaluate(target, args.cluster)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
