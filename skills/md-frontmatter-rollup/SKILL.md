---
name: md-frontmatter-rollup
description: >
  그래프 엣지를 따라 인접 노드의 frontmatter 값을 집계(sum/avg/weighted_avg/max/min/count)해
  상위 노드 frontmatter에 자동으로 기록하는 롤업 엔진.
  graph-ontology.yaml(OWL 방식)에 집계 규칙을 선언하면 자동 도출되며,
  rollup-config.yaml(레거시 방식)도 하위 호환으로 지원한다.
  md-graph-multihop, md-scaffolding-design과 함께 사용되며,
  "market_size를 L2에서 L1으로 합산해줘", "adoption_rate를 콜량 가중평균으로 롤업해줘",
  "자식 노드 점수를 부모에 집계해줘", "frontmatter 집계 실행해줘" 같은 요청에 사용한다.
---

# md-frontmatter-rollup

그래프 엣지를 따라 인접 노드 frontmatter 값을 집계해 상위 노드에 기록하는 롤업 엔진.

## 스크립트

```
scripts/
└── rollup_engine.py   # 롤업 실행 메인 스크립트 (OWL 온톨로지 + 레거시 호환)
```

## 설정 방식

### A. graph-ontology.yaml (OWL 방식 — 권장)

`graph-ontology.yaml`의 `object_properties[*].rollup`에 집계 규칙 선언.
그래프 구성 + 집계 규칙을 파일 하나로 관리.

```bash
python3 scripts/rollup_engine.py --ontology graph-ontology.yaml
python3 scripts/rollup_engine.py --ontology graph-ontology.yaml --dry-run
python3 scripts/rollup_engine.py --ontology graph-ontology.yaml --show-rules
```

→ `references/owl-ontology-reference.md` 참조

### B. rollup-config.yaml (레거시 방식)

```bash
python3 scripts/rollup_engine.py
python3 scripts/rollup_engine.py --config graph-config.yaml --rollup rollup-config.yaml
python3 scripts/rollup_engine.py --rule industry_market_size
python3 scripts/rollup_engine.py --dry-run
```

→ `references/rollup-config-reference.md` 참조

## 워크플로우 (레거시)

### 1. rollup-config.yaml 작성

```yaml
rollup_rules:
  - id: industry_market_size
    description: "L2 세그먼트 시장규모 합산 → L1 산업 노드"
    source_entity: industry
    edge_relation: has_segment
    direction: in
    aggregations:
      - field: market_size
        func: sum
        write_to: market_size
      - field: callbot_adoption_rate
        func: weighted_avg
        weight_field: market_size
        write_to: callbot_adoption_rate
```

### 2. 롤업 실행

```bash
python3 scripts/rollup_engine.py
python3 scripts/rollup_engine.py --rule industry_market_size
python3 scripts/rollup_engine.py --dry-run
```

## 지원 집계 함수

| func | 설명 |
|------|------|
| `sum` | 합계 |
| `avg` | 단순 평균 |
| `weighted_avg` | weight_field 기준 가중평균 |
| `max` | 최댓값 |
| `min` | 최솟값 |
| `count` | 자식 노드 수 |
