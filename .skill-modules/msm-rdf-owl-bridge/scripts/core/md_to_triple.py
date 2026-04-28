"""
md_to_triple: MD frontmatter → TripleGraph 변환
- 단일 파일 파싱
- 디렉토리 일괄 로드
- 엔티티 feature dict 추출 (embedding 입력용)
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import yaml

from .triple_graph import TripleGraph, ENTITY, ONTO, REL, REL_STR

# wikilink 파싱: [[EntityType/entity_id]] 또는 [[entity_id]]
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def _parse_wikilink_target(raw: str) -> str:
    """[[ModelFamily/model_family__xxx]] → model_family__xxx"""
    raw = raw.strip()
    return raw.split("/")[-1] if "/" in raw else raw


def parse_frontmatter(md_path: Path) -> dict | None:
    """MD 파일에서 YAML frontmatter 추출. 실패 시 None 반환."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return None

    if not text.startswith("---"):
        return None

    end = text.find("---", 3)
    if end == -1:
        return None

    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return None


def load_entity_dir(entity_root: Path, graph: TripleGraph) -> int:
    """
    entity_root 하위 모든 .md 파일을 읽어 TripleGraph에 적재.

    반환: 적재된 엔티티 수
    """
    count = 0
    for md_path in sorted(entity_root.rglob("*.md")):
        fm = parse_frontmatter(md_path)
        if not fm:
            continue

        entity_id   = fm.get("entity_id")
        entity_type = fm.get("entity_type")
        if not entity_id or not entity_type:
            continue

        graph.add_entity(
            entity_id   = entity_id,
            entity_type = entity_type,
            label_en    = str(fm.get("label_en") or ""),
            label_ko    = str(fm.get("label_ko") or ""),
        )

        for rel in fm.get("relations") or []:
            if not isinstance(rel, dict):
                continue
            rel_type   = rel.get("type", "")
            target_raw = str(rel.get("target", ""))

            match = _WIKILINK_RE.search(target_raw)
            target_id = _parse_wikilink_target(match.group(1)) if match else target_raw.strip()

            if rel_type and target_id:
                graph.add_relation(
                    subject_id    = entity_id,
                    relation_type = rel_type,
                    object_id     = target_id,
                    confidence    = float(fm.get("confidence") or 1.0),
                )
        count += 1

    return count


def iter_entity_files(entity_root: Path) -> Iterator[tuple[Path, dict]]:
    """(md_path, frontmatter) 순회 — 파일별 접근이 필요할 때 사용."""
    for md_path in sorted(entity_root.rglob("*.md")):
        fm = parse_frontmatter(md_path)
        if fm and fm.get("entity_id"):
            yield md_path, fm


def entity_feature_dict(entity_id: str, graph: TripleGraph) -> dict:
    """
    embedding 입력용 feature dict 반환.

    {
        entity_id: str,
        entity_type: str,
        label_en: str,
        relations: [(rel_type, target_id), ...],
        feature_text: str   # TF-IDF 입력용 concat 텍스트
    }
    """
    g = graph.g
    uri = ENTITY[entity_id]

    entity_type = str(g.value(uri, ONTO.entityType) or "")
    label_en    = graph.get_label_en(entity_id)

    relations: list[tuple[str, str]] = []
    for _, p, o in g.triples((uri, None, None)):
        p_str = str(p)
        if p_str.startswith(REL_STR):
            rel_type = p_str[len(REL_STR):]
            obj_id   = str(g.value(o, ONTO.entityId) or o)
            relations.append((rel_type, obj_id))

    feature_text = " ".join([
        entity_type,
        label_en,
        *[f"{rt} {oid}" for rt, oid in relations],
    ])

    return {
        "entity_id":    entity_id,
        "entity_type":  entity_type,
        "label_en":     label_en,
        "relations":    relations,
        "feature_text": feature_text,
    }
