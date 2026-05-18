#!/usr/bin/env python3
"""L0 static validator for Tbox JSONL files.

Checks for all ontology/Tbox/*/{entities,relations}.jsonl:
- Each line is valid JSON
- Each entity has required fields
- All entity ids are unique within the file
- source_refs format: each ref matches 'evidence:seed:...'
- id format matches expected prefix

Empty or missing JSONL → OK.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ENTITY_REQUIRED = ("id", "label", "cluster", "kind", "status", "source_refs",
                   "created_at", "updated_at", "tool_version")
RELATION_REQUIRED = ("id", "source", "predicate", "target", "cluster", "status",
                     "source_refs", "created_at", "updated_at", "tool_version")

EVIDENCE_RE = re.compile(r'^evidence:seed:.+$')
ENTITY_ID_RE = re.compile(r'^entity:.+$')
RELATION_ID_RE = re.compile(r'^rel:.+$')


def _validate_file(path: Path, id_re: re.Pattern, required_fields: tuple) -> list[str]:
    failures: list[str] = []
    if not path.exists():
        return failures
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return failures

    seen_ids: set[str] = set()
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            failures.append(f"{path.name} line {lineno}: invalid JSON: {exc}")
            continue

        # Required fields
        for field in required_fields:
            if field not in obj:
                failures.append(f"{path.name} line {lineno} ({obj.get('id','?')}): missing field '{field}'")

        # id format
        oid = obj.get("id", "")
        if oid and not id_re.match(oid):
            failures.append(f"{path.name} line {lineno}: id '{oid}' does not match expected pattern")

        # id uniqueness
        if oid:
            if oid in seen_ids:
                failures.append(f"{path.name} line {lineno}: duplicate id '{oid}'")
            seen_ids.add(oid)

        # source_refs format
        for ref in obj.get("source_refs", []):
            if not EVIDENCE_RE.match(ref):
                failures.append(
                    f"{path.name} line {lineno} ({oid}): invalid source_ref format: {ref!r}"
                )

    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="validate_tbox")
    p.add_argument("--target", required=True)
    return p.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    target = Path(args.target).resolve()
    tbox_root = target / "ontology" / "Tbox"

    if not tbox_root.exists():
        print(f"OK: no Tbox at {target} (0 clusters)")
        return 0

    all_failures: list[str] = []

    for cluster_dir in sorted(tbox_root.iterdir()):
        if not cluster_dir.is_dir():
            continue
        ent_path = cluster_dir / "entities.jsonl"
        rel_path = cluster_dir / "relations.jsonl"

        all_failures.extend(_validate_file(ent_path, ENTITY_ID_RE, ENTITY_REQUIRED))
        all_failures.extend(_validate_file(rel_path, RELATION_ID_RE, RELATION_REQUIRED))

    if all_failures:
        for f in all_failures:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"FAIL: {len(all_failures)} issue(s) in Tbox", file=sys.stderr)
        return 1

    print(f"OK: Tbox L0 validation passed at {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
