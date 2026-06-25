#!/usr/bin/env python3
"""msm-maintain rewrite — apply auto_fixes from a scan plan.

Only applies create_md_placeholder actions.
Writes rewrite log to agent-context/work-memory/insight-record/<run_id>__rewrite.md.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

TOOL_VERSION = "msm-maintain/1.0.0"
MAX_AUTO_FIXES = 100

PLACEHOLDER_TEMPLATE = """\
<!-- msm:generated:file skill="msm-maintain" version="1.0.0" -->
# {label}

> Auto-generated placeholder. Populate with entity description.

**ID**: `{entity_id}`
**Cluster**: `{cluster}`
**Status**: draft
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rewrite")
    p.add_argument("--target", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--apply", action="store_true", default=False)
    p.add_argument("--run-id", default=None, dest="run_id")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    target = Path(args.target).resolve()
    plan_path = Path(args.plan).resolve()

    try:
        plan = json.loads(plan_path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot read plan: {e}", file=sys.stderr)
        return 1

    auto_fixes = plan.get("auto_fixes", [])
    run_id = args.run_id or plan.get("plan_id", _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))

    # AC-MN-8: bulk rewrite guard
    if len(auto_fixes) >= MAX_AUTO_FIXES:
        print(f"HITL_REQUIRED: auto_fixes count={len(auto_fixes)} >= {MAX_AUTO_FIXES} (bulk_rewrite_volume)", file=sys.stderr)
        print(json.dumps({
            "hitl_request": "bulk_rewrite_volume",
            "auto_fixes_count": len(auto_fixes),
            "threshold": MAX_AUTO_FIXES,
        }, ensure_ascii=False))
        return 100

    applied: list[dict] = []
    skipped: list[dict] = []
    errors: list[dict] = []

    for fix in auto_fixes:
        action = fix.get("action", "")
        if action == "create_md_placeholder":
            rel_path = fix.get("path", "")
            entity_id = fix.get("for_id", "?")
            label = fix.get("label", entity_id)
            cluster = fix.get("cluster", "")
            full = target / rel_path

            if full.exists():
                skipped.append({"action": action, "path": rel_path, "reason": "already_exists"})
                continue

            content = PLACEHOLDER_TEMPLATE.format(
                label=label,
                entity_id=entity_id,
                cluster=cluster,
            )

            if args.apply:
                full.parent.mkdir(parents=True, exist_ok=True)
                full.write_text(content, encoding="utf-8")
                applied.append({"action": action, "path": rel_path, "for_id": entity_id})
            else:
                skipped.append({"action": action, "path": rel_path, "reason": "dry_run"})
        else:
            skipped.append({"action": action, "path": fix.get("path", "?"), "reason": "unsupported"})

    # Write rewrite log
    if args.apply:
        ts = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        log_dir = target / "agent-context" / "work-memory" / "insight-record"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{run_id}__rewrite.md"
        lines = [
            f"<!-- msm:generated:file skill=\"msm-maintain\" version=\"1.0.0\" -->",
            f"# Rewrite Log — {run_id}",
            f"",
            f"**Target**: `{target}`  ",
            f"**Plan**: `{plan_path}`  ",
            f"**Timestamp**: {ts}  ",
            f"",
            f"## Applied ({len(applied)})",
            "",
        ]
        for a in applied:
            lines.append(f"- `{a['action']}` → `{a['path']}` (id: `{a['for_id']}`)")
        lines += ["", f"## Skipped ({len(skipped)})", ""]
        for s in skipped:
            lines.append(f"- `{s['action']}` `{s['path']}` — {s['reason']}")
        log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = {
        "run_id": run_id,
        "applied": applied,
        "skipped": skipped,
        "errors": errors,
        "dry_run": not args.apply,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
