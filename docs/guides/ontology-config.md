# 온톨로지 설정

## graph-ontology.yaml (권장)

OWL-lite 스타일 단일 진실 소스.
엔티티 클래스, 관계, 스칼라 속성, 집계 규칙을 한 파일에 선언한다.

```yaml
classes:
  Industry:
    entity_dir: ontology/industry
  Competitor:
    entity_dir: ontology/competitor

object_properties:
  targetsIndustry:
    domain: Competitor
    range: Industry
    relation_name: targets_industry

datatype_properties:
  name:
    domain: [Industry, Competitor]
    range: xsd:string
```

`graph-config.yaml` + `rollup-config.yaml`은 이 파일에서 자동 도출된다.
전체 예시 → [`graph-ontology.example.yaml`](../../graph-ontology.example.yaml)

## Categorical Morphism Extension (선택)

`graph-ontology.yaml`에 `morphism_types` + `composition_table` 섹션을 추가하면
**범주론적 합성 추론**이 자동으로 활성화된다.

```yaml
# 사상 유형 정의
morphism_types:
  requires:
    transitive: true
    description: "F_j 분석에 F_i 출력이 선행 입력으로 필요"
  informs:
    transitive: true
    description: "F_i 결과가 F_j 해석에 맥락 제공"
  causes:
    transitive: true
    description: "F_i 상태 변화가 F_j를 유발"
  constrains:
    transitive: true
    description: "F_i가 F_j의 선택지/실행 조건을 제한"
  contrasts_with:
    transitive: false
    description: "대립적 관점 (양방향, 비추이적)"

# 합성 테이블: g ∘ f 결과 유형
composition_table:
  causes:     [causes,     causes,     causes,     informs]
  requires:   [requires,   requires,   constrains, requires]
  constrains: [constrains, constrains, constrains, constrains]
  informs:    [informs,    informs,    informs,    informs]
```

**동작 방식:**
1. `graph_builder`가 그래프 구축 후 transitive morphism 엣지를 필터링
2. `composition_table`에 따라 2-hop/3-hop 합성 엣지를 자동 생성
3. 합성 엣지에 `inferred=true`, `via`, `composition` 메타데이터 부착
4. `graph_rag`가 직접 관계와 합성 추론을 분리하여 LLM에 전달

`morphism_types`/`composition_table`이 없으면 기존과 동일하게 동작한다 (opt-in).

## 설정 파일 요약

| 파일 | 역할 |
|------|------|
| `graph-ontology.yaml` | OWL-lite 단일 진실 소스 (권장) |
| `graph-config.yaml` | entity_dirs / relation_map / scalar_node_attrs (레거시 호환) |
| `rollup-config.yaml` | 집계 규칙 (레거시 호환) |
