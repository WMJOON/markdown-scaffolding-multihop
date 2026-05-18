"""
공통 JSONL I/O 유틸리티
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("JSONL 파싱 실패 (줄 %d): %s", lineno, e)
    return records


def save_jsonl(records: list[dict], path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_jsonl_stream(items, path: Path):
    """제너레이터/이터러블을 스트리밍으로 JSONL 저장 (메모리 효율)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
