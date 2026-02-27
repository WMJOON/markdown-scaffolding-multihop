---
name: md-graph-multihop
description: >
  Markdown 기반 지식 베이스(frontmatter + wikilink)를 인메모리 그래프로 파싱하고,
  BFS 멀티홉 서브그래프 추출을 통해 Claude가 직접 구조적 추론을 수행하는 경량 Graph RAG 워크플로우.
  외부 DB·API 키 없이 로컬에서 동작하며, graph-config.yaml 또는 graph-ontology.yaml 하나로
  로컬 파일 시스템(Obsidian vault 포함)과 GitHub 레포 모두에 적용 가능하다.
  노드 간 관계를 N-hop으로 추적해 단일 문서 검색으로는 도달하기 어려운 연결 인사이트가 필요할 때 사용한다.
  트리거 예시: "멀티홉으로 추론해줘", "그래프 기반으로 분석해줘", "관계를 따라가며 설명해줘",
  "knowledge graph에서 인사이트 뽑아줘", "GraphRAG로 리포트 작성해줘".
---

# md-graph-multihop

Markdown 지식 베이스 entity 그래프 위에서 Claude Code가 직접 멀티홉 추론을 수행하는 워크플로우.
`ANTHROPIC_API_KEY` 불필요 — Claude Code 세션 자체가 LLM.

## 전제 조건

```bash
pip3 install langchain langchain-anthropic langchain-community networkx pyyaml
```

## 스크립트

```
scripts/
├── graph_builder.py     # 로컬 md 파일 파싱 → NetworkX DiGraph
├── graph_rag.py         # 로컬 대상 BFS 서브그래프 + 컨텍스트 CLI
└── github_adapter.py    # GitHub repo md 파일 → 그래프 (로컬 클론 불필요)
```

## 워크플로우

### 1단계 — 그래프 구조 파악

```bash
python3 scripts/graph_builder.py                   # 노드/엣지 통계
python3 scripts/graph_builder.py --search 키워드   # 노드 검색
```

### 2단계 — 서브그래프 컨텍스트 추출

```bash
# 자연어 질의 기반 (관련 노드 자동 탐색)
python3 scripts/graph_rag.py \
  --query "X가 Y에 미치는 영향" \
  --hops 2 \
  --context-only

# 특정 entity 기준
python3 scripts/graph_rag.py \
  --entity competitor__채널톡 \
  --hops 2 \
  --context-only
```

### 3단계 — Claude가 직접 추론

`--context-only` 출력(Graph Triples + Node Facts)을 받아 Claude가 멀티홉 경로를 명시하며 답변.

## 설정

`graph-config.yaml` (로컬 vault 구조에 맞게 수정):

```python
entity_dirs:
  competitor: data/competitor-entities
  industry:   data/industry-entities

relation_map:
  target_industry: targets_industry
  related:         related_to

scalar_node_attrs:
  - name
  - status
  - tags
```

또는 `graph-ontology.yaml` (OWL 스타일 단일 설정 파일, 권장):
→ `repository/graph-ontology.example.yaml` 참조

## 주요 CLI 옵션

| 옵션 | 설명 |
|------|------|
| `--query TEXT` | 자연어 질의로 관련 노드 자동 탐색 |
| `--entity NODE_ID` | 시작 노드 직접 지정 |
| `--hops N` | BFS 탐색 깊이 (기본 2) |
| `--context-only` | LLM 호출 없이 서브그래프 텍스트만 출력 |
| `--search KEYWORD` | 노드 이름/ID 키워드 검색 |
| `--config PATH` | graph-config.yaml 경로 (생략 시 자동 탐색) |

## 주의사항

**한국어 파일명 (macOS)**: HFS+는 NFD, Python 문자열은 NFC. 한글 node ID 비교 시
`unicodedata.normalize("NFC", s)` 필수. `graph_builder.py`의 `nfc()` 함수가 처리한다.

## GitHub 소스 워크플로우

로컬 파일 없이 GitHub API로 직접 그래프를 구성한다.

### 인증

```bash
export GITHUB_TOKEN=ghp_...
# 또는
gh auth login
```

### 사용

```bash
python3 scripts/github_adapter.py --repo owner/repo --stats
python3 scripts/github_adapter.py --repo owner/repo --search "keyword"
python3 scripts/github_adapter.py \
  --repo owner/repo \
  --query "X와 Y의 관계는?" \
  --hops 2
python3 scripts/github_adapter.py \
  --repo owner/repo \
  --paths docs/ wiki/ \
  --query "..."
```

### 로컬 vs GitHub 비교

| | graph_rag.py (로컬) | github_adapter.py (GitHub) |
|--|--|--|
| 데이터 소스 | 로컬 md 파일 | GitHub API |
| 링크 형식 | `[[wikilink]]` | `[[wikilink]]` + `[text](link.md)` |
| 인증 | 불필요 | GITHUB_TOKEN 또는 gh CLI |
| 속도 | 빠름 | API 호출 수에 비례 |

## 확장 포인트

- **백엔드 교체**: `graph_builder.get_graph()`가 `nx.DiGraph` 반환 → Neo4j 전환 시 이 함수만 수정
- **relation 추가**: `relation_map`에 frontmatter 필드명 추가
- **LLM 직접 호출**: `ANTHROPIC_API_KEY` 설정 후 `--context-only` 제거
