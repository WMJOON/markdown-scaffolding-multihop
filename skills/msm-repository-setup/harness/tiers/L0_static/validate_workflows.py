#!/usr/bin/env python3
"""SPEC §8.1 + integration-SPEC §4.2: workflow yaml schema check."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

INDEX_REQUIRED_KEYS = ("workflows:", "id:", "path:", "category:", "kind:")
WORKFLOW_REQUIRED_KEYS = (
    "version:",
    "id:",
    "category:",
    "kind:",
    "mode:",
    "inputs:",
    "outputs:",
    "runtime:",
    "governance:",
)
GOVERNANCE_REQUIRED = ("hitl_required:", "max_retry:")
MODE_VALUES = {"dry-run", "apply", "validate-only"}
KIND_VALUES = {"single", "pipeline"}


def check_workflow(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errs: list[str] = []
    for k in WORKFLOW_REQUIRED_KEYS:
        if k not in text:
            errs.append(f"missing key: {k}")
    for k in GOVERNANCE_REQUIRED:
        if k not in text:
            errs.append(f"missing governance.{k}")
    m = re.search(r"\nmode:\s*([^\s\n]+)", text)
    if m and m.group(1) not in MODE_VALUES:
        errs.append(f"mode invalid: {m.group(1)}")
    m = re.search(r"\nkind:\s*([^\s\n]+)", text)
    if m:
        if m.group(1) not in KIND_VALUES:
            errs.append(f"kind invalid: {m.group(1)}")
        elif m.group(1) == "single" and not re.search(r"\ntool:\s*\S", text):
            errs.append("kind=single requires top-level tool:")
        elif m.group(1) == "pipeline" and "\npipeline:" not in text:
            errs.append("kind=pipeline requires pipeline: block")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--workflow", default=None, help="check a single yaml file")
    args = ap.parse_args()
    target = Path(args.target).resolve()

    if args.workflow:
        single = Path(args.workflow)
        if not single.is_absolute():
            single = target / single
        errs = check_workflow(single)
        if errs:
            print(f"FAIL: {single}", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print(f"OK: {single}")
        return 0

    index = target / "workflow" / "index.yaml"
    if not index.exists():
        print("FAIL: workflow/index.yaml not found", file=sys.stderr)
        return 1
    idx_text = index.read_text(encoding="utf-8")
    for k in INDEX_REQUIRED_KEYS:
        if k not in idx_text:
            print(f"FAIL: workflow/index.yaml missing {k}", file=sys.stderr)
            return 1

    yamls = [p for p in (target / "workflow").rglob("*.yaml") if p.name != "index.yaml"]
    if not yamls:
        print("FAIL: no workflow yaml under workflow/", file=sys.stderr)
        return 1
    total_errs = 0
    for p in yamls:
        errs = check_workflow(p)
        if errs:
            total_errs += len(errs)
            print(f"FAIL: {p.relative_to(target)}", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
    if total_errs:
        return 1
    print(f"OK: {len(yamls)} workflow yaml(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
