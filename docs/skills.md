# 스킬 구성

이 문서는 markdown-scaffolding-multihop을 구성하는 10개 스킬의 역할과 사용 시점을 설명합니다. 각 스킬은 명확한 단일 책임을 가지며, 상황에 맞는 스킬을 선택해 조합합니다.

---

## 검색·추론

### `md-graph-multihop`

**무엇을 하나:** frontmatter와 wikilink로 선언된 노드 관계를 NetworkX 그래프로 파싱하고, BFS N-hop 서브그래프를 추출해 Claude가 구조적으로 추론할 수 있는 컨텍스트를 만듭니다.

**이런 상황에서 쓰세요:**
- "A 개념이 C 개념에 어떻게 이어지는지 추론해줘" — 두 노드 사이의 연결 경로를 따라가야 할 때
- "이 키워드와 관련된 노드를 그래프 기반으로 찾아줘" — 단순 검색이 아닌 관계 기반 탐색이 필요할 때

→ [SKILL.md](../skills/md-graph-multihop/SKILL.md)

---

### `md-vector-search`

**무엇을 하나:** zvec으로 KB 노드의 벡터 인덱스를 만들고, 시맨틱 검색 결과와 그래프 검색 결과를 RRF 방식으로 결합해 하이브리드 랭킹을 냅니다.

**이런 상황에서 쓰세요:**
- "이 개념과 의미상 비슷한 노드가 뭔지 찾아줘" — 키워드가 정확히 일치하지 않아도 의미가 가까운 노드를 찾을 때
- 그래프 검색 단독으로는 놓치는 의미적 유사 노드가 있을 것 같을 때

→ [SKILL.md](../skills/md-vector-search/SKILL.md)

---

### `md-frontmatter-rollup`

**무엇을 하나:** 엣지를 따라 인접 노드의 frontmatter 숫자값을 상위 노드로 집계합니다. sum, avg, weighted_avg, max, min, count를 지원합니다.

**이런 상황에서 쓰세요:**
- "하위 개념 노드들의 점수/비율/수치를 상위 노드에 자동으로 합산하고 싶다"
- "각 sub-concept의 adoption_rate를 부모 개념에 가중평균으로 집계해줘"

→ [SKILL.md](../skills/md-frontmatter-rollup/SKILL.md)

---

## 온톨로지 설계·관리

### `md-scaffolding-design`

**무엇을 하나:** KB를 처음 설계할 때 `graph-ontology.yaml`을 자동 생성하고, `ontology/` · `schema/` · `evidence/` · `context/` · `docs/` 디렉토리 구조를 초기화합니다. Top-Down(structure-first)과 Bottom-Up(evidence-first) 두 가지 구축 전략을 지원하며, 노드 유형별 검증 깊이(Light/Medium/Deep) 루브릭을 제공합니다. Claude의 추론 결과를 wikilink가 연결된 md 노드로 저장하는 기능도 포함합니다.

**이런 상황에서 쓰세요:**
- "새 KB를 만들려는데 어떤 폴더 구조로 시작해야 할지 모르겠다"
- "Claude가 분석한 인사이트를 그래프에 노드로 남기고 싶다"
- "이 GitHub repo에 멀티홉 추론 구조를 심어줘"

→ [SKILL.md](../skills/md-scaffolding-design/SKILL.md)

---

### `md-mece-validator`

**무엇을 하나:** `graph-ontology.yaml`의 클래스·관계 구조가 MECE(상호배제·전체포괄)한지 검증하고 개선합니다. Calibrated Validation 루프로 Socratic 인터뷰를 진행하고, 인터뷰 내용을 반영해 온톨로지를 결정화(crystallize)한 뒤 `mece_assessment` 블록을 자동 생성합니다. `depth` 파라미터 하나로 LLM 호출 수·라운드·게이트·출력물을 동시에 제어합니다.

**이런 상황에서 쓰세요:**
- "온톨로지 클래스들이 겹치는 것 같아, MECE한지 확인해줘"
- "graph-ontology.yaml 구조 설계할 때 빠진 개념이나 관계가 없는지 점검해줘"
- `md-scaffolding-design`으로 구조를 만든 뒤 MECE 품질을 보장하고 싶을 때
- `md-rdf-owl-bridge`로 외부 온톨로지를 import한 뒤 변환된 구조의 MECE를 재검증하고 싶을 때
- `md-ralph-etl`로 Bottom-Up ETL 후 새 클래스·관계가 추가됐을 때 기존 구조와의 MECE를 확인하고 싶을 때

| depth  | 언제 | LLM 호출 |
|--------|------|---------|
| light  | 빠른 구조 확인, 아는 도메인 | 0회 (heuristic) |
| medium | 일반 KB 설계 | 4-6회, 게이트 ≥0.75 |
| deep   | 신규·복잡 도메인 | 15-24회, 게이트 ≥0.85 |

→ [SKILL.md](../skills/md-mece-validator/SKILL.md)

---

### `md-rdf-owl-bridge`

**무엇을 하나:** 기존 RDF/OWL 지식 그래프를 MD-frontmatter 형식으로 변환하거나, 반대로 MD 구조를 RDF로 내보냅니다. KG 임베딩과 placement도 지원합니다.

**이런 상황에서 쓰세요:**
- "Wikidata나 외부 온톨로지 데이터를 KB에 가져오고 싶다"
- "이 KB를 RDF/OWL 형식으로 내보내야 한다"

→ [SKILL.md](../skills/md-rdf-owl-bridge/SKILL.md)

---

### `md-ralph-etl`

**무엇을 하나:** URL이나 로컬 문서를 크롤링해서 핵심 내용을 추출하고, `evidence/[domain]/sources/`에 구조화된 노트로 저장합니다. 증거 기반으로 온톨로지를 확장할 때 쓰는 ETL 파이프라인입니다.

**이런 상황에서 쓰세요:**
- "이 논문 URL을 읽어서 KB에 evidence 노트로 추가해줘"
- "웹 기사들을 수집해서 특정 topic의 evidence 폴더를 채우고 싶다"

→ [SKILL.md](../skills/md-ralph-etl/SKILL.md)

---

## 유지보수·거버넌스

### `md-kb-rewrite`

**무엇을 하나:** KB가 오래되거나 지저분해졌을 때 품질을 복원합니다. 6단계 rewrite loop와 8가지 휴리스틱(H-A~H-X)으로 노트의 문제를 진단하고, 위험도에 따라 자동 반영 또는 human review 경로를 선택합니다. 반복적인 텍스트 작업은 ollama_mcp(로컬 Gemma)에 위임할 수 있습니다.

**이런 상황에서 쓰세요:**
- "이 노트들 품질이 낮아진 것 같은데 한번 점검해줘"
- "새 논문을 추가했는데 기존 노드에 반영이 안 됐어"
- "KB 전체에서 orphan 노드를 찾아서 연결해줘"

#### rewrite loop 6단계

rewrite는 감각적으로 고치는 게 아니라 정해진 순서를 따릅니다.

1. **Detect** — H-A~H-X 휴리스틱을 기준으로 문제가 있는 노트를 스캔합니다. 어떤 휴리스틱에 걸렸는지 식별합니다.
2. **Diagnose** — 어떤 종류의 rewrite가 필요한지, 위험도(Low/Medium/High)는 어느 수준인지 분류합니다.
3. **Draft** — rationale(왜 이렇게 고쳤는가)을 포함한 controlled rewrite를 작성합니다. 변경한 것과 유지한 것을 명시합니다.
4. **Review** — 위험도에 따라 경로를 분기합니다. Low는 자동 반영 가능, Medium은 variant 파일 생성 후 검토, High는 반드시 human review를 거칩니다.
5. **Merge** — 승인된 rewrite를 적용합니다. in-place overwrite, 새 variant 파일, 또는 sidecar note 중 상황에 맞게 선택합니다.
6. **Observe** — `context/rewrite-log/`에 변경 이력을 기록합니다. 어떤 휴리스틱이 트리거됐고, 수동 검토 여부, 수락/거절 결과를 남깁니다.

→ [SKILL.md](../skills/md-kb-rewrite/SKILL.md)

---

## 운영·분석

### `md-obsidian-cli`

**무엇을 하나:** Claude가 Obsidian vault의 노트를 직접 읽고 쓰고 검색할 수 있게 해주는 CLI 인터페이스입니다. 노트 CRUD, 태그·링크 검색, 플러그인 제어를 지원합니다.

**이런 상황에서 쓰세요:**
- "Obsidian vault 안의 특정 노트를 찾아서 수정해줘"
- 다른 스킬들이 entity MD 파일을 직접 읽고 써야 할 때 (대부분 내부적으로 사용됨)

→ [SKILL.md](../skills/md-obsidian-cli/SKILL.md)

---

### `md-data-analysis`

**무엇을 하나:** KB 노드들의 frontmatter 값, CSV, JSON 형태로 수집된 데이터를 통계적으로 분석합니다. 기술통계, 상관, 회귀, 시계열을 지원합니다.

**이런 상황에서 쓰세요:**
- "KB에 있는 노드들의 status 분포를 집계해줘"
- "특정 frontmatter 필드값들의 추세를 시계열로 보여줘"

→ [SKILL.md](../skills/md-data-analysis/SKILL.md)

---

## 스킬 레퍼런스

각 스킬의 상세 구현과 설정 방법은 아래 레퍼런스 파일을 참조하세요.

| 스킬 | 레퍼런스 |
|------|---------|
| `md-scaffolding-design` | [modules/](../skills/md-scaffolding-design/modules/) · [references/](../skills/md-scaffolding-design/references/) |
| `md-mece-validator` | [references/depth-guide.md](../skills/md-mece-validator/references/depth-guide.md) |
| `md-graph-multihop` | [core.md](../skills/md-graph-multihop/core.md) |
| `md-kb-rewrite` | [core.md](../skills/md-kb-rewrite/core.md) |
| `md-ralph-etl` | [core.md](../skills/md-ralph-etl/core.md) |
| `md-rdf-owl-bridge` | [core.md](../skills/md-rdf-owl-bridge/core.md) |
| `md-vector-search` | [core.md](../skills/md-vector-search/core.md) |
| `md-frontmatter-rollup` | [core.md](../skills/md-frontmatter-rollup/core.md) |
