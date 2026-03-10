# Mode A — RDF/OWL Import

외부 RDF/OWL 온톨로지 파일을 Semantic Atlas MD 엔티티 파일로 변환한다.

## 입력 형식

| 확장자 | rdflib format |
|--------|--------------|
| `.ttl` | turtle |
| `.owl` | xml |
| `.rdf` | xml |
| `.n3`  | n3 |
| `.nt`  | nt |
| `.jsonld` | json-ld |
| `.trig` | trig |

지정 format 파싱 실패 시 rdflib 자동 감지로 재시도.

## 파이프라인

```
RDF/OWL 파일
  → rdflib.Graph.parse()
  → OWL Class + RDFS Class 추출
  → OWL ObjectProperty (domain/range) 추출
  → TripleGraph 변환
  → triple_graph_to_md() → MD 파일 출력
```

## 추출 규칙

### Class 처리

- `rdf:type owl:Class` 또는 `rdf:type rdfs:Class` 인 모든 URI
- label 우선순위: `rdfs:label[en]` → `skos:prefLabel` → `skos:altLabel` → `dct:title` → URI 로컬명
- `entity_id`: label_en를 slugify (소문자 + 하이픈)
- `entity_type`: `infer_entity_type(uri)` — URI 패턴 매핑 (기본: GenericConcept)

### Property 처리

- `rdf:type owl:ObjectProperty` + domain/range 모두 있는 경우만 추출
- `rel_type`: property label을 slugify
- confidence: 0.80 (OWL property 기반)

### OWL 관계 매핑

| OWL | 내부 rel_type |
|-----|-------------|
| rdfs:subClassOf | subclass_of |
| owl:equivalentClass | equivalent_to |
| owl:disjointWith | disjoint_with |
| skos:broader | subclass_of |
| skos:narrower | has_subclass |
| skos:related | related_to |
| skos:exactMatch | equivalent_to |
| skos:closeMatch | related_to |
| owl:sameAs | equivalent_to |

## 출력 MD 파일 형식

```yaml
---
entity_id: <slug>
entity_type: <inferred_type>
ontology_layer: <layer>
label_en: "English Label"
label_ko: "한국어 레이블"  # OWL에 ko label 있을 때만
relations:
  - type: subclass_of
    target: "[[EntityType/target_entity_id]]"
    confidence: 0.85
---
```

출력 디렉토리: `<entity_dir>/<entity_type>/<entity_id>.md`

## 실행 예시

```bash
PYTHON="03_platform/tools/rdf-owl-bridge/.venv/bin/python"
BRIDGE="03_platform/tools/rdf-owl-bridge/__main__.py"

# Wikidata 온톨로지 임포트 (자동 출력 경로 탐지)
${PYTHON} ${BRIDGE} wikidata-transport.ttl

# 출력 경로 명시
${PYTHON} ${BRIDGE} schema.org.ttl \
  --output 01_ontology-data/data/ontology-entities

# 상세 로그
${PYTHON} ${BRIDGE} ontology.owl --verbose
```

## 주의사항

- entity_id 길이 < 2 이면 스킵 (너무 짧은 로컬명 방지)
- blank node (URIRef가 아닌 BNode)는 처리 제외
- 대규모 OWL(수만 Class) 임포트 시 시간 소요 — `--verbose`로 진행상황 확인 권장
