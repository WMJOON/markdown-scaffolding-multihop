# 스킬 구성

## 검색·추론

| 스킬 | 역할 | 문서 |
|------|------|------|
| `md-graph-multihop` | 그래프 구축 + BFS 멀티홉 서브그래프 추출 + 키워드 노드 검색 | [SKILL.md](../skills/md-graph-multihop/SKILL.md) |
| `md-vector-search` | zvec 벡터 인덱싱 + 시맨틱 노드 검색 + 하이브리드(Graph×Vector) 랭킹 | [SKILL.md](../skills/md-vector-search/SKILL.md) |
| `md-frontmatter-rollup` | 엣지를 따라 frontmatter 값 집계 (sum/avg/weighted_avg/max/min/count) | [SKILL.md](../skills/md-frontmatter-rollup/SKILL.md) |

## 온톨로지 설계·관리

| 스킬 | 역할 | 문서 |
|------|------|------|
| `md-scaffolding-design` | KB 구조 초기화 + 온톨로지 분해 → `graph-ontology.yaml` 생성 | [SKILL.md](../skills/md-scaffolding-design/SKILL.md) |
| `md-rdf-owl-bridge` | RDF/OWL ↔ MD-frontmatter 양방향 변환 + KG 임베딩 + placement | [SKILL.md](../skills/md-rdf-owl-bridge/SKILL.md) |
| `md-ralph-etl` | URL/로컬 문서 크롤링 → 증거 기반 온톨로지 확장 ETL | [SKILL.md](../skills/md-ralph-etl/SKILL.md) |

## 운영·분석

| 스킬 | 역할 | 문서 |
|------|------|------|
| `md-obsidian-cli` | Obsidian vault CLI 조작 (노트 CRUD, 검색, 플러그인 제어) | [SKILL.md](../skills/md-obsidian-cli/SKILL.md) |
| `md-data-analysis` | frontmatter / CSV / JSON 통계 분석 (기술통계, 상관, 회귀, 시계열) | [SKILL.md](../skills/md-data-analysis/SKILL.md) |

## 스킬 레퍼런스

| 스킬 | 레퍼런스 |
|------|---------|
| `md-scaffolding-design` | [modules/](../skills/md-scaffolding-design/modules/) · [references/](../skills/md-scaffolding-design/references/) |
| `md-graph-multihop` | [core.md](../skills/md-graph-multihop/core.md) |
| `md-ralph-etl` | [core.md](../skills/md-ralph-etl/core.md) |
| `md-rdf-owl-bridge` | [core.md](../skills/md-rdf-owl-bridge/core.md) |
| `md-vector-search` | [core.md](../skills/md-vector-search/core.md) |
| `md-frontmatter-rollup` | [core.md](../skills/md-frontmatter-rollup/core.md) |
