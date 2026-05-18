"""SHA256-based idempotency key management for Ralph ETL."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from ralph.common import RunConfig


def compute_string_hash(content: str) -> str:
    return "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def compute_config_hash(config: RunConfig) -> str:
    from dataclasses import asdict
    raw = json.dumps(asdict(config), sort_keys=True, ensure_ascii=False)
    return compute_string_hash(raw)


def compute_idempotency_key(
    batch_id: str, step: str, input_snapshot_hash: str, config_hash: str
) -> str:
    combined = f"{batch_id}+{step}+{input_snapshot_hash}+{config_hash}"
    return compute_string_hash(combined)


def compute_input_snapshot_hash(manifest_path: Path) -> str:
    """Hash the manifest file or directory listing as input snapshot."""
    if not manifest_path.exists():
        return compute_string_hash("")
    if manifest_path.is_dir():
        # hash sorted list of file paths + sizes
        entries = sorted(
            f"{p.relative_to(manifest_path)}:{p.stat().st_size}"
            for p in manifest_path.rglob("*")
            if p.is_file()
        )
        return compute_string_hash("\n".join(entries))
    return compute_file_hash(manifest_path)


def find_cached_checkpoint(
    checkpoints: list, step: str, key: str
) -> bool:
    """Check if a checkpoint with matching step and idempotency_key exists."""
    for cp in checkpoints:
        cp_step = cp.step if hasattr(cp, "step") else cp.get("step", "")
        cp_key = (
            cp.idempotency_key
            if hasattr(cp, "idempotency_key")
            else cp.get("idempotency_key", "")
        )
        if cp_step == step and cp_key == key:
            return True
    return False
