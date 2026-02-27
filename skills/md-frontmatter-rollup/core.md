# md-frontmatter-rollup — Core

## 역할

그래프 엣지를 따라 인접 노드의 frontmatter scalar 값을 집계해
상위/부모 노드 frontmatter에 자동으로 기록한다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **rollup rule** | 어떤 relation을 따라 어떤 필드를 어떤 함수로 집계할지 선언 |
| **source_entity** | 집계 결과를 받는 노드 타입 |
| **direction** | `in` = 자식→부모 집계, `out` = 부모→자식 집계 (기본: out) |
| **write_to** | 집계 결과를 기록할 frontmatter 필드명 |

## 설정 방식

| 방식 | 파일 | 특징 |
|------|------|------|
| **OWL 온톨로지** | `graph-ontology.yaml` | 단일 진실 소스, 그래프+집계 통합 관리 |
| **레거시** | `rollup-config.yaml` | 기존 방식, 하위 호환 |

## 실행 흐름

```
graph-ontology.yaml (또는 graph-config.yaml + rollup-config.yaml)
    → graph_builder.get_graph()로 그래프 로드
    → 각 rollup_rule 순서대로 실행
        → source_entity 타입 노드 순회
        → edge_relation으로 연결된 인접 노드 수집
        → 지정 집계 함수로 값 계산
        → 원본 md 파일 frontmatter 업데이트
    → 변경 파일 목록 출력
```

## 모듈 구성

- `module.rollup-policy.md` — 집계 규칙 선언 방법 및 검증
- `module.aggregation.md` — 집계 함수 정의 및 엣지 케이스 처리
