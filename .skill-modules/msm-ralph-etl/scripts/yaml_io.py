"""Minimal YAML reader/writer using only stdlib.

Handles the specific YAML shapes used by Ralph: flat scalars, lists, nested
dicts (1-level), and list-of-dicts for relations/checkpoints.

For full YAML fidelity we rely on json for intermediate artifacts.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Union


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    if any(c in s for c in (":", "#", "{", "}", "[", "]", ",", "&", "*",
                            "?", "|", "-", "<", ">", "=", "!", "%", "@",
                            "`", "\n")):
        return json.dumps(s, ensure_ascii=False)
    if s in ("true", "false", "null", "yes", "no", "on", "off",
             "True", "False", "Null", "Yes", "No", "On", "Off"):
        return json.dumps(s, ensure_ascii=False)
    if not s:
        return '""'
    return s


def dump_yaml(data: Any, indent: int = 0) -> str:
    """Serialize a dict / list / scalar to a YAML string."""
    prefix = "  " * indent
    lines: List[str] = []

    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(dump_yaml(val, indent + 1))
            elif isinstance(val, list):
                lines.append(f"{prefix}{key}:")
                if not val:
                    lines[-1] += " []"
                else:
                    for item in val:
                        if isinstance(item, dict):
                            first = True
                            for k, v in item.items():
                                if first:
                                    lines.append(
                                        f"{prefix}  - {k}: {_yaml_scalar(v)}"
                                    )
                                    first = False
                                else:
                                    lines.append(
                                        f"{prefix}    {k}: {_yaml_scalar(v)}"
                                    )
                        else:
                            lines.append(
                                f"{prefix}  - {_yaml_scalar(item)}"
                            )
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(val)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append(dump_yaml(item, indent))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
    else:
        lines.append(f"{prefix}{_yaml_scalar(data)}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reader
# ---------------------------------------------------------------------------

_SCALAR_RE = re.compile(
    r"^(?P<indent>\s*)(?P<key>[A-Za-z_][A-Za-z0-9_]*):\s*(?P<value>.*)$"
)
_LIST_ITEM_RE = re.compile(r"^(?P<indent>\s*)-\s*(?P<rest>.*)$")


def _parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if not raw or raw == "null":
        return None
    if raw in ("true", "True", "yes"):
        return True
    if raw in ("false", "False", "no"):
        return False
    if raw.startswith('"') and raw.endswith('"'):
        return json.loads(raw)
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def load_yaml(text: str) -> Dict[str, Any]:
    """Parse a simple YAML string into a dict.

    Supports: flat key-value, nested dicts (indent-based), lists of scalars,
    and lists of dicts (``- key: val`` form).  Enough for Ralph run state
    and intake manifest files.
    """
    result: Dict[str, Any] = {}
    lines = text.splitlines()
    idx = 0

    def _parse_block(base_indent: int) -> Dict[str, Any]:
        nonlocal idx
        block: Dict[str, Any] = {}
        while idx < len(lines):
            line = lines[idx]
            if not line.strip() or line.strip().startswith("#"):
                idx += 1
                continue
            cur_indent = len(line) - len(line.lstrip(" "))
            if cur_indent < base_indent:
                break
            if cur_indent > base_indent:
                # should not happen at top level, skip
                idx += 1
                continue

            m = _SCALAR_RE.match(line)
            if m:
                key = m.group("key")
                val_raw = m.group("value").strip()
                idx += 1
                if val_raw == "" or val_raw.endswith(":"):
                    # nested block or list starts on next line
                    if idx < len(lines):
                        next_line = lines[idx]
                        next_indent = len(next_line) - len(next_line.lstrip(" "))
                        if next_indent > cur_indent:
                            if _LIST_ITEM_RE.match(next_line):
                                block[key] = _parse_list(next_indent)
                            else:
                                block[key] = _parse_block(next_indent)
                        else:
                            block[key] = None
                    else:
                        block[key] = None
                elif val_raw == "[]":
                    block[key] = []
                elif val_raw.startswith("[") and val_raw.endswith("]"):
                    # inline list
                    inner = val_raw[1:-1]
                    block[key] = [_parse_scalar(x) for x in inner.split(",")]
                else:
                    block[key] = _parse_scalar(val_raw)
            else:
                idx += 1
        return block

    def _parse_list(base_indent: int) -> List[Any]:
        nonlocal idx
        items: List[Any] = []
        while idx < len(lines):
            line = lines[idx]
            if not line.strip() or line.strip().startswith("#"):
                idx += 1
                continue
            cur_indent = len(line) - len(line.lstrip(" "))
            if cur_indent < base_indent:
                break

            m = _LIST_ITEM_RE.match(line)
            if m:
                rest = m.group("rest").strip()
                item_indent = len(m.group("indent"))
                if ":" in rest:
                    # dict item  "- key: val"
                    d: Dict[str, Any] = {}
                    k, v = rest.split(":", 1)
                    d[k.strip()] = _parse_scalar(v)
                    idx += 1
                    # continuation keys for same dict
                    while idx < len(lines):
                        cline = lines[idx]
                        if not cline.strip():
                            idx += 1
                            continue
                        ci = len(cline) - len(cline.lstrip(" "))
                        if ci <= item_indent:
                            break
                        if _LIST_ITEM_RE.match(cline):
                            break
                        cm = _SCALAR_RE.match(cline)
                        if cm:
                            d[cm.group("key")] = _parse_scalar(
                                cm.group("value")
                            )
                            idx += 1
                        else:
                            idx += 1
                    items.append(d)
                else:
                    items.append(_parse_scalar(rest))
                    idx += 1
            else:
                break
        return items

    result = _parse_block(0)
    return result


# ---------------------------------------------------------------------------
# RunState I/O
# ---------------------------------------------------------------------------

def run_state_to_dict(state: Any) -> Dict[str, Any]:
    """Convert a RunState dataclass to a plain dict for YAML serialization."""
    from ralph.common import RunState  # noqa: F811 – deferred import
    from dataclasses import asdict
    return asdict(state)


def dump_run_state(state: Any, path: Path) -> None:
    """Atomically write RunState to a YAML file."""
    d = run_state_to_dict(state)
    content = dump_yaml(d)
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(str(tmp), str(path))


def load_run_state(path: Path) -> Dict[str, Any]:
    """Load run state dict from YAML file."""
    text = path.read_text(encoding="utf-8")
    return load_yaml(text)


# ---------------------------------------------------------------------------
# JSONL helpers (for intermediate artifacts)
# ---------------------------------------------------------------------------

def append_jsonl(path: Path, obj: Any) -> None:
    """Append a single JSON object as a line to a JSONL file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read all lines from a JSONL file."""
    if not path.exists():
        return []
    items = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def write_jsonl(path: Path, items: List[Any]) -> None:
    """Overwrite a JSONL file with the given items."""
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")
