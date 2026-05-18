"""Minimal text parser for the subset of workflow yaml we consume.

We avoid a pyyaml dep; the workflow yaml schema is well-defined and we only
read a handful of fields (kind, tool, pipeline, governance.*).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _strip_quote(s: str) -> str:
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def parse(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    out: dict[str, Any] = {"path": str(path), "raw": text}

    def first(field: str) -> str | None:
        m = re.search(rf"^{re.escape(field)}:\s*([^\n]+)\s*$", text, re.MULTILINE)
        return _strip_quote(m.group(1)) if m else None

    out["version"] = first("version")
    out["id"] = first("id")
    out["category"] = first("category")
    out["kind"] = first("kind")
    out["mode"] = first("mode")
    out["status"] = first("status")
    out["tool"] = first("tool")

    # governance block: scan a few specific keys
    gov: dict[str, Any] = {}
    for key in ("hitl_required", "max_retry", "oracle", "oracle_threshold"):
        m = re.search(rf"^\s+{re.escape(key)}:\s*([^\n]+)\s*$", text, re.MULTILINE)
        if m:
            v = _strip_quote(m.group(1))
            if key in ("hitl_required",):
                gov[key] = v.lower() == "true"
            elif key in ("max_retry",):
                try:
                    gov[key] = int(v)
                except ValueError:
                    gov[key] = 1
            elif key == "oracle_threshold":
                try:
                    gov[key] = float(v)
                except ValueError:
                    gov[key] = 0.85
            else:
                gov[key] = v if v.lower() != "null" else None
    out["governance"] = gov

    # cost_budget (best-effort)
    budget: dict[str, Any] = {}
    for key in ("tokens", "seconds", "power_wh"):
        m = re.search(rf"^\s+{re.escape(key)}:\s*([^\n]+)\s*$", text, re.MULTILINE)
        if m:
            v = _strip_quote(m.group(1))
            if v.lower() == "null":
                budget[key] = None
            else:
                try:
                    budget[key] = float(v) if "." in v else int(v)
                except ValueError:
                    pass
    if budget:
        out["cost_budget"] = budget

    # pipeline steps
    steps: list[dict[str, Any]] = []
    m_pipe = re.search(r"^pipeline:\s*\n((?:(?:[ \t]+[^\n]*|^[ \t]*-[^\n]*)\n)+)", text, re.MULTILINE)
    if m_pipe:
        block = m_pipe.group(1)
        cur: dict[str, Any] = {}
        for raw_line in block.splitlines():
            if not raw_line.strip():
                continue
            if re.match(r"^\s*-\s", raw_line):
                if cur:
                    steps.append(cur)
                cur = {}
                inline = re.match(r"^\s*-\s*([\w]+):\s*([^\n]+)\s*$", raw_line)
                if inline:
                    cur[inline.group(1)] = _strip_quote(inline.group(2))
                continue
            kv = re.match(r"^\s+([\w]+):\s*([^\n]+)\s*$", raw_line)
            if kv:
                cur[kv.group(1)] = _strip_quote(kv.group(2))
        if cur:
            steps.append(cur)
    out["pipeline"] = steps
    return out
