# graph-ontology.yaml — OWL 온톨로지 레퍼런스

## 개요

`graph-ontology.yaml`은 OWL(Web Ontology Language) 스타일로 지식 그래프의
클래스(entity 타입)와 프로퍼티(관계/속성)를 선언하는 **단일 진실 소스**다.

이 파일 하나로 `graph-config.yaml`과 `rollup-config.yaml`을 자동 도출한다.

## 파일 위치

프로젝트 루트 (graph-config.yaml과 같은 위치) 또는 `--ontology` 옵션으로 지정.

## 전체 스키마

```yaml
# 네임스페이스 (선택 — 문서화/URI 목적)
namespace: "http://example.org/kg#"

# ── 클래스 (Entity 타입) ──────────────────────
classes:
  ClassName:
    label: 한국어 레이블 (선택)
    entity_dir: path/to/directory     # graph_builder가 읽을 디렉토리
    description: 설명 (선택)

# ── Object Properties (엣지 / 관계) ──────────
object_properties:
  propertyName:
    label: 레이블 (선택)
    domain: SourceClass               # 관계 주체 (source_entity)
    range: TargetClass                # 관계 대상
    relation_name: edge_relation_id   # 그래프 엣지 relation 식별자
    rollup:                           # 집계 규칙 (선택)
      - field: frontmatter_field      # 집계할 필드
        func: sum | avg | weighted_avg | max | min | count
        weight_field: weight_field    # weighted_avg 전용
        write_to: result_field        # 결과를 기록할 필드
        updated_at_field: date_field  # 업데이트 날짜 기록 (선택)

# ── Datatype Properties (스칼라 속성) ─────────
datatype_properties:
  propertyName:
    label: 레이블 (선택)
    domain: ClassName | [Class1, Class2]
    range: xsd:string | xsd:float | xsd:integer | xsd:boolean

# ── 추가 scalar_node_attrs ────────────────────
# datatype_properties에 없지만 노드 속성으로 보존할 필드
scalar_node_attrs:
  - field_name
```

---

## rollup_engine.py가 ontology에서 도출하는 것

| 온톨로지 필드 | 도출 결과 |
|--------------|----------|
| `classes[*].entity_dir` | `graph-config.yaml`의 `entity_dirs` |
| `datatype_properties[*]` 이름 | `scalar_node_attrs` |
| `object_properties[*].rollup[*].field` | `scalar_node_attrs` (자동 포함) |
| `object_properties[*].rollup` | `rollup-config.yaml`의 `rollup_rules` |

---

## 예시 1: 산업/경쟁사 분석 그래프

```yaml
namespace: "http://example.org/market-analysis#"

classes:
  Industry:
    label: 산업
    entity_dir: data/industry-entities
  Segment:
    label: 세그먼트
    entity_dir: data/segment-entities
  Competitor:
    label: 경쟁사
    entity_dir: data/competitor-entities

object_properties:
  hasSegment:
    domain: Industry
    range: Segment
    relation_name: has_segment
    rollup:
      - field: market_size
        func: sum
        write_to: market_size
      - field: adoption_rate
        func: weighted_avg
        weight_field: market_size
        write_to: adoption_rate
  targetsIndustry:
    domain: Competitor
    range: Industry
    relation_name: targets_industry

datatype_properties:
  name:
    domain: [Industry, Segment, Competitor]
    range: xsd:string
  market_size:
    domain: [Industry, Segment]
    range: xsd:float
  adoption_rate:
    domain: [Industry, Segment]
    range: xsd:float

scalar_node_attrs: [title, status, tags]
```

---

## 예시 2: 개인 지식 베이스 (personal-memory)

```yaml
classes:
  Note:
    label: 노트
    entity_dir: notes
  Project:
    label: 프로젝트
    entity_dir: projects
  Topic:
    label: 토픽
    entity_dir: topics

object_properties:
  relatedTo:
    domain: Note
    range: Note
    relation_name: related_to
  partOf:
    domain: Note
    range: Project
    relation_name: part_of
    rollup:
      - field: score
        func: avg
        write_to: avg_note_score

datatype_properties:
  title:
    domain: [Note, Project, Topic]
    range: xsd:string
  score:
    domain: Note
    range: xsd:float
  status:
    domain: [Note, Project]
    range: xsd:string

scalar_node_attrs: [date, tags, area]
```

---

## 예시 3: GitHub 문서 레포

```yaml
classes:
  Guide:
    label: 가이드
    entity_dir: docs/guides
  Reference:
    label: 레퍼런스
    entity_dir: docs/reference
  Decision:
    label: 아키텍처 결정
    entity_dir: docs/decisions

object_properties:
  dependsOn:
    domain: Guide
    range: Reference
    relation_name: depends_on
  supersedes:
    domain: Decision
    range: Decision
    relation_name: supersedes

datatype_properties:
  title:
    domain: [Guide, Reference, Decision]
    range: xsd:string
  status:
    domain: [Guide, Reference, Decision]
    range: xsd:string
  author:
    domain: [Guide, Reference, Decision]
    range: xsd:string

scalar_node_attrs: [date, tags, version]
```

---

## CLI 사용법

```bash
# 온톨로지 기반 롤업 실행
python3 rollup_engine.py --ontology graph-ontology.yaml

# dry-run (파일 수정 없이 결과 미리 보기)
python3 rollup_engine.py --ontology graph-ontology.yaml --dry-run

# 도출된 롤업 규칙 확인
python3 rollup_engine.py --ontology graph-ontology.yaml --show-rules

# 특정 property만 실행
python3 rollup_engine.py --ontology graph-ontology.yaml --property hasSegment

# graph-config.yaml이 없을 때: ontology에서 entity_dirs 자동 도출
python3 rollup_engine.py --ontology graph-ontology.yaml
```

## 참고: relation_name 확인

```bash
# 현재 그래프의 relation 목록 확인
python3 graph_builder.py --config graph-config.yaml
# [ 엣지 relation ] 섹션에서 사용 가능한 relation 확인
```
