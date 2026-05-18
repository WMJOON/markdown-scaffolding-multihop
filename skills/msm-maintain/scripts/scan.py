#!/usr/bin/env python3
"""msm-maintain scan — drift / orphan / eval detection.

Outputs plan JSON to stdout and appends trajectory event to
harness/trajectory/run-<id>.jsonl when --run-id is set.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

TOOL_VERSION = "msm-maintain/1.0.0"
GENERATED_START = "<!-- msm:generated:start -->"
GENERATED_END = "<!-- msm:generated:end -->"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_id_or_new(val: str | None) -> str:
    if val:
        return val
    ts = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ts


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


def _generated_block_hash(md_text: str) -> str | None:
    """Extract text between msm:generated:start/end and return sha256 hex."""
    start = md_text.find(GENERATED_START)
    end = md_text.find(GENERATED_END)
    if start == -1 or end == -1 or end <= start:
        return None
    block = md_text[start + len(GENERATED_START):end]
    return hashlib.sha256(block.encode("utf-8")).hexdigest()


def _entity_generated_hash(entity: dict) -> str:
    """Produce a canonical hash of selected entity fields for comparison."""
    key = {k: entity.get(k) for k in ("id", "label", "cluster", "kind", "status",
                                        "synonyms", "source_refs")}
    canonical = json.dumps(key, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Scan functions
# ---------------------------------------------------------------------------

def scan_drift(target: Path, clusters: list[str], seed_ids: set[str]) -> tuple[list[dict], list[dict]]:
    """Return (findings, auto_fixes) for drift kind."""
    findings: list[dict] = []
    auto_fixes: list[dict] = []

    for cluster in clusters:
        entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
        relations_path = target / "ontology" / "Tbox" / cluster / "relations.jsonl"
        md_dir = target / "ontology" / "Tbox" / cluster / "md"

        entities = _load_jsonl(entities_path)
        relations = _load_jsonl(relations_path)

        # Build set of md_paths referenced by jsonl
        jsonl_md_paths: set[str] = set()
        for e in entities:
            mp = e.get("md_path", "")
            if mp:
                jsonl_md_paths.add(mp)

        # md files on disk
        md_files_on_disk: set[Path] = set()
        if md_dir.exists():
            md_files_on_disk = {f for f in md_dir.glob("*.md") if f.is_file()}

        # jsonl_without_md: entry in jsonl but file missing
        for e in entities:
            mp = e.get("md_path", "")
            if not mp:
                continue
            full = target / mp
            if not full.exists():
                finding = {
                    "kind": "jsonl_without_md",
                    "id": e.get("id", "?"),
                    "cluster": cluster,
                    "expected_md": mp,
                }
                findings.append(finding)
                auto_fixes.append({
                    "action": "create_md_placeholder",
                    "path": mp,
                    "for_id": e.get("id", "?"),
                    "label": e.get("label", ""),
                    "cluster": cluster,
                })

        # md_without_jsonl: md file exists but no jsonl entry references it
        for md_file in sorted(md_files_on_disk):
            rel = str(md_file.relative_to(target))
            if rel not in jsonl_md_paths:
                findings.append({
                    "kind": "md_without_jsonl",
                    "cluster": cluster,
                    "path": rel,
                })

        # stale_generated_block: block hash differs from entity hash
        for e in entities:
            mp = e.get("md_path", "")
            if not mp:
                continue
            full = target / mp
            if not full.exists():
                continue
            md_text = full.read_text("utf-8")
            block_hash = _generated_block_hash(md_text)
            if block_hash is None:
                continue  # no generated block — skip
            expected_hash = _entity_generated_hash(e)
            if block_hash != expected_hash:
                findings.append({
                    "kind": "stale_generated_block",
                    "id": e.get("id", "?"),
                    "cluster": cluster,
                    "path": mp,
                })

        # evidence_dangling: source_refs reference non-existent seeds
        for e in entities:
            for ref in e.get("source_refs", []):
                if ref.startswith("evidence:seed:") and ref not in seed_ids:
                    findings.append({
                        "kind": "evidence_dangling",
                        "id": e.get("id", "?"),
                        "cluster": cluster,
                        "ref": ref,
                    })

        # cluster_mismatch: jsonl cluster field != directory cluster
        for e in entities:
            if e.get("cluster", cluster) != cluster:
                findings.append({
                    "kind": "cluster_mismatch",
                    "id": e.get("id", "?"),
                    "directory_cluster": cluster,
                    "jsonl_cluster": e.get("cluster"),
                })

    # Stable sort
    findings.sort(key=lambda x: (x.get("kind", ""), x.get("id", ""), x.get("path", "")))
    auto_fixes.sort(key=lambda x: (x.get("action", ""), x.get("path", "")))
    return findings, auto_fixes


def scan_orphan(target: Path, clusters: list[str]) -> list[dict]:
    """Return findings for orphan kind."""
    findings: list[dict] = []

    # Collect all md_path refs from all jsonl
    all_md_refs: set[str] = set()
    for cluster in clusters:
        entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
        for e in _load_jsonl(entities_path):
            mp = e.get("md_path", "")
            if mp:
                all_md_refs.add(mp)

    # md_orphan: md files in Tbox/.../md/ not referenced by any jsonl
    for cluster in clusters:
        md_dir = target / "ontology" / "Tbox" / cluster / "md"
        if not md_dir.exists():
            continue
        for md_file in sorted(md_dir.glob("*.md")):
            rel = str(md_file.relative_to(target))
            if rel not in all_md_refs:
                findings.append({
                    "kind": "md_orphan",
                    "cluster": cluster,
                    "path": rel,
                })

    # seed_orphan: evidence/md/*.md not in seeds.jsonl
    seeds_path = target / "evidence" / "seeds.jsonl"
    seeds = _load_jsonl(seeds_path)
    seed_md_paths: set[str] = {s.get("md_path", "") for s in seeds}
    evidence_md_dir = target / "evidence" / "md"
    if evidence_md_dir.exists():
        for md_file in sorted(evidence_md_dir.glob("*.md")):
            rel = str(md_file.relative_to(target))
            if rel not in seed_md_paths:
                findings.append({
                    "kind": "seed_orphan",
                    "path": rel,
                })

    # no_incoming_relation: accepted+ entity with no in/out relations
    for cluster in clusters:
        entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
        relations_path = target / "ontology" / "Tbox" / cluster / "relations.jsonl"
        entities = _load_jsonl(entities_path)
        relations = _load_jsonl(relations_path)

        connected_ids: set[str] = set()
        for r in relations:
            s = r.get("subject_id", "")
            o = r.get("object_id", "")
            if s:
                connected_ids.add(s)
            if o:
                connected_ids.add(o)

        ACCEPTED_PLUS = {"accepted", "stable"}
        for e in entities:
            if e.get("status", "") in ACCEPTED_PLUS:
                eid = e.get("id", "")
                if eid and eid not in connected_ids:
                    findings.append({
                        "kind": "no_incoming_relation",
                        "id": eid,
                        "cluster": cluster,
                    })

    findings.sort(key=lambda x: (x.get("kind", ""), x.get("id", ""), x.get("path", "")))
    return findings


def scan_eval(target: Path, clusters: list[str]) -> list[dict]:
    """Return per-cluster eval stats."""
    results: list[dict] = []
    for cluster in sorted(clusters):
        entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
        relations_path = target / "ontology" / "Tbox" / cluster / "relations.jsonl"
        instances_path = target / "ontology" / "Abox" / cluster / "instances.jsonl"

        entities = _load_jsonl(entities_path)
        relations = _load_jsonl(relations_path)
        instances = _load_jsonl(instances_path)

        status_dist: dict[str, int] = {}
        for e in entities:
            s = e.get("status", "draft")
            status_dist[s] = status_dist.get(s, 0) + 1

        with_refs = sum(1 for e in entities if e.get("source_refs"))
        ec = len(entities)
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="scan")
    p.add_argument("--target", required=True)
    p.add_argument("--cluster", default=None)
    p.add_argument("--kind", default="all", choices=["drift", "orphan", "eval", "all"])
    p.add_argument("--run-id", default=None, dest="run_id")
    return p.parse_args(argv)


def _emit_trajectory(target: Path, run_id: str, plan: dict) -> None:
    traj_dir = target / "harness" / "trajectory"
    traj_dir.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    event = {
        "run_id": run_id,
        "ts": ts,
        "event_type": "scan_complete",
        "plan_id": plan["plan_id"],
        "drift_count": len(plan["findings"].get("drift", [])),
        "orphan_count": len(plan["findings"].get("orphan", [])),
        "auto_fixes_count": len(plan.get("auto_fixes", [])),
    }
    path = traj_dir / f"run-{run_id}.jsonl"
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    finally:
        os.close(fd)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()
    run_id = _run_id_or_new(args.run_id)
    plan_id = f"maintain-{run_id}"

    clusters = _discover_clusters(target)
    if args.cluster:
        clusters = [c for c in clusters if c == args.cluster]

    # Load seed ids once
    seeds = _load_jsonl(target / "evidence" / "seeds.jsonl")
    seed_ids: set[str] = {s.get("id", "") for s in seeds}

    kinds = ["drift", "orphan", "eval"] if args.kind == "all" else [args.kind]

    findings: dict = {}
    auto_fixes: list[dict] = []
    hitl_required: list[dict] = []

    if "drift" in kinds:
        df, af = scan_drift(target, clusters, seed_ids)
        findings["drift"] = df
        auto_fixes.extend(af)
        # stale_generated_block always goes to hitl
        for f in df:
            if f["kind"] == "stale_generated_block":
                hitl_required.append({
                    "reason": "stale_generated_block",
                    "path": f.get("path", ""),
                    "id": f.get("id", ""),
                    "cluster": f.get("cluster", ""),
                })
        # Remove stale_block auto_fixes (none added, but ensure no overlap)
        auto_fixes = [a for a in auto_fixes if a.get("action") != "rewrite_generated_block"]

    if "orphan" in kinds:
        findings["orphan"] = scan_orphan(target, clusters)

    if "eval" in kinds:
        findings["eval"] = scan_eval(target, clusters)

    plan = {
        "plan_id": plan_id,
        "target": str(target),
        "scans_performed": kinds,
        "findings": findings,
        "auto_fixes": auto_fixes,
        "hitl_required": hitl_required,
    }

    json.dump(plan, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

    _emit_trajectory(target, run_id, plan)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
