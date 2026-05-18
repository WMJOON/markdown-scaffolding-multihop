#!/usr/bin/env python3
"""msm-ontology project_md — JSONL → Markdown projection.

Writes or updates MD files for entities and instances.
The <!-- msm:generated:start --> ... <!-- msm:generated:end --> block is
regenerated. Any content after <!-- msm:generated:end --> (e.g., Notes)
is preserved.

Usage:
  python project_md.py --target REPO --cluster NAME [--apply]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GENERATED_FILE_MARKER = '<!-- msm:generated:file skill="msm-ontology" version="1.0.0" -->'
GENERATED_START = '<!-- msm:generated:start source="{source}" -->'
GENERATED_END = "<!-- msm:generated:end -->"


# ---------------------------------------------------------------------------
# JSONL helpers
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


# ---------------------------------------------------------------------------
# MD generation
# ---------------------------------------------------------------------------

def _entity_body(record: dict, source_jsonl: str) -> str:
    """Generate the generated block body for an entity."""
    source_refs = record.get("source_refs", [])
    evidence_lines = "\n".join(
        f"- [[{ref}|seed {ref.split(':')[-1]}]]" for ref in source_refs
    ) or "- (none)"

    return (
        f"**Type**: Tbox class\n\n"
        f"**Cluster**: `{record.get('cluster', '')}`\n\n"
        f"**Source evidence**:\n\n"
        f"{evidence_lines}"
    )


def _instance_body(record: dict, source_jsonl: str) -> str:
    """Generate the generated block body for an instance."""
    source_refs = record.get("source_refs", [])
    evidence_lines = "\n".join(
        f"- [[{ref}|seed {ref.split(':')[-1]}]]" for ref in source_refs
    ) or "- (none)"
    type_id = record.get("type", "")

    return (
        f"**Type**: Abox instance of [[{type_id}]]\n\n"
        f"**Cluster**: `{record.get('cluster', '')}`\n\n"
        f"**Source evidence**:\n\n"
        f"{evidence_lines}"
    )


def _build_frontmatter(record: dict) -> str:
    source_refs = record.get("source_refs", [])
    refs_yaml = "\n".join(f"  - {r}" for r in source_refs)
    if not refs_yaml:
        refs_yaml = "  []"

    lines = [
        "---",
        f"id: {record.get('id', '')}",
        f"label: {record.get('label', '')}",
        f"cluster: {record.get('cluster', '')}",
    ]
    if "kind" in record:
        lines.append(f"kind: {record['kind']}")
    if "type" in record:
        lines.append(f"type: {record['type']}")
    lines += [
        f"status: {record.get('status', 'draft')}",
        "source_refs:",
        refs_yaml,
        "---",
    ]
    return "\n".join(lines)


def _build_md(record: dict, body_fn, source_jsonl: str) -> str:
    frontmatter = _build_frontmatter(record)
    label = record.get("label", "")
    body = body_fn(record, source_jsonl)
    start_tag = GENERATED_START.format(source=source_jsonl)

    return (
        f"{GENERATED_FILE_MARKER}\n"
        f"{frontmatter}\n\n"
        f"# {label}\n\n"
        f"{start_tag}\n"
        f"{body}\n"
        f"{GENERATED_END}\n\n"
        f"## Notes\n\n"
        f"(사용자 자유 작성 영역)\n"
    )


def _update_md(existing: str, record: dict, body_fn, source_jsonl: str) -> str:
    """Update only the generated block; preserve Notes and content after end marker."""
    start_tag = GENERATED_START.format(source=source_jsonl)
    start_marker = "<!-- msm:generated:start"
    end_marker = GENERATED_END

    # Find generated block boundaries
    start_idx = existing.find(start_marker)
    end_idx = existing.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        # No existing generated block — rewrite entirely preserving content after frontmatter
        return _build_md(record, body_fn, source_jsonl)

    after_end = existing[end_idx + len(end_marker):]

    # Rebuild frontmatter + title section
    frontmatter = _build_frontmatter(record)
    label = record.get("label", "")
    body = body_fn(record, source_jsonl)

    new_content = (
        f"{GENERATED_FILE_MARKER}\n"
        f"{frontmatter}\n\n"
        f"# {label}\n\n"
        f"{start_tag}\n"
        f"{body}\n"
        f"{GENERATED_END}"
        f"{after_end}"
    )
    return new_content


def write_entity_md(md_path: Path, record: dict, entities_path: Path) -> None:
    """Write or update an entity MD file."""
    source_jsonl = str(entities_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    if md_path.exists():
        existing = md_path.read_text(encoding="utf-8")
        content = _update_md(existing, record, _entity_body, source_jsonl)
    else:
        content = _build_md(record, _entity_body, source_jsonl)
    md_path.write_text(content, encoding="utf-8")


def write_instance_md(md_path: Path, record: dict, instances_path: Path) -> None:
    """Write or update an instance MD file."""
    source_jsonl = str(instances_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    if md_path.exists():
        existing = md_path.read_text(encoding="utf-8")
        content = _update_md(existing, record, _instance_body, source_jsonl)
    else:
        content = _build_md(record, _instance_body, source_jsonl)
    md_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Batch projection
# ---------------------------------------------------------------------------

def project_cluster(target: Path, cluster: str, apply: bool) -> int:
    """Project all entities and instances for a cluster."""
    entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
    instances_path = target / "ontology" / "Abox" / cluster / "instances.jsonl"

    rc = 0
    # Entities
    for rec in _load_jsonl(entities_path):
        md_rel = rec.get("md_path")
        if not md_rel:
            continue
        md_path = target / md_rel
        if apply:
            write_entity_md(md_path, rec, entities_path)
            print(f"projected: {md_rel}")
        else:
            print(f"[dry-run] would project: {md_rel}")

    # Instances
    for rec in _load_jsonl(instances_path):
        md_rel = rec.get("md_path")
        if not md_rel:
            continue
        md_path = target / md_rel
        if apply:
            write_instance_md(md_path, rec, instances_path)
            print(f"projected: {md_rel}")
        else:
            print(f"[dry-run] would project: {md_rel}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="project_md")
    p.add_argument("--target", required=True)
    p.add_argument("--cluster", required=True)
    p.add_argument("--apply", action="store_true", default=False)
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()
    return project_cluster(target, args.cluster, args.apply)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
