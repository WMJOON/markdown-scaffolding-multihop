"""Tiny workflow yaml reader used by orchestration policy modules.

Shares the same single-file approach as `msm-harness/runtime/workflow_parser.py`
but lives in orchestration so the two skills don't import each other.
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


def read_meta(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    out: dict[str, Any] = {}
    for field in ("version", "id", "category", "kind", "mode", "status", "tool"):
        m = re.search(rf"^{re.escape(field)}:\s*([^\n]+)\s*$", text, re.MULTILINE)
        if m:
            out[field] = _strip_quote(m.group(1))
    gov: dict[str, Any] = {}
    for key in ("oracle", "oracle_threshold", "max_retry"):
        m = re.search(rf"^\s+{re.escape(key)}:\s*([^\n]+)\s*$", text, re.MULTILINE)
        if m:
            v = _strip_quote(m.group(1))
            if v.lower() == "null":
                gov[key] = None
            else:
                try:
                    gov[key] = float(v) if "." in v else int(v)
                except ValueError:
                    gov[key] = v
    if gov:
        out["governance"] = gov
    return out
