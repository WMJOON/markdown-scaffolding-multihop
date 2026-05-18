#!/usr/bin/env python3
"""msm-ontology mece — MECE violation detector.

Checks:
1. label_duplicate: same normalized label within a cluster
2. jaccard_overlap: label+synonyms Jaccard >= 0.7
3. cluster_boundary: relation source/target in different Tbox clusters
4. orphan_entity: source_refs empty
5. missing_md: md_path defined but file not found

Usage:
  python mece.py --target REPO [--cluster NAME]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def _jaccard(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0


def _label_tokens(record: dict) -> set[str]:
    tokens: set[str] = set()
    label = record.get("label", "").lower().strip()
    for w in label.split():
        tokens.add(w)
    for syn in record.get("synonyms", []):
        for w in syn.lower().strip().split():
            tokens.add(w)
    return tokens


# ---------------------------------------------------------------------------
# Cluster-level checks
# ---------------------------------------------------------------------------

def check_cluster(target: Path, cluster: str, jaccard_max: float = 0.7) -> list[dict]:
    """Run MECE checks for a single cluster. Returns list of violation dicts."""
    violations: list[dict] = []

    entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
    relations_path = target / "ontology" / "Tbox" / cluster / "relations.jsonl"

    entities = _load_jsonl(entities_path)

    # 1. label_duplicate
    seen_labels: dict[str, str] = {}  # norm_label -> id
    for rec in entities:
        norm = rec.get("label", "").lower().strip()
        eid = rec.get("id", "?")
        if norm in seen_labels:
            violations.append({
                "kind": "label_duplicate",
                "ids": [seen_labels[norm], eid],
                "label": norm,
                "cluster": cluster,
            })
        else:
            seen_labels[norm] = eid

    # 2. jaccard_overlap
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            a, b = entities[i], entities[j]
            tok_a = _label_tokens(a)
            tok_b = _label_tokens(b)
            j_score = _jaccard(tok_a, tok_b)
            if j_score >= jaccard_max:
                violations.append({
                    "kind": "jaccard_overlap",
                    "ids": [a.get("id", "?"), b.get("id", "?")],
                    "jaccard": round(j_score, 4),
                    "cluster": cluster,
                })

    # 3. orphan_entity
    for rec in entities:
        if not rec.get("source_refs"):
            violations.append({
                "kind": "orphan_entity",
                "id": rec.get("id", "?"),
                "cluster": cluster,
            })

    # 4. missing_md
    for rec in entities:
        md_path_rel = rec.get("md_path")
        if md_path_rel:
            full_path = target / md_path_rel
            if not full_path.exists():
                violations.append({
                    "kind": "missing_md",
                    "id": rec.get("id", "?"),
                    "md_path": md_path_rel,
                    "cluster": cluster,
                })

    # 5. cluster_boundary (relation source/target in different Tbox clusters)
    # Build global entity → cluster map
    relations = _load_jsonl(relations_path)
    # We only check against other Tbox clusters if we can find them
    tbox_root = target / "ontology" / "Tbox"
    entity_cluster_map: dict[str, str] = {}
    if tbox_root.exists():
        for cl_dir in tbox_root.iterdir():
            if cl_dir.is_dir():
                for erec in _load_jsonl(cl_dir / "entities.jsonl"):
                    eid = erec.get("id", "")
                    if eid:
                        entity_cluster_map[eid] = cl_dir.name

    for rel in relations:
        src = rel.get("source", "")
        tgt = rel.get("target", "")
        src_cl = entity_cluster_map.get(src)
        tgt_cl = entity_cluster_map.get(tgt)
        if src_cl and tgt_cl and src_cl != tgt_cl:
            violations.append({
                "kind": "cluster_boundary",
                "relation_id": rel.get("id", "?"),
                "source_cluster": src_cl,
                "target_cluster": tgt_cl,
                "cluster": cluster,
            })

    return violations


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="mece")
    p.add_argument("--target", required=True)
    p.add_argument("--cluster", default=None)
    p.add_argument("--jaccard-max", type=float, default=0.7)
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()

    if args.cluster:
        clusters = [args.cluster]
    else:
        # Discover all clusters
        tbox_root = target / "ontology" / "Tbox"
        if tbox_root.exists():
            clusters = [d.name for d in tbox_root.iterdir() if d.is_dir()]
        else:
            clusters = []

    all_violations: list[dict] = []
    for cluster in clusters:
        violations = check_cluster(target, cluster, jaccard_max=args.jaccard_max)
        if violations:
            all_violations.extend(violations)

    report = {
        "event_type": "mece_report",
        "clusters_checked": clusters,
        "violations": all_violations,
    }
    print(json.dumps(report, ensure_ascii=False))

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
