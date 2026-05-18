#!/usr/bin/env python3
"""
graphify_to_msm.py — Graphify → MSM Semantic Lifting Adapter (Option A)

Pipeline:
  graphify-out/graph.json
      → filter file_type == "concept" (code nodes dropped)
      → god node detection (degree > mean + sigma*std → hub_candidate)
      → entity_candidates.jsonl + relation_candidates.jsonl

Usage:
  python graphify_to_msm.py graphify-out/graph.json
  python graphify_to_msm.py graphify-out/graph.json --output-dir etl-out --sigma 2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _candidate_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", s.lower()).strip("_")


def _source_doc_id(node: dict) -> str:
    sf = node.get("source_file", "")
    if sf:
        return "graphify__" + _slugify(Path(sf).stem)
    return "graphify__unknown"


def _evidence_span(node: dict) -> str:
    sf = node.get("source_file", "unknown")
    label = node.get("label", node["id"])
    return f"graphify:{sf}:{label}"


def _edge_endpoints(edge: dict) -> tuple[str, str]:
    src = edge.get("source") or edge.get("from", "")
    tgt = edge.get("target") or edge.get("to", "")
    return src, tgt


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def _god_node_ids(concept_ids: set[str], edges: list[dict], sigma: float) -> set[str]:
    degree: Counter[str] = Counter({nid: 0 for nid in concept_ids})
    for edge in edges:
        src, tgt = _edge_endpoints(edge)
        if src in concept_ids:
            degree[src] += 1
        if tgt in concept_ids:
            degree[tgt] += 1

    if not degree:
        return set()

    values = list(degree.values())
    mean = sum(values) / len(values)
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    threshold = mean + sigma * std
    return {nid for nid, d in degree.items() if d > threshold}


def convert(
    graph_path: Path,
    output_dir: Path,
    sigma: float = 2.0,
) -> dict[str, int]:
    raw = json.loads(graph_path.read_text(encoding="utf-8"))

    nodes: list[dict] = raw.get("nodes", [])
    edges: list[dict] = raw.get("edges") or raw.get("links", [])

    # --- filter: concept nodes only ---
    concept_nodes = {
        n["id"]: n for n in nodes if n.get("file_type") == "concept"
    }

    if not concept_nodes:
        print(
            "[graphify_to_msm] WARNING: no concept nodes found. "
            "Run graphify with Step 2 (LLM semantic extraction) enabled.",
            file=sys.stderr,
        )

    hub_ids = _god_node_ids(set(concept_nodes), edges, sigma)

    # --- entity candidates ---
    entity_rows: list[dict] = []
    for node_id, node in concept_nodes.items():
        tags = ["hub_candidate"] if node_id in hub_ids else []
        entity_rows.append({
            "candidate_id": _candidate_id(f"graphify:{node_id}"),
            "entity_id": _slugify(node_id),
            "entity_type": "Concept",
            "label_en": node.get("label", node_id),
            "label_ko": "",
            "aliases": [],
            "evidence_spans": [_evidence_span(node)],
            "source_doc_id": _source_doc_id(node),
            "confidence": 0.8,
            "source_refs": [],
            "relations": [],
            "tags": tags,
            "extra": {
                "leiden_community": node.get("community"),
                "leiden_community_name": node.get("community_name", ""),
                "graphify_source": str(graph_path),
            },
        })

    # --- relation candidates (concept↔concept edges only) ---
    relation_rows: list[dict] = []
    for edge in edges:
        src, tgt = _edge_endpoints(edge)
        if src not in concept_nodes or tgt not in concept_nodes:
            continue
        sf = edge.get("source_file", "unknown")
        relation_rows.append({
            "candidate_id": _candidate_id(
                f"graphify:{src}:{tgt}:{edge.get('relation', '')}"
            ),
            "source_entity_id": _slugify(src),
            "predicate": edge.get("relation") or "related_to",
            "target_entity_id": _slugify(tgt),
            "evidence_spans": [f"graphify:{sf}:{src}→{tgt}"],
            "confidence": float(edge.get("confidence", 0.7)),
        })

    # --- write ---
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "entity_candidates.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in entity_rows) + "\n",
        encoding="utf-8",
    )
    (output_dir / "relation_candidates.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in relation_rows) + "\n",
        encoding="utf-8",
    )

    stats = {
        "total_nodes": len(nodes),
        "concept_nodes": len(concept_nodes),
        "hub_candidates": len(hub_ids),
        "relations": len(relation_rows),
    }
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Graphify → MSM Semantic Lifting Adapter"
    )
    parser.add_argument(
        "graph_json",
        type=Path,
        help="Path to graphify-out/graph.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("msm-etl-out"),
        help="Output directory (default: msm-etl-out/)",
    )
    parser.add_argument(
        "--sigma",
        type=float,
        default=2.0,
        help="God node threshold in std-dev units (default: 2.0)",
    )
    args = parser.parse_args()

    if not args.graph_json.exists():
        sys.exit(f"[graphify_to_msm] ERROR: {args.graph_json} not found")

    stats = convert(args.graph_json, args.output_dir, sigma=args.sigma)

    print(f"[graphify_to_msm] input nodes  : {stats['total_nodes']}")
    print(f"[graphify_to_msm] concept nodes: {stats['concept_nodes']}")
    print(f"[graphify_to_msm] hub_candidates: {stats['hub_candidates']}")
    print(f"[graphify_to_msm] relations    : {stats['relations']}")
    print(f"[graphify_to_msm] output → {args.output_dir}/")


if __name__ == "__main__":
    main()
