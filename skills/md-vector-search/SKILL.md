---
name: md-vector-search
description: >
  zvec 벡터 DB를 내장하여 그래프 노드에 대한 시맨틱 검색을 제공한다.
  md-graph-multihop의 naive keyword matching을 벡터 유사도 검색으로 대체/보강하여
  자연어 질의에서 관련 시작 노드를 더 정확하게 발견한다.
  graph_builder.py가 구축한 NetworkX 그래프의 노드 텍스트(name, frontmatter, body)를
  zvec collection에 인덱싱하고, 질의 시 top-K 유사 노드 ID를 반환한다.
  graph_rag.py의 find_relevant_nodes() 드롭인 대체 함수를 제공한다.
  트리거 예시: "벡터 검색으로 노드 찾아줘", "zvec 인덱스 빌드", "시맨틱 노드 검색",
  "그래프 인덱싱", "노드 임베딩 구축".
---

# md-vector-search

zvec 기반 시맨틱 벡터 검색으로 그래프 노드 발견 정확도를 강화하는 스킬.
`md-graph-multihop`의 companion으로, keyword matching → vector similarity 업그레이드를 담당한다.

## 전제 조건

```bash
pip3 install zvec pyyaml networkx
```

## 스크립트

```
scripts/
└── zvec_graph_index.py   # 그래프 노드 인덱싱 + 시맨틱 검색 CLI
```

## 워크플로우

### 1단계 — 인덱스 빌드

그래프 노드를 zvec collection에 임베딩한다.

```bash
# 기본 (hash embedder, 오프라인)
python3 scripts/zvec_graph_index.py index

# 시맨틱 embedder 사용
python3 scripts/zvec_graph_index.py index --embedder local

# 커스텀 config 지정
python3 scripts/zvec_graph_index.py index \
  --config path/to/graph-config.yaml \
  --collection /tmp/md-graph-zvec
```

### 2단계 — 시맨틱 노드 검색

```bash
# 자연어 질의로 관련 노드 탐색
python3 scripts/zvec_graph_index.py search "경쟁사의 시장 진입 전략"

# top-K 조정
python3 scripts/zvec_graph_index.py search "AI 도입 현황" --limit 10

# entity type 필터
python3 scripts/zvec_graph_index.py search "채널톡" --entity-type competitor
```

### 3단계 — graph_rag.py 통합

`graph_rag.py`에서 zvec 검색을 시작 노드 탐색에 사용한다.

```bash
# zvec 검색 결과를 --entity로 전달
NODE_ID=$(python3 scripts/zvec_graph_index.py search "시장 점유율" --top1)
python3 ../md-graph-multihop/scripts/graph_rag.py \
  --entity "$NODE_ID" --hops 2 --context-only
```

또는 Python import로 직접 통합:

```python
from zvec_graph_index import find_relevant_nodes_zvec

# find_relevant_nodes() 대체
start_nodes = find_relevant_nodes_zvec(query="경쟁 분석", top_k=5)
```

## 주요 CLI 옵션

### index

| 옵션 | 설명 |
|------|------|
| `--config PATH` | graph-config.yaml 경로 (생략 시 자동 탐색) |
| `--collection PATH` | zvec collection 경로 (기본: /tmp/md-graph-zvec) |
| `--embedder {hash,local,openai,qwen}` | 임베딩 백엔드 (기본: hash) |
| `--dimension N` | 벡터 차원 (기본: 384) |
| `--include-body` | 노드 본문 텍스트도 인덱싱에 포함 |
| `--body-max-chars N` | 본문 포함 시 최대 문자 수 (기본: 500) |
| `--force` | 기존 collection 삭제 후 재빌드 |

### search

| 옵션 | 설명 |
|------|------|
| `--collection PATH` | zvec collection 경로 |
| `--embedder {hash,local,openai,qwen}` | 검색 시 사용할 embedder (인덱싱 때와 동일해야 함) |
| `--limit N` | Top-K 결과 수 (기본: 5) |
| `--entity-type TYPE` | entity type 필터 |
| `--top1` | 최상위 1개 노드 ID만 출력 (파이프라인 연계용) |
| `--json` | JSON 형식 출력 |

### stats

| 옵션 | 설명 |
|------|------|
| `--collection PATH` | zvec collection 경로 |

## 실행 규칙

1. collection 경로는 공백 없는 디렉토리 사용 (zvec 제약).
2. `--embedder hash`로 시작해 오프라인 동작을 확인한 후, `local`/`openai`로 품질 향상.
3. 인덱싱과 검색에 같은 embedder를 사용해야 한다. embedder 변경 시 `--force`로 재인덱싱.
4. 그래프 구조가 변경되면 (노드 추가/삭제) `index --force`로 재빌드.

## 아키텍처

```
graph-config.yaml
       │
       ▼
graph_builder.py ──→ NetworkX DiGraph
       │                    │
       │              노드별 텍스트 추출
       │              (name + attrs + body)
       │                    │
       │                    ▼
       │            zvec_graph_index.py
       │              embed → upsert
       │                    │
       │                    ▼
       │             zvec collection
       │            (벡터 인덱스 저장)
       │                    │
       ▼                    ▼
find_relevant_nodes()  find_relevant_nodes_zvec()
  (keyword matching)     (vector similarity)
       │                    │
       └────────┬───────────┘
                ▼
         start_nodes → BFS N-hop → 서브그래프
```

## References

- 운영 노트: `references/zvec-graph-ops.md`
- zvec 공식 문서: https://zvec.org/en/docs/
