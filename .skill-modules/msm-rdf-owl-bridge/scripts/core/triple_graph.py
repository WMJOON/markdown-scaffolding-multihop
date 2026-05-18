"""
TripleGraph: rdflib Graph 래퍼

네임스페이스와 엔티티 타입 매핑은 rdf-bridge-config.yaml에서 런타임 로드.
config가 없으면 generic 기본값(http://rdf-bridge.local/)으로 동작.
"""
from __future__ import annotations

from typing import Iterator, Tuple

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

from .rdf_bridge_config import get_config

# ─── 런타임 Namespace 초기화 ─────────────────────────────────────────────────
# config 로드 후 네임스페이스 결정
_cfg  = get_config()
_base = _cfg.namespace_base.rstrip("/") + "/"

ONTO   = Namespace(_base + "ontology/")
ENTITY = Namespace(_base + "entity/")
REL    = Namespace(_base + "relation/")

# 루프 내 str() 반복 변환 방지용 캐시
REL_STR  = str(REL)
ONTO_STR = str(ONTO)


# ─── 런타임 매핑 테이블 ───────────────────────────────────────────────────────
# config.entity_types → ENTITY_TYPE_MAP
# 미등록 entity_type 은 ONTO[entity_type] 으로 자동 생성

def _build_entity_type_map() -> dict[str, URIRef]:
    return {et.name: ONTO[et.name] for et in _cfg.entity_types}


ENTITY_TYPE_MAP: dict[str, URIRef] = _build_entity_type_map()
ENTITY_TYPE_REVERSE: dict[str, str] = {str(v): k for k, v in ENTITY_TYPE_MAP.items()}
LAYER_MAP: dict[str, str] = _cfg.layer_map   # entity_type → layer
DIR_MAP:   dict[str, str] = _cfg.dir_map     # entity_type → directory name


class TripleGraph:
    """rdflib Graph 래퍼. config 기반 네임스페이스 + 엔티티 관리."""

    def __init__(self):
        self.g = Graph()
        self.g.bind("onto",   ONTO)
        self.g.bind("entity", ENTITY)
        self.g.bind("rel",    REL)
        self.g.bind("rdf",    RDF)
        self.g.bind("rdfs",   RDFS)
        self.g.bind("owl",    OWL)

    # ── 엔티티 추가 ───────────────────────────────────────────────────────────

    def add_entity(
        self,
        entity_id:   str,
        entity_type: str,
        label_en:    str = "",
        label_ko:    str = "",
    ) -> URIRef:
        uri       = ENTITY[entity_id]
        # 미등록 타입은 ONTO[entity_type] 으로 자동 생성
        rdf_class = ENTITY_TYPE_MAP.get(entity_type, ONTO[entity_type])
        self.g.add((uri, RDF.type,        rdf_class))
        self.g.add((uri, ONTO.entityId,   Literal(entity_id)))
        self.g.add((uri, ONTO.entityType, Literal(entity_type)))
        if label_en:
            self.g.add((uri, RDFS.label, Literal(label_en, lang="en")))
        if label_ko:
            self.g.add((uri, RDFS.label, Literal(label_ko, lang="ko")))
        return uri

    # ── 관계 추가 ─────────────────────────────────────────────────────────────

    def add_relation(
        self,
        subject_id:    str,
        relation_type: str,
        object_id:     str,
        confidence:    float = 1.0,
    ):
        s = ENTITY[subject_id]
        p = REL[relation_type]
        o = ENTITY[object_id]
        self.g.add((s, p, o))
        if confidence < 1.0:
            stmt = URIRef(f"{ONTO_STR}stmt/{subject_id}__{relation_type}__{object_id}")
            self.g.add((stmt, RDF.type,        RDF.Statement))
            self.g.add((stmt, RDF.subject,     s))
            self.g.add((stmt, RDF.predicate,   p))
            self.g.add((stmt, RDF.object,      o))
            self.g.add((stmt, ONTO.confidence,
                         Literal(confidence, datatype=XSD.float)))

    # ── 순회 ─────────────────────────────────────────────────────────────────

    def iter_entities(self) -> Iterator[Tuple[URIRef, str, str]]:
        """(uri, entity_id, entity_type) 순회"""
        for uri, _, eid in self.g.triples((None, ONTO.entityId, None)):
            etype = str(next(self.g.objects(uri, ONTO.entityType), ""))
            yield uri, str(eid), etype

    def iter_relations(self) -> Iterator[Tuple[str, str, str]]:
        """(subject_entity_id, predicate_local, object_entity_id) 순회"""
        for s, p, o in self.g:
            p_str = str(p)
            if p_str.startswith(REL_STR):
                s_id    = str(self.g.value(s, ONTO.entityId) or s)
                o_id    = str(self.g.value(o, ONTO.entityId) or o)
                p_local = p_str[len(REL_STR):]
                yield s_id, p_local, o_id

    def get_label_en(self, entity_id: str) -> str:
        uri = ENTITY[entity_id]
        for lit in self.g.objects(uri, RDFS.label):
            if isinstance(lit, Literal) and lit.language in ("en", None):
                return str(lit)
        return entity_id

    def entity_exists(self, entity_id: str) -> bool:
        return (ENTITY[entity_id], ONTO.entityId, None) in self.g

    def serialize(self, fmt: str = "turtle") -> str:
        return self.g.serialize(format=fmt)

    def parse_rdf_file(self, path: str, fmt: str | None = None):
        self.g.parse(path, format=fmt)

    def __len__(self) -> int:
        return len(self.g)
