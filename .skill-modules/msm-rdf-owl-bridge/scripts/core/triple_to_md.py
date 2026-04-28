"""
triple_to_md: TripleGraph → MD frontmatter 파일 변환 (Mode A Import 출력용)
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml
from rdflib import Literal, URIRef
from rdflib.namespace import RDFS

from .triple_graph import (
    TripleGraph,
    ONTO, ENTITY, REL, REL_STR,
    ENTITY_TYPE_REVERSE,
    LAYER_MAP,
    DIR_MAP,
)

def infer_entity_type(class_uri: str) -> str:
    """OWL Class URI → entity_type 추론.
    config.entity_types 역매핑 우선, 없으면 URI 로컬명을 그대로 사용.
    """
    if class_uri in ENTITY_TYPE_REVERSE:
        return ENTITY_TYPE_REVERSE[class_uri]
    # URI 로컬명 추출: http://x/y#LocalName → LocalName
    local = class_uri.split("/")[-1].split("#")[-1]
    return local if local else "Entity"


def slugify(label: str) -> str:
    """레이블 → entity_id 슬러그 (최대 80자)."""
    label = label.lower().strip()
    label = re.sub(r"[^a-z0-9\s_]", "", label)
    label = re.sub(r"[\s]+", "_", label)
    return label[:80].strip("_")


def entity_type_to_dir(entity_type: str) -> str:
    return DIR_MAP.get(entity_type, entity_type)


def triple_graph_to_md(
    graph: TripleGraph,
    output_dir: Path,
    dry_run: bool = False,
) -> list[dict]:
    """
    TripleGraph의 모든 엔티티를 MD frontmatter 파일로 출력.

    반환: [{entity_id, entity_type, path, status}, ...]
    """
    g       = graph.g
    results = []
    today   = date.today().isoformat()

    for uri, entity_id, entity_type in graph.iter_entities():
        # label 수집 — 단일 패스로 en/ko 분리
        label_en = ""
        label_ko = ""
        for lit in g.objects(uri, RDFS.label):
            if not isinstance(lit, Literal):
                continue
            if lit.language == "ko":
                label_ko = label_ko or str(lit)
            elif lit.language in ("en", None):
                label_en = label_en or str(lit)
        if not label_en:
            label_en = entity_id.replace("_", " ").title()

        # 관계 수집
        relations: list[dict] = []
        for _, p, o in g.triples((uri, None, None)):
            p_str = str(p)
            if not p_str.startswith(REL_STR):
                continue
            rel_type  = p_str[len(REL_STR):]
            obj_eid   = g.value(o, ONTO.entityId)
            obj_etype = g.value(o, ONTO.entityType)
            if obj_eid:
                obj_id = str(obj_eid)
                if obj_etype:
                    wikilink = f"[[{obj_etype}/{obj_id}]]"
                else:
                    wikilink = f"[[{obj_id}]]"
                relations.append({"type": rel_type, "target": wikilink})

        # frontmatter 구성
        fm: dict = {
            "entity_id":      entity_id,
            "entity_type":    entity_type,
            "is_abstract":    False,
            "ontology_layer": LAYER_MAP.get(entity_type, "general"),
            "label_ko":       label_ko,
            "label_en":       label_en,
            "status":         "draft",
            "version":        "v0.1.0",
            "created":        today,
            "updated":        today,
            "source_refs":    [],
            "confidence":     0.70,
            "relations":      relations,
            "tags":           [
                f"ontology/{entity_type.lower()}",
                "ontology/entity",
                "imported/rdf",
            ],
        }

        type_dir = entity_type_to_dir(entity_type)
        out_path = output_dir / type_dir / f"{entity_id}.md"
        md_body  = _build_md_content(fm, label_en, entity_type)

        results.append({
            "entity_id":   entity_id,
            "entity_type": entity_type,
            "path":        str(out_path),
            "status":      "written" if not dry_run else "dry_run",
        })

        if not dry_run:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md_body, encoding="utf-8")

    return results


def _build_md_content(fm: dict, label_en: str, entity_type: str) -> str:
    yaml_str = yaml.dump(
        fm,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return (
        f"---\n{yaml_str}---\n"
        f"# Summary\n{label_en} (RDF import)\n\n"
        f"# Definition\n"
        f"- entity_type: {entity_type}\n"
        f"- status: draft\n"
    )
