"""
_data_loader.py
공통 데이터 로더: CSV / JSON / Markdown frontmatter → pandas DataFrame
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yaml


def load_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    """CSV 파일을 DataFrame으로 로드."""
    return pd.read_csv(path, **kwargs)


def load_json(path: str | Path) -> pd.DataFrame:
    """JSON 파일을 DataFrame으로 로드. records 배열 또는 {col: {idx: val}} 형식 지원."""
    import json
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame(data)


def _parse_frontmatter(text: str) -> dict:
    """YAML frontmatter(--- ... ---) 파싱. 없으면 빈 dict 반환."""
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def load_frontmatter(
    md_dir: str | Path,
    keys: List[str],
    recursive: bool = True,
    ignore_dirs: Optional[set] = None,
) -> pd.DataFrame:
    """
    Markdown 디렉토리에서 frontmatter 값을 추출해 DataFrame으로 반환.

    Args:
        md_dir: Markdown 파일이 있는 디렉토리
        keys: 추출할 frontmatter 키 목록
        recursive: 하위 디렉토리 포함 여부
        ignore_dirs: 무시할 디렉토리명 집합
    """
    ignore_dirs = ignore_dirs or {".git", ".obsidian", "node_modules", "__pycache__"}
    root = Path(md_dir)
    rows = []

    pattern = "**/*.md" if recursive else "*.md"
    for md_file in root.glob(pattern):
        if any(part in ignore_dirs for part in md_file.parts):
            continue
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        row = {"_file": str(md_file.relative_to(root))}
        for key in keys:
            row[key] = fm.get(key)
        rows.append(row)

    df = pd.DataFrame(rows)
    # 수치 변환 시도
    for key in keys:
        if key in df.columns:
            df[key] = pd.to_numeric(df[key], errors="ignore")
    return df


def auto_load(
    csv: Optional[str] = None,
    json: Optional[str] = None,
    md_dir: Optional[str] = None,
    frontmatter_keys: Optional[str] = None,
) -> pd.DataFrame:
    """
    소스에 따라 적절한 로더 호출.

    Args:
        csv: CSV 파일 경로
        json: JSON 파일 경로
        md_dir: Markdown 디렉토리
        frontmatter_keys: 쉼표로 구분된 frontmatter 키 문자열
    """
    if csv:
        return load_csv(csv)
    if json:
        return load_json(json)
    if md_dir:
        keys = [k.strip() for k in (frontmatter_keys or "").split(",") if k.strip()]
        if not keys:
            raise ValueError("--frontmatter-keys 옵션이 필요합니다 (예: score,rating,count)")
        return load_frontmatter(md_dir, keys)
    raise ValueError("데이터 소스를 지정하세요: --csv / --json / --md-dir")
