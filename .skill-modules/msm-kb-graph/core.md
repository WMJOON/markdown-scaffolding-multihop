# md-graph-multihop — Core

## 역할

Markdown 기반 지식 베이스를 NetworkX 인메모리 그래프로 파싱하고,
BFS 멀티홉 서브그래프 추출 → Claude 직접 추론 파이프라인을 제공한다.

로컬 파일 시스템(Obsidian vault 포함), GitHub API 모두 지원한다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **node** | entity md 파일 1개. frontmatter 필드가 속성 |
| **edge** | frontmatter wikilink(RELATION_MAP) 또는 본문 `[[link]]` / `[text](link.md)` |
| **subgraph** | 시작 노드에서 BFS N-hop으로 추출한 부분 그래프 |
| **context** | subgraph를 Graph Triples + Node Facts 텍스트로 직렬화한 것 |

## 모듈 구성

- `module.graph-build.md` — 그래프 구축 정책 (파싱, NFC 정규화, edge 분류)
- `module.multihop-query.md` — 서브그래프 추출 및 노드 탐색 정책
- `module.github-source.md` — GitHub API 소스 어댑터 정책

## 스크립트 의존성

```
graph_builder.py   → PyYAML, networkx
graph_rag.py       → graph_builder, langchain-anthropic (선택)
github_adapter.py  → graph_builder, requests
```

## 설정 진입점

| 파일 | 설명 |
|------|------|
| `graph-config.yaml` | entity_dirs / relation_map / scalar_node_attrs (기본) |
| `graph-ontology.yaml` | OWL 스타일 단일 진실 소스 (rollup_engine이 자동 도출) |
