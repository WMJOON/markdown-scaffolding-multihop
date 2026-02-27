# module.multihop-query

## 목적

그래프에서 관련 노드를 탐색하고 N-hop 서브그래프를 추출해 LLM 컨텍스트를 만든다.

## 노드 탐색 정책

### 키워드 검색 (`find_nodes_by_keyword`)
- node_id 또는 `name` 속성에 키워드가 포함되면 매칭
- NFC 정규화 후 소문자 비교

### 질의 기반 탐색 (`find_relevant_nodes`)
- 노드 name/id가 질의 문자열에 포함 → score +2~3
- 질의 토큰이 노드 경로(path flat)에 포함 → score +1
- 상위 top_k개 반환

## BFS 서브그래프 추출

```
start_nodes → hop 1 (successors + predecessors) → hop 2 → ... → hop N
```
- 방향 무관 (양방향 탐색)
- visited 집합으로 중복 방지

## 컨텍스트 직렬화

출력 포맷:
```
## Graph Triples (관계)
  (src_name) --[relation]--> (tgt_name)

## Node Facts (속성)
  [entity_type] node_name  (field1=val1, field2=val2)
```
