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
  "추론 결과 노드로 저장해줘", "knowledge graph 인사이트 뽑아줘"
---

# md-kb-graph

## 워크플로우 선택

| 목적 | 워크플로우 |
|------|---------|
| 새 프로젝트에 그래프 구조 세팅 | [A] Scaffolding |
| 기존 그래프에서 멀티홉 추론 | [B] Graph RAG |
| 자연어로 관련 노드 탐색 | [C] Vector Search |
| 추론 결과를 그래프에 다시 저장 | [D] Save Insight |

---

## 전제 조건

```bash
pip3 install langchain langchain-anthropic langchain-community networkx pyyaml zvec
```

---

## [A] Scaffolding — 그래프 구조 초기화

`scaffold_project.py` (md-scaffolding-design 스킬의 scripts/ 에 위치)

```bash
# 로컬 디렉토리 분석 → graph-config.yaml 자동 생성
python3 scaffold_project.py --local ./my-docs --output ./graph-config.yaml

# 프리셋으로 즉시 초기화 (personal-memory | github-docs | git-repo | obsidian-vault | any-markdown)
python3 scaffold_project.py --template obsidian-vault --output ./graph-config.yaml

# GitHub repo 분석
python3 scaffold_project.py --repo owner/repo --output ./graph-config.yaml
```

설정 필드 상세: `graph-config.yaml` 또는 `graph-ontology.yaml` (OWL 스타일, 권장).

---

## [B] Graph RAG — 멀티홉 추론

`graph_builder.py` + `graph_rag.py` + `github_adapter.py` (md-graph-multihop 스킬의 scripts/)

```bash
# 그래프 구조 파악
python3 graph_builder.py                    # 노드/엣지 통계
python3 graph_builder.py --search 키워드    # 노드 검색

# 서브그래프 추출 (자연어 질의)
python3 graph_rag.py --query "X가 Y에 미치는 영향" --hops 2 --context-only

# 특정 노드 기준
python3 graph_rag.py --entity node__slug --hops 2 --context-only

# GitHub repo 직접 (로컬 클론 불필요)
python3 github_adapter.py --repo owner/repo --query "..." --hops 2
```

`--context-only` 출력(Graph Triples + Node Facts)을 받아 Claude가 멀티홉 경로를 명시하며 추론.

**한국어 파일명 (macOS)**: HFS+ NFD ↔ Python NFC 불일치 → `graph_builder.py`의 `nfc()` 함수가 자동 처리.

---

## [C] Vector Search — 시맨틱 노드 탐색

`scripts/zvec_graph_index.py` 참조: `references/zvec-graph-ops.md`

```bash
# 인덱스 빌드
python3 scripts/zvec_graph_index.py index

# 시맨틱 노드 검색
python3 scripts/zvec_graph_index.py search "경쟁사의 시장 진입 전략"

# Graph RAG와 연계 (벡터 검색 → 멀티홉)
NODE_ID=$(python3 scripts/zvec_graph_index.py search "시장 점유율" --top1)
python3 graph_rag.py --entity "$NODE_ID" --hops 2 --context-only
```

embedder 변경 시 `--force`로 재인덱싱. 인덱싱과 검색에 동일한 embedder 사용 필수.

---

## [D] Save Insight — 결과 저장

`save_insight.py` (md-scaffolding-design 스킬의 scripts/)

```bash
python3 save_insight.py \
  --title "분석 제목" \
  --content "내용" \
  --links "node-a,node-b" \
  --config graph-config.yaml
```

저장 후 `graph_builder.py` 재실행하면 인사이트 노드가 그래프에 포함되어 다음 멀티홉에서 활용 가능.

---

## 관련 스킬

- `msm-mece-validator` — graph-ontology.yaml MECE 검증 (`scaffold_project.py --mece` 연계 가능)
- `msm-kb-rewrite` — 인사이트 노드 정제 후 KB 편입
