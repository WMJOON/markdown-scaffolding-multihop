# zvec Graph Ops

## 1) Baseline Flow

```bash
# 1. 그래프 노드 인덱싱 (오프라인)
python3 scripts/zvec_graph_index.py index \
  --collection /tmp/md-graph-zvec \
  --embedder hash

# 2. 시맨틱 검색
python3 scripts/zvec_graph_index.py search \
  --collection /tmp/md-graph-zvec \
  "시장 진입 전략"

# 3. graph_rag.py 연계
NODE_ID=$(python3 scripts/zvec_graph_index.py search "시장 점유율" --top1)
python3 ../md-graph-multihop/scripts/graph_rag.py \
  --entity "$NODE_ID" --hops 2 --context-only
```

## 2) Embedder 선택

| embedder | 특징 | 사용 시점 |
|----------|------|-----------|
| `hash` | 결정적, 오프라인, 외부 의존 없음 | 초기 테스트, CI |
| `local` | zvec 내장 로컬 모델, 시맨틱 품질 양호 | 로컬 개발 |
| `openai` | OpenAI API 경유, 높은 시맨틱 품질 | 프로덕션 |
| `qwen` | Qwen API 경유 | Qwen 환경 |

`hash`로 시작 → 동작 확인 후 `local`/`openai`로 전환.
embedder 변경 시 반드시 `--force`로 재인덱싱.

## 3) 하이브리드 검색 (Python)

```python
from zvec_graph_index import find_relevant_nodes_hybrid

# graph_builder에서 G 구축 후
start_nodes = find_relevant_nodes_hybrid(
    G, query="경쟁 분석",
    top_k=5,
    zvec_weight=0.7,  # zvec 70% + keyword 30%
)
```

`zvec_weight` 조정으로 벡터/키워드 비중 제어:
- `1.0`: 순수 벡터 검색
- `0.0`: 순수 키워드 (기존 동작)
- `0.5~0.7`: 하이브리드 (권장)

## 4) 노드 텍스트 구성

인덱싱 시 각 노드는 다음 정보를 결합한 텍스트로 임베딩된다:

```
{name} [{entity_type}] {key1}: {value1} {key2}: {value2} ... {body_snippet}
```

- `name`: frontmatter name 또는 파일명
- `entity_type`: entity_dirs 키 (competitor, industry 등)
- scalar attributes: graph-config.yaml의 scalar_node_attrs
- body: `--include-body` 옵션 시 frontmatter 이후 본문 (최대 500자)

## 5) Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `collection path에 공백` | iCloud 경로 등 | `/tmp/md-graph-zvec` 사용 |
| `dimension mismatch` | embedder 변경 | `--force`로 재인덱싱 |
| `collection이 없음` | index 미실행 | `index` 명령 먼저 실행 |
| 검색 결과 부정확 | hash embedder 한계 | `local`/`openai`로 전환 |
| `graph_builder import 실패` | 경로 문제 | md-graph-multihop이 같은 skills/ 하위인지 확인 |

## 6) Collection 경로 규칙

zvec는 경로에 공백이 있으면 실패한다. Obsidian vault가 iCloud에 있는 경우:
- collection은 `/tmp/md-graph-zvec` 같은 공백 없는 경로에 저장
- 소스 그래프(md 파일)는 iCloud 경로 OK (graph_builder가 읽기만 함)
- collection은 인덱스일 뿐, 언제든 `index --force`로 재빌드 가능
