# rollup-config.yaml 레퍼런스

## 전체 스키마

```yaml
rollup_rules:
  - id: string              # 고유 식별자
    description: string     # 선택
    source_entity: string   # entity_dirs 키 (집계 결과를 받는 노드 타입)
    edge_relation: string   # 따라갈 relation (graph_builder 엣지의 relation 값)
    direction: in | out     # in: 자식→source, out: source→자식 (기본: in)
    aggregations:
      - field: string
        func: sum | avg | weighted_avg | max | min | count
        weight_field: string   # weighted_avg 전용
        write_to: string
        updated_at_field: string  # 선택: 업데이트 날짜 기록
```

---

## 예시 1: L2 세그먼트 → L1 산업 시장규모 합산

```yaml
rollup_rules:
  - id: industry_market_size_rollup
    description: "L2 세그먼트 시장규모 합산 → L1 산업 노드"
    source_entity: industry
    edge_relation: has_segment
    direction: in
    aggregations:
      - field: market_size
        func: sum
        write_to: market_size
        updated_at_field: market_size_updated_at
      - field: callbot_adoption_rate
        func: weighted_avg
        weight_field: market_size
        write_to: callbot_adoption_rate
```

## 예시 2: 고객사 → 산업 대표 고객 수 집계

```yaml
  - id: industry_account_count
    description: "산업별 대표 고객사 수 집계"
    source_entity: industry
    edge_relation: has_account
    direction: in
    aggregations:
      - field: name
        func: count
        write_to: account_count
```

## 예시 3: 인사이트 노드 점수 집계

```yaml
  - id: topic_insight_score
    description: "토픽 노드에 연결된 인사이트 점수 평균"
    source_entity: topic
    edge_relation: related_to
    direction: in
    aggregations:
      - field: score
        func: avg
        write_to: avg_insight_score
```

---

## relation 이름 확인 방법

```bash
python3 graph_builder.py --config graph-config.yaml
# [ 엣지 relation ] 섹션에서 사용 가능한 relation 목록 확인
```
