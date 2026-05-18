#!/usr/bin/env python3
"""msm-maintain analyze — generate cluster eval stats + analysis report.

Saves report to harness/reports/maintain-analysis-<run_id>.md.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

TOOL_VERSION = "msm-maintain/1.0.0"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="analyze")
    p.add_argument("--target", required=True)
    p.add_argument("--cluster", default=None)
    p.add_argument("--run-id", default=None, dest="run_id")
    return p.parse_args(argv)


def _run_id_or_new(val: str | None) -> str:
    if val:
        return val
    return _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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
    tbox = target / "ontology" / "Tbox"
    if not tbox.exists():
        return []
    return sorted(d.name for d in tbox.iterdir() if d.is_dir())


def compute_eval(target: Path, clusters: list[str]) -> list[dict]:
    results: list[dict] = []
    for cluster in sorted(clusters):
        entities = _load_jsonl(target / "ontology" / "Tbox" / cluster / "entities.jsonl")
        relations = _load_jsonl(target / "ontology" / "Tbox" / cluster / "relations.jsonl")
        instances = _load_jsonl(target / "ontology" / "Abox" / cluster / "instances.jsonl")

        status_dist: dict[str, int] = {}
        for e in entities:
            s = e.get("status", "draft")
            status_dist[s] = status_dist.get(s, 0) + 1

        ec = len(entities)
        with_refs = sum(1 for e in entities if e.get("source_refs"))
        coverage = round(with_refs / ec, 3) if ec > 0 else 0.0
        density = round(len(relations) / max(ec, 1), 3)

        results.append({
            "cluster": cluster,
            "entities": ec,
            "relations": len(relations),
            "instances": len(instances),
            "status_dist": status_dist,
            "evidence_coverage": coverage,
            "relation_density": density,
        })
    return results


def count_orphan_md(target: Path, clusters: list[str]) -> int:
    """Count md files in Tbox not referenced by any jsonl."""
    all_md_refs: set[str] = set()
    for cluster in clusters:
        for e in _load_jsonl(target / "ontology" / "Tbox" / cluster / "entities.jsonl"):
            mp = e.get("md_path", "")
            if mp:
                all_md_refs.add(mp)
    orphans = 0
    for cluster in clusters:
        md_dir = target / "ontology" / "Tbox" / cluster / "md"
        if md_dir.exists():
            for f in md_dir.glob("*.md"):
                if str(f.relative_to(target)) not in all_md_refs:
                    orphans += 1
    return orphans


def count_drift(target: Path, clusters: list[str], seed_ids: set[str]) -> int:
    """Quick drift count without full scan module import."""
    count = 0
    for cluster in clusters:
        entities = _load_jsonl(target / "ontology" / "Tbox" / cluster / "entities.jsonl")
        for e in entities:
            mp = e.get("md_path", "")
            if mp and not (target / mp).exists():
                count += 1
    return count


def build_report(target: Path, target_name: str, eval_stats: list[dict],
                  orphan_count: int, drift_count: int, seed_count: int) -> str:
    lines = [
        f'<!-- msm:generated:file skill="msm-maintain" version="1.0.0" -->',
        f"# Maintain Analysis — {target_name}",
        "",
    ]
    for stat in eval_stats:
        c = stat["cluster"]
        ec = stat["entities"]
        sd = stat["status_dist"]
        sd_parts = " / ".join(f"{k} {v}" for k, v in sorted(sd.items()))
        cov = stat["evidence_coverage"]
        with_refs = round(cov * ec)
        density = stat["relation_density"]
        lines += [
            f"## Cluster: {c}",
            "",
            f"- entities: {ec} ({sd_parts})",
            f"- relations: {stat['relations']}",
            f"- instances: {stat['instances']}",
            f"- evidence coverage: {with_refs}/{ec} ({int(cov * 100)}%)",
            f"- relation density: {density:.2f} per entity",
            "",
        ]
    lines += [
        "## Cross-cluster",
        "",
        f"- total clusters: {len(eval_stats)}",
        f"- total evidence seeds: {seed_count}",
        f"- orphan md files: {orphan_count}",
        f"- drift findings: {drift_count}",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()
    run_id = _run_id_or_new(args.run_id)

    clusters = _discover_clusters(target)
    if args.cluster:
        clusters = [c for c in clusters if c == args.cluster]

    eval_stats = compute_eval(target, clusters)

    seeds = _load_jsonl(target / "evidence" / "seeds.jsonl")
    seed_ids = {s.get("id", "") for s in seeds}

    orphan_count = count_orphan_md(target, clusters)
    drift_count = count_drift(target, clusters, seed_ids)

    target_name = target.name
    report_text = build_report(target, target_name, eval_stats, orphan_count, drift_count, len(seeds))

    # Save report
    reports_dir = target / "harness" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"maintain-analysis-{run_id}.md"
    report_path.write_text(report_text, encoding="utf-8")

    print(report_text)
    print(f"\n[analyze] Report saved: {report_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
