"""
Mode A: RDF/OWL 파일 → Semantic Atlas MD 엔티티 파일

파이프라인:
  RDF/OWL 파일 (rdflib 파싱)
    → OWL Class/Property 추출
    → TripleGraph (내부 포맷) 변환
    → MD frontmatter 파일 출력
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS

from core.triple_graph import TripleGraph, ONTO, ENTITY, REL
from core.triple_to_md import (
    triple_graph_to_md,
    infer_entity_type,
    slugify,
)

logger = logging.getLogger(__name__)

# 파일 확장자 → rdflib format 매핑
_SUFFIX_FMT: dict[str, str] = {
    ".ttl":    "turtle",
    ".owl":    "xml",
    ".rdf":    "xml",
    ".n3":     "n3",
    ".nt":     "nt",
    ".jsonld": "json-ld",
    ".trig":   "trig",
}

# 외부 OWL Property → 내부 relation_type 매핑
_OWL_PROP_TO_REL: dict[str, str] = {
    str(RDFS.subClassOf):                                          "subclass_of",
    str(OWL.equivalentClass):                                      "equivalent_to",
    str(OWL.disjointWith):                                         "disjoint_with",
    "http://www.w3.org/2004/02/skos/core#broader":                 "subclass_of",
    "http://www.w3.org/2004/02/skos/core#narrower":                "has_subclass",
    "http://www.w3.org/2004/02/skos/core#related":                 "related_to",
    "http://www.w3.org/2004/02/skos/core#exactMatch":              "equivalent_to",
    "http://www.w3.org/2004/02/skos/core#closeMatch":              "related_to",
    "http://www.w3.org/2002/07/owl#sameAs":                        "equivalent_to",
}


# ─── 진입점 ───────────────────────────────────────────────────────────────────

def run_import(
    input_path:  Path,
    output:      str | None,
    entity_dir:  str | None,
):
    logger.info("[Mode A] RDF/OWL 임포트 시작: %s", input_path)
    print(f"[Mode A] 입력: {input_path}")

    out_dir = _resolve_output_dir(input_path, output, entity_dir)
    print(f"[Mode A] 출력 디렉토리: {out_dir}")

    # ── rdflib 파싱 ──────────────────────────────────────────────────────────
    raw = _parse_rdf(input_path)
    print(f"[Mode A] 파싱된 Triple 수: {len(raw)}")

    # ── 내부 TripleGraph 변환 ─────────────────────────────────────────────────
    bridge = TripleGraph()
    n_classes, n_props = _convert_owl_to_bridge(raw, bridge)
    entities = list(bridge.iter_entities())
    print(f"[Mode A] 변환: Class {n_classes}개, Property {n_props}개 → 엔티티 {len(entities)}개")

    if not entities:
        print("[WARN] 변환된 엔티티가 없습니다. 입력 파일을 확인하세요.")
        return

    # ── MD 파일 출력 ──────────────────────────────────────────────────────────
    results = triple_graph_to_md(bridge, out_dir)
    written = [r for r in results if r["status"] == "written"]
    print(f"[Mode A] 완료: {len(written)}개 MD 파일 → {out_dir}")

    for r in written[:15]:
        print(f"  · [{r['entity_type']:20s}] {r['entity_id']}")
    if len(written) > 15:
        print(f"  ... 외 {len(written) - 15}개")

    # 통계
    from collections import Counter
    by_type = Counter(r["entity_type"] for r in written)
    print("\n[Mode A] 타입별 집계:")
    for etype, cnt in by_type.most_common():
        print(f"  {etype:25s}: {cnt}")


# ─── RDF 파싱 ─────────────────────────────────────────────────────────────────

def _parse_rdf(path: Path) -> Graph:
    g   = Graph()
    fmt = _SUFFIX_FMT.get(path.suffix.lower())
    try:
        g.parse(str(path), format=fmt)
        return g
    except Exception as e:
        logger.warning("지정 format(%s) 파싱 실패: %s — 자동 감지 재시도", fmt, e)

    try:
        g2 = Graph()
        g2.parse(str(path))
        return g2
    except Exception as e2:
        logger.error("RDF 파싱 최종 실패: %s", e2)
        print(f"[ERROR] RDF 파싱 실패: {e2}", file=sys.stderr)
        sys.exit(1)


# ─── OWL → TripleGraph 변환 ───────────────────────────────────────────────────

def _convert_owl_to_bridge(raw: Graph, bridge: TripleGraph) -> tuple[int, int]:
    """
    외부 rdflib Graph → 내부 TripleGraph 변환.
    반환: (처리된 class 수, 처리된 property 수)
    """
    processed: set[URIRef] = set()
    n_classes = 0
    n_props   = 0

    # OWL Class + RDFS Class
    for cls in sorted(
        set(raw.subjects(RDF.type, OWL.Class))
        | set(raw.subjects(RDF.type, RDFS.Class))
    ):
        if cls in processed or not isinstance(cls, URIRef):
            continue
        processed.add(cls)
        if _process_class(raw, bridge, cls):
            n_classes += 1

    # OWL ObjectProperty → domain/range 관계 추가
    for prop in sorted(raw.subjects(RDF.type, OWL.ObjectProperty)):
        if isinstance(prop, URIRef):
            if _process_property(raw, bridge, prop):
                n_props += 1

    return n_classes, n_props


def _process_class(raw: Graph, bridge: TripleGraph, cls: URIRef) -> bool:
    cls_str     = str(cls)
    entity_type = infer_entity_type(cls_str)
    label_en    = _get_label(raw, cls, "en") or _uri_local_name(cls_str)
    label_ko    = _get_label(raw, cls, "ko")
    entity_id   = slugify(label_en)

    if not entity_id or len(entity_id) < 2:
        return False

    bridge.add_entity(entity_id, entity_type, label_en, label_ko)

    # subClassOf / OWL 관계
    for rel_uri, rel_type in _OWL_PROP_TO_REL.items():
        for _, _, target in raw.triples((cls, URIRef(rel_uri), None)):
            if not isinstance(target, URIRef):
                continue
            t_label = _get_label(raw, target, "en") or _uri_local_name(str(target))
            t_id    = slugify(t_label)
            if t_id and t_id != entity_id and len(t_id) >= 2:
                bridge.add_relation(entity_id, rel_type, t_id, confidence=0.85)

    return True


def _process_property(raw: Graph, bridge: TripleGraph, prop: URIRef) -> bool:
    domains = list(raw.objects(prop, RDFS.domain))
    ranges  = list(raw.objects(prop, RDFS.range))
    if not (domains and ranges):
        return False

    prop_label = _get_label(raw, prop, "en") or _uri_local_name(str(prop))
    rel_type   = slugify(prop_label) or "related_to"

    added = False
    for domain in domains:
        for rng in ranges:
            if not (isinstance(domain, URIRef) and isinstance(rng, URIRef)):
                continue
            d_label = _get_label(raw, domain, "en") or _uri_local_name(str(domain))
            r_label = _get_label(raw, rng,    "en") or _uri_local_name(str(rng))
            d_id    = slugify(d_label)
            r_id    = slugify(r_label)
            if d_id and r_id and len(d_id) >= 2 and len(r_id) >= 2:
                bridge.add_relation(d_id, rel_type, r_id, confidence=0.80)
                added = True
    return added


_LABEL_PREDS = [
    RDFS.label,
    URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"),
    URIRef("http://www.w3.org/2004/02/skos/core#altLabel"),
    URIRef("http://purl.org/dc/terms/title"),
]


def _get_label(g: Graph, uri: URIRef, lang: str = "en") -> str:
    """우선순위 predicate 목록에서 지정 언어 label 반환. 없으면 빈 문자열."""
    for pred in _LABEL_PREDS:
        for lit in g.objects(uri, pred):
            if isinstance(lit, Literal):
                if lit.language == lang:
                    return str(lit)
                if lit.language is None and lang == "en":
                    return str(lit)
    return ""


def _uri_local_name(uri_str: str) -> str:
    """URI에서 로컬명 추출: http://x/y#z → z, http://x/y/z → z"""
    return uri_str.split("/")[-1].split("#")[-1]


# ─── 출력 디렉토리 결정 ───────────────────────────────────────────────────────

def _resolve_output_dir(
    input_path: Path,
    output:     str | None,
    entity_dir: str | None,
) -> Path:
    if output:
        return Path(output)
    if entity_dir:
        return Path(entity_dir)

    # 자동 탐색: semantic-atlas 표준 경로
    candidates = [
        Path.cwd() / "01_ontology-data" / "data" / "ontology-entities",
        Path.cwd() / "data" / "ontology-entities",
        Path.cwd().parent / "01_ontology-data" / "data" / "ontology-entities",
        input_path.parent.parent / "01_ontology-data" / "data" / "ontology-entities",
    ]
    for c in candidates:
        if c.is_dir():
            logger.info("엔티티 디렉토리 자동 탐지: %s", c)
            return c

    fallback = input_path.parent / "imported_entities"
    logger.warning("엔티티 디렉토리 탐지 실패 → 폴백: %s", fallback)
    return fallback
