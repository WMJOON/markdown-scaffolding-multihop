# module.rollup-policy

## OWL 기반 설계 원칙

rollup 규칙은 도메인 특정 설정이 아니라 **온톨로지 선언에서 자동으로 도출**된다.
`graph-ontology.yaml`에 클래스·프로퍼티를 선언하면 rollup 엔진이 규칙을 유추한다.

## graph-ontology.yaml 구조

```yaml
# 클래스: entity 타입 정의 (OWL Class에 대응)
classes:
  ClassName:
    entity_dir: 상대경로/디렉토리
    label: 레이블 (선택)
    subClassOf: ParentClassName   # 선택: 계층 관계

# 객체 프로퍼티: 노드 간 관계 (OWL ObjectProperty에 대응)
object_properties:
  propertyName:
    domain: ClassName             # 관계 출발 클래스
    range: ClassName              # 관계 도착 클래스
    relation_name: graph_edge_id  # 그래프 엣지 relation 값
    cardinality: one | many       # 선택
    rollup:                       # 선언 시 range→domain 집계 실행
      - field: frontmatter_field
        func: sum | avg | weighted_avg | max | min | count
        weight_field: field       # weighted_avg 전용
        write_to: target_field
        updated_at_field: field   # 선택

# 데이터 프로퍼티: 스칼라 값 (OWL DatatypeProperty에 대응)
datatype_properties:
  propName:
    domain: [ClassName, ...]
    range: xsd:integer | xsd:decimal | xsd:string | xsd:boolean
    label: 설명 (선택)
```

## 도출 규칙

| 온톨로지 선언 | 도출되는 동작 |
|-------------|-------------|
| `classes[N].entity_dir` | graph-config의 `entity_dirs[N]` |
| `object_properties[P].relation_name` | graph-config의 `relation_map`에서 wikilink 필드 추론 |
| `datatype_properties[P].domain` | `scalar_node_attrs`에 자동 포함 |
| `object_properties[P].rollup` | rollup 규칙 자동 생성 |

## 하위 호환성

`graph-config.yaml`과 `rollup-config.yaml`은 계속 동작한다.
`graph-ontology.yaml`은 두 파일을 **대체**하는 단일 진입점이다.
