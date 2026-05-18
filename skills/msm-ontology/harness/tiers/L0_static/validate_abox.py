#!/usr/bin/env python3
"""L0 static validator for Abox JSONL files.

Checks for all ontology/Abox/*/{instances}.jsonl:
- Each line is valid JSON
- Each instance has required fields
- All instance ids are unique within the file
- source_refs format: each ref matches 'evidence:seed:...'
- instance 'type' field references a valid entity id format

Empty or missing JSONL → OK.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INSTANCE_REQUIRED = ("id", "type", "label", "cluster", "status", "source_refs",
                     "created_at", "updated_at", "tool_version")

EVIDENCE_RE = re.compile(r'^evidence:seed:.+$')
INSTANCE_ID_RE = re.compile(r'^instance:.+$')
ENTITY_ID_RE = re.compile(r'^entity:.+$')


def _validate_instances(path: Path) -> list[str]:
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
        for field in INSTANCE_REQUIRED:
            if field not in obj:
                failures.append(f"{path.name} line {lineno} ({obj.get('id','?')}): missing field '{field}'")

        # id format
        oid = obj.get("id", "")
        if oid and not INSTANCE_ID_RE.match(oid):
            failures.append(f"{path.name} line {lineno}: id '{oid}' does not match 'instance:...' pattern")

        # id uniqueness
        if oid:
            if oid in seen_ids:
                failures.append(f"{path.name} line {lineno}: duplicate id '{oid}'")
            seen_ids.add(oid)

        # type format
        type_id = obj.get("type", "")
        if type_id and not ENTITY_ID_RE.match(type_id):
            failures.append(
                f"{path.name} line {lineno} ({oid}): 'type' must reference an entity id, got {type_id!r}"
            )

        # source_refs format
        for ref in obj.get("source_refs", []):
            if not EVIDENCE_RE.match(ref):
                failures.append(
                    f"{path.name} line {lineno} ({oid}): invalid source_ref format: {ref!r}"
                )

    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="validate_abox")
    p.add_argument("--target", required=True)
    return p.parse_args(argv)


def main() -> int:
    args = parse_args(sys.argv[1:])
    target = Path(args.target).resolve()
    abox_root = target / "ontology" / "Abox"

    if not abox_root.exists():
        print(f"OK: no Abox at {target} (0 clusters)")
        return 0

    all_failures: list[str] = []

    for cluster_dir in sorted(abox_root.iterdir()):
        if not cluster_dir.is_dir():
            continue
        inst_path = cluster_dir / "instances.jsonl"
        all_failures.extend(_validate_instances(inst_path))

    if all_failures:
        for f in all_failures:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"FAIL: {len(all_failures)} issue(s) in Abox", file=sys.stderr)
        return 1

    print(f"OK: Abox L0 validation passed at {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
