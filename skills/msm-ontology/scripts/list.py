#!/usr/bin/env python3
"""msm-ontology list — list entities / relations / instances.

Usage:
  python list.py --target REPO [--cluster NAME] [--kind entity|relation|instance]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="list")
    p.add_argument("--target", required=True)
    p.add_argument("--cluster", default=None)
    p.add_argument("--kind", choices=["entity", "relation", "instance"], default=None)
    p.add_argument("--format", choices=["table", "json", "ids"], default="table")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()

    # Determine clusters
    if args.cluster:
        clusters = [args.cluster]
    else:
        tbox_root = target / "ontology" / "Tbox"
        abox_root = target / "ontology" / "Abox"
        cluster_set: set[str] = set()
        for root in (tbox_root, abox_root):
            if root.exists():
                for d in root.iterdir():
                    if d.is_dir():
                        cluster_set.add(d.name)
        clusters = sorted(cluster_set)

    results: list[dict] = []

    for cluster in clusters:
        if args.kind in (None, "entity"):
            for r in _load_jsonl(target / "ontology" / "Tbox" / cluster / "entities.jsonl"):
                r["_kind"] = "entity"
                results.append(r)
        if args.kind in (None, "relation"):
            for r in _load_jsonl(target / "ontology" / "Tbox" / cluster / "relations.jsonl"):
                r["_kind"] = "relation"
                results.append(r)
        if args.kind in (None, "instance"):
            for r in _load_jsonl(target / "ontology" / "Abox" / cluster / "instances.jsonl"):
                r["_kind"] = "instance"
                results.append(r)

    fmt = args.format
    if fmt == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif fmt == "ids":
        for r in results:
            print(r.get("id", "?"))
    else:
        # table
        header = f"{'ID':<40} {'KIND':<10} {'CLUSTER':<15} {'STATUS':<12} {'LABEL'}"
        print(header)
        print("-" * len(header))
        for r in results:
            rid = r.get("id", "?")
            kind = r.get("_kind", r.get("kind", "?"))
            cl = r.get("cluster", "?")
            st = r.get("status", "?")
            label = r.get("label", r.get("predicate", "?"))
            print(f"{rid:<40} {kind:<10} {cl:<15} {st:<12} {label}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
