#!/usr/bin/env python3
"""msm-ontology add — register entity / relation / instance into JSONL.

Usage (via CLI wrapper):
  msm-ontology add --target REPO --cluster NAME
    (--entity LABEL [...] | --relation LABEL --source ID --target-id ID
     | --instance LABEL --type ID)
    --evidence evidence:seed:XYZ [...]
    [--status draft|accepted|stable|deprecated]
    [--apply]
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import id_utils  # noqa: E402
import mece as _mece  # noqa: E402  (for label_duplicate check)
import project_md as _proj  # noqa: E402

TOOL_VERSION = "msm-ontology/1.1.0"
TODAY = datetime.date.today().isoformat()


# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def _log(msg: str, level: str = "info") -> None:
    """Log to stderr with consistent prefix."""
    prefix = {"info": "[*]", "ok": "[+]", "warn": "[!]", "err": "[x]"}[level]
    print(f"{prefix} {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# Atomic append helper
# ---------------------------------------------------------------------------

def _atomic_append(path: Path, record: dict) -> None:
    """Atomically append a JSON line to path."""
    line = json.dumps(record, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


# ---------------------------------------------------------------------------
# JSONL readers
# ---------------------------------------------------------------------------

def _load_records(path: Path) -> list[dict]:
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


def _existing_ids(path: Path) -> set[str]:
    return {r.get("id", "") for r in _load_records(path)}


# ---------------------------------------------------------------------------
# Entity add
# ---------------------------------------------------------------------------

def add_entities(
    target: Path,
    cluster: str,
    labels: list[str],
    evidence: list[str],
    status: str,
    apply: bool,
) -> int:
    """Add one or more entities. Returns exit code."""
    entities_path = target / "ontology" / "Tbox" / cluster / "entities.jsonl"
    existing = _load_records(entities_path)
    existing_ids = {r.get("id", "") for r in existing}
    existing_labels_norm = {r.get("label", "").lower().strip() for r in existing}

    added_count = 0
    skipped_count = 0
    failed_count = 0
    rc = 0

    if apply:
        _log(f"adding {len(labels)} entities to cluster '{cluster}'")

    for i, label in enumerate(labels, start=1):
        label_norm = label.lower().strip()

        # MECE: label duplicate check
        if label_norm in existing_labels_norm:
            report = {
                "event_type": "mece_report",
                "cluster": cluster,
                "violations": [
                    {
                        "kind": "label_duplicate",
                        "label": label,
                        "cluster": cluster,
                    }
                ],
            }
            print(json.dumps(report))
            if apply:
                _log(f"({i}/{len(labels)}) skip: label_duplicate '{label}' in cluster '{cluster}'", "warn")
            skipped_count += 1
            rc = 1
            continue

        entity_id = id_utils.make_entity_id(label, existing_ids)
        snake = id_utils.to_snake(label)
        md_rel = f"ontology/Tbox/{cluster}/md/{snake}.md"

        record: dict = {
            "id": entity_id,
            "label": label,
            "cluster": cluster,
            "kind": "class",
            "status": status,
            "md_path": md_rel,
            "source_refs": evidence,
            "synonyms": [],
            "created_at": TODAY,
            "updated_at": TODAY,
            "tool_version": TOOL_VERSION,
        }

        if not apply:
            print(json.dumps({"event_type": "plan_entity_add", "record": record}))
        else:
            _log(f"({i}/{len(labels)}) {entity_id} ← '{label}'")
            try:
                _atomic_append(entities_path, record)
                existing_ids.add(entity_id)
                existing_labels_norm.add(label_norm)
                existing.append(record)
                # md projection
                md_path = target / md_rel
                _proj.write_entity_md(md_path, record, entities_path)
                _log(f"({i}/{len(labels)}) wrote {md_rel}", "ok")
                print(json.dumps({"event_type": "entity_added", "id": entity_id, "md_path": md_rel}))
                added_count += 1
            except Exception as e:
                _log(f"({i}/{len(labels)}) error: {label} — {e}", "err")
                failed_count += 1
                rc = 1

    if apply:
        _log(f"summary: {added_count} added, {skipped_count} skipped, {failed_count} failed")

    return rc


# ---------------------------------------------------------------------------
# Relation add
# ---------------------------------------------------------------------------

def add_relation(
    target: Path,
    cluster: str,
    label: str,
    source_id: str,
    target_id: str,
    evidence: list[str],
    status: str,
    apply: bool,
) -> int:
    """Add a relation. Returns exit code."""
    relations_path = target / "ontology" / "Tbox" / cluster / "relations.jsonl"
    existing_ids = _existing_ids(relations_path)

    rel_id = id_utils.make_relation_id(source_id, label, target_id, existing_ids)

    record: dict = {
        "id": rel_id,
        "source": source_id,
        "predicate": label,
        "target": target_id,
        "cluster": cluster,
        "status": status,
        "md_path": None,
        "source_refs": evidence,
        "created_at": TODAY,
        "updated_at": TODAY,
        "tool_version": TOOL_VERSION,
    }

    if not apply:
        print(json.dumps({"event_type": "plan_relation_add", "record": record}))
    else:
        _log(f"adding relation '{label}' ({source_id} → {target_id})")
        try:
            _atomic_append(relations_path, record)
            _log(f"relation_added: {rel_id}", "ok")
            print(json.dumps({"event_type": "relation_added", "id": rel_id}))
        except Exception as e:
            _log(f"error: {label} — {e}", "err")
            return 1

    return 0


# ---------------------------------------------------------------------------
# Instance add
# ---------------------------------------------------------------------------

def add_instance(
    target: Path,
    cluster: str,
    label: str,
    type_id: str,
    evidence: list[str],
    status: str,
    apply: bool,
) -> int:
    """Add an instance. Returns exit code."""
    instances_path = target / "ontology" / "Abox" / cluster / "instances.jsonl"
    existing_ids = _existing_ids(instances_path)

    instance_id = id_utils.make_instance_id(label, existing_ids)
    snake = id_utils.to_snake(label)
    md_rel = f"ontology/Abox/{cluster}/md/{snake}.md"

    record: dict = {
        "id": instance_id,
        "type": type_id,
        "label": label,
        "cluster": cluster,
        "status": status,
        "md_path": md_rel,
        "source_refs": evidence,
        "created_at": TODAY,
        "updated_at": TODAY,
        "tool_version": TOOL_VERSION,
    }

    if not apply:
        print(json.dumps({"event_type": "plan_instance_add", "record": record}))
    else:
        _log(f"adding instance '{label}' (type: {type_id})")
        try:
            _atomic_append(instances_path, record)
            # md projection
            md_path = target / md_rel
            _proj.write_instance_md(md_path, record, instances_path)
            _log(f"instance_added: {instance_id} → {md_rel}", "ok")
            print(json.dumps({"event_type": "instance_added", "id": instance_id, "md_path": md_rel}))
        except Exception as e:
            _log(f"error: {label} — {e}", "err")
            return 1

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="add")
    p.add_argument("--target", default=".", help="KB root")
    p.add_argument("--cluster", required=True)
    # Mutually exclusive modes
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--entity", nargs="+", metavar="LABEL", dest="entity_labels")
    mode.add_argument("--relation", metavar="LABEL", dest="relation_label")
    mode.add_argument("--instance", metavar="LABEL", dest="instance_label")
    # Relation options
    p.add_argument("--source", dest="rel_source", metavar="ID")
    p.add_argument("--target-id", dest="rel_target_id", metavar="ID")
    # Instance options
    p.add_argument("--type", dest="instance_type", metavar="ID")
    # Common
    p.add_argument("--evidence", nargs="+", default=[], metavar="URI")
    p.add_argument("--status", default="draft",
                   choices=["draft", "accepted", "stable", "deprecated"])
    p.add_argument("--apply", action="store_true", default=False)
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    # AC-ON-5: evidence required
    if not args.evidence:
        _log("source_refs_missing — --evidence is required", "err")
        return 1

    target = Path(args.target).resolve()

    if args.entity_labels:
        return add_entities(
            target=target,
            cluster=args.cluster,
            labels=args.entity_labels,
            evidence=args.evidence,
            status=args.status,
            apply=args.apply,
        )

    elif args.relation_label:
        # AC-ON-2: --source and --target-id required
        if not args.rel_source or not args.rel_target_id:
            _log("--source and --target-id are required for --relation", "err")
            return 2
        return add_relation(
            target=target,
            cluster=args.cluster,
            label=args.relation_label,
            source_id=args.rel_source,
            target_id=args.rel_target_id,
            evidence=args.evidence,
            status=args.status,
            apply=args.apply,
        )

    elif args.instance_label:
        if not args.instance_type:
            _log("--type is required for --instance", "err")
            return 2
        return add_instance(
            target=target,
            cluster=args.cluster,
            label=args.instance_label,
            type_id=args.instance_type,
            evidence=args.evidence,
            status=args.status,
            apply=args.apply,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
