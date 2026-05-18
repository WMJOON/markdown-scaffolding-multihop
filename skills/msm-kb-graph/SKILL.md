---
name: msm-kb-graph
description: >
  Markdown 기반 지식 베이스의 그래프 구조 설계·조회·추론·저장 통합 스킬.
  (A) 그래프 구조 초기화 — graph-config.yaml 자동 생성 또는 프리셋으로 GraphRAG 구조 세팅.
  (B) 멀티홉 추론 — BFS 서브그래프 추출로 단일 문서 검색을 넘는 연결 인사이트 발견.
  (C) 시맨틱 노드 검색 — zvec 벡터 인덱스로 자연어 질의에서 관련 시작 노드를 정확하게 탐색.
  (D) 추론 결과 저장 — 멀티홉 인사이트를 wikilink 연결 md 노드로 저장.
  외부 DB·API 키 없이 로컬/GitHub 모두 동작.
  트리거: "멀티홉 추론해줘", "그래프 기반 분석", "GraphRAG 구조 만들어줘",
  "graph-config 생성해줘", "벡터 검색으로 노드 찾아줘", "zvec 인덱스 빌드",
  "추론 결과 노드로 저장해줘", "knowledge graph 인사이트 뽑아줘",
  "클러스터링", "커뮤니티 탐지", "Leiden", "cluster_id", "브릿지 노드", "synthesis 후보"
---

# md-kb-graph

## 권장 검색 흐름: Vector-First

온톨로지 탐색 시 항상 **Vector Search → Graph RAG** 순서로 수행한다.

```
자연어 질의
    ↓  [C] Vector Search  (zvec 인덱스 — 관련 시드 노드 빠르게 식별)
시드 노드 1~3개
    ↓  [B] Graph RAG      (BFS 멀티홉 — 연결 인사이트 탐색)
컨텍스트 서브그래프
    ↓  Claude 추론
최종 답변
```

**이유**: 전체 그래프에서 텍스트 매칭으로 시작하면 관련 없는 노드에서 멀티홉이 시작될 수 있다.
벡터 검색으로 의미적으로 가장 가까운 시드를 먼저 찾으면 멀티홉의 정밀도가 올라간다.

```bash
# 원라이너 패턴
NODE=$(python3 scripts/zvec_graph_index.py search "질의" --top1)
python3 graph_rag.py --entity "$NODE" --hops 2 --context-only
```

