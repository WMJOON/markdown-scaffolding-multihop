# markdown-scaffolding-multihop (v0.1.6)

이 스킬셋은 **"Markdown 파일은 많이 쌓였는데, 그 안의 연결을 구조적으로 읽고 유지하고 확장하기가 어렵다"**는 문제를 풀기 위해 만들어졌습니다.

단일 문서 검색은 하나의 노트 안에 있는 정보만 돌려줍니다. 하지만 실제 인사이트는 여러 노트를 가로질러 존재합니다. markdown-scaffolding-multihop은 frontmatter와 wikilink로 선언된 관계를 실제 그래프로 파싱하고, BFS 멀티홉 추론과 유지보수 레이어를 통해 **검색·추론·구조화·유지보수**를 하나의 skillset으로 다룹니다.

v0.1.4에서 `md-kb-rewrite`를 maintenance/governance wrapper layer로 추가해 KB entropy 문제를 다루기 시작했고, **v0.1.5에서는 `ollama_mcp`로 execution plane을 분리**해 토큰 최적화를 다뤘습니다. 반복적·저위험 작업(개념 추출, 초안 생성, 유사도 필터링)을 로컬 경량 모델(`qwen3.5:4b`)에 위임하고, 의미 판단과 governance는 상위 모델이 맡는 2-plane 구조입니다. **v0.1.6에서는 온톨로지 구조 자체를 더 단단하게** 만들었습니다. `ontology/concept/[domain]/`·`ontology/instance/[domain]/` 분리로 TBox-lite와 ABox를 명확히 구분하고, 도메인 축을 `evidence/`와 정렬했습니다. 여기에 `md-mece-validator`가 추가되어 온톨로지 설계 단계부터 MECE 품질을 검증할 수 있게 됐습니다.

---

## 설계 철학: Bounded Rationality, Calibrated Validation

> 우리는 언제나 제한된 정보와 시간 안에서 판단한다.
> 즉, 모든 의사결정은 제한된 합리성(Bounded Rationality) 위에서 이루어진다.
>
> markdown-scaffolding-multihop은 이 전제를 기반으로,
> 무조건 깊은 검증이 아니라 인지 비용을 최소화하면서도 충분히 신뢰 가능한 판단을 가능하게 하는 구조를 지향한다.
>
> 이를 위해 검증 깊이를 고정하지 않고
> Light · Medium · Deep 수준으로 조정 가능한 파라미터로 두며,
> 문제의 스케일과 의사결정 중요도에 따라 최적의 검증 수준을 선택해야 한다.

---

## 기존 Markdown KB와 무엇이 다른가

|  | 기존 Markdown KB | 이 프레임워크 |
|--|-----------------|--------------|
| **노드 출처** | 어디서 왔는지 불분명 | Evidence에서 ETL된 것만 Ontology로 승격 |
| **관계 정의** | 노트 안 wikilink 임의 연결 | `schema/relation/*.yaml` 또는 `graph-ontology.yaml` 기반의 명시적 관계 정의 |
| **그래프 탐색** | 모든 파일이 같은 계층 | `ontology/` 중심 traversal, 나머지 레이어는 역할별 분리 |
| **온톨로지 구조** | 개념·인스턴스 구분 없음 | `concept/[domain]/` (TBox-lite) · `instance/[domain]/` (ABox) 명시적 분리 |
| **유지보수** | 낡은 노트·중복·semantic drift를 수동으로 정리 | `md-kb-rewrite`가 heuristic rewrite loop + framing guardrail 제공 |
| **Obsidian 필터** | 태그·폴더 혼용 | `path:ontology/` → concept·instance 노드만 정확히 반환 |
| **Neo4j 확장** | 별도 매핑 작업 필요 | `schema/` → relationship type 스키마 직접 매핑 가능 |
| **지식 신뢰도** | draft와 validated 구분 없음 | `status: raw → draft → experimental → validated` 승격 모델 |
| **로컬 보조 모델 사용** | 별도 운영 | `ollama_mcp`로 경량 개념 추출·초안 작성·후보 탐지 보조 가능 |

---

## 핵심 파이프라인

```mermaid
flowchart TD
    A["graph-ontology.yaml<br/><small>경량 온톨로지 (OWL-lite)</small>"] --> B["Entity MD 파일<br/><small>frontmatter = 속성 · wikilink = 관계</small>"]
    B --> C["NetworkX DiGraph<br/><small>인메모리 그래프 구축</small>"]
    C --> C2["Categorical Composition<br/><small>범주론적 합성 추론 (opt-in)</small>"]
    C2 --> D["Keyword 검색"]
    C2 --> E["Vector 검색 (zvec)"]
    D --> F["하이브리드 랭킹<br/><small>RRF 기반 점수 병합</small>"]
    E --> F
    F --> G["BFS N-hop 서브그래프<br/><small>멀티홉 컨텍스트 추출</small>"]
    G --> H["Claude 구조적 추론<br/><small>Graph Triples + Composition Inferences</small>"]
    B --> I["md-kb-rewrite<br/><small>heuristic rewrite + synthesis detection</small>"]
    I --> B
    I -. "concept extraction assist" .-> J["ollama_mcp / Gemma4:e4b"]
```

**KB 구축 ETL 흐름:**
```
Evidence 수집  →  Ontology ETL  →  Node Link  →  Validation 승격
(evidence/)       (ontology/)       (relations)    (status: validated)
```

**KB 유지보수 흐름:**
```
Detect  →  Diagnose  →  Draft  →  Review  →  Merge  →  Observe
(note entropy, drift, framing risk, missing synthesis)
```

---

## 레이어 구조

### Layer 1 — Structural / Retrieval / Transformation Layer

그래프 구조 생성, ETL, 멀티홉 탐색, 벡터 검색, rollup, RDF/OWL 변환.

### Layer 2 — Maintenance / Governance / Semantic Framing Layer

`md-kb-rewrite`가 담당하는 wrapper layer. rewrite candidate audit, note drift detection, evidence lag review, semantic framing risk check, missing synthesis/article/concept 후보 탐지.

이 두 레이어를 분리함으로써, 구조 스킬은 구조 처리에 집중하고, KB의 장기 유지보수와 의미 보호는 별도 wrapper layer가 맡습니다.

---

## 스킬 구성

현재 10개 스킬이 4개 영역(온톨로지 설계 · 검색추론 · 유지보수 · 운영분석)에서 협업합니다.

```mermaid
flowchart LR
    subgraph 온톨로지["온톨로지 설계·관리"]
        scaffolding["md-scaffolding-design<br/><small>KB 구조 초기화 + 온톨로지 분해</small>"]
        mece["md-mece-validator<br/><small>온톨로지 MECE 설계·검증</small>"]
        ralph["md-ralph-etl<br/><small>증거 기반 온톨로지 확장</small>"]
        rdf["md-rdf-owl-bridge<br/><small>RDF/OWL ↔ MD 변환</small>"]
    end
    subgraph 검색추론["검색·추론"]
        multihop["md-graph-multihop<br/><small>그래프 구축 + 멀티홉 추론</small>"]
        vector["md-vector-search<br/><small>zvec 벡터 인덱싱·검색</small>"]
        rollup["md-frontmatter-rollup<br/><small>엣지 기반 값 집계</small>"]
    end
    subgraph 유지보수["유지보수·거버넌스"]
        kbrewrite["md-kb-rewrite<br/><small>rewrite loop + H-A~H-X + framing guard</small>"]
    end
    subgraph 운영분석["운영·분석"]
        obsidian["md-obsidian-cli<br/><small>Obsidian vault 조작</small>"]
        analysis["md-data-analysis<br/><small>통계 분석</small>"]
    end

    config[/"graph-ontology.yaml"/]
    entities[/"Entity MD 파일"/]
    scaffolding -- "생성" --> config
    scaffolding -. "--mece 연계" .-> mece
    rdf -. "import 후 MECE 검증" .-> mece
    ralph -. "ontology 확장 후 검증" .-> mece
    mece -- "MECE 검증·개선" --> config
    config -- "읽기" --> multihop
    config -- "읽기" --> rollup
    vector -. "import graph_builder" .-> multihop
    rollup -. "import graph_builder" .-> multihop
    ralph -- "entity 추가·확장" --> entities
    rdf -- "import/export" --> entities
    obsidian -- "노트 CRUD" --> entities
    entities -- "파싱" --> multihop
    multihop -- "그래프 제공" --> vector
    multihop -- "그래프 제공" --> rollup
    multihop -- "frontmatter" --> analysis
    kbrewrite -- "노트 rewrite / draft / synthesis stub" --> entities
    kbrewrite -. "concept extraction assist" .-> ollama["ollama_mcp"]
    scaffolding -. "Workflow D: raw→wiki" .-> kbrewrite
```

### 스킬별 역할 요약

**검색·추론**

`md-graph-multihop` — KB 안에서 "A와 C가 어떻게 연결되는가?"처럼 여러 노드를 거쳐야 답이 나오는 질문에 씁니다. 그래프를 구축하고 BFS로 N-hop 서브그래프를 추출해 Claude가 구조적으로 추론할 수 있는 컨텍스트를 만듭니다.

`md-vector-search` — "이 개념과 의미상 가까운 노드가 뭔가?"처럼 키워드 매칭이 아닌 의미 기반 검색이 필요할 때 씁니다. zvec으로 벡터 인덱스를 만들고, 그래프 검색과 결합해 하이브리드 랭킹을 냅니다.

`md-frontmatter-rollup` — 하위 노드들의 숫자값(점수, 수치, 비율 등)을 상위 노드로 자동 집계할 때 씁니다. 엣지를 따라 sum/avg/weighted_avg/max/min/count를 수행합니다.

**온톨로지 설계·관리**

`md-scaffolding-design` — KB를 처음 만들거나 새 프로젝트에 그래프 구조를 심을 때 씁니다. `graph-ontology.yaml`을 자동 생성하고, Top-Down/Bottom-Up 구축 흐름을 지원합니다.

`md-mece-validator` — `graph-ontology.yaml`의 클래스·관계 구조가 MECE(상호배제·전체포괄)한지 검증하고 개선할 때 씁니다. Calibrated Validation 루프(light/medium/deep)로 리소스 투입량을 조절하며, `md-scaffolding-design`의 `--mece` 플래그로 연계 실행할 수 있습니다.

`md-ralph-etl` — URL이나 로컬 문서를 크롤링해서 KB에 새 증거 노드를 추가할 때 씁니다. 웹 페이지, 논문, 기사를 읽어 `evidence/[domain]/sources/`에 구조화된 노트로 넣습니다. v0.1.5부터 arxiv 등 PDF URL 직접 처리를 지원합니다(`step_pdf.py`).

`md-rdf-owl-bridge` — 기존 RDF/OWL 지식 그래프를 MD-frontmatter 형식으로 변환하거나 반대로 내보낼 때 씁니다.

**유지보수·거버넌스**

`md-kb-rewrite` — KB가 오래되거나 지저분해졌을 때만 쓰는 단순 정리 스킬이 아닙니다. 이 스킬은 **maintenance/governance wrapper layer**로서, 6단계 rewrite loop와 H-A~H-X 휴리스틱으로 노트 품질 문제를 진단하고, semantic framing risk를 점검하고, missing synthesis/article 후보까지 탐지합니다. 필요 시 `ollama_mcp`와 연동해 개념 추출이나 경량 초안 생성을 보조시킵니다.

**운영·분석**

`md-obsidian-cli` — Claude가 Obsidian vault의 노트를 직접 읽고 쓰고 검색해야 할 때 씁니다. 노트 CRUD, 태그 검색, 플러그인 제어를 처리합니다.

`md-data-analysis` — frontmatter, CSV, JSON 형태로 쌓인 KB 데이터를 통계적으로 분석할 때 씁니다. 기술통계, 상관, 회귀, 시계열을 지원합니다.

### 스킬 간 의존 관계

| 소비자 | 제공자 | 계약 유형 |
|--------|--------|---------|
| `md-vector-search` | `md-graph-multihop` | **코드 import** — `graph_builder.build_graph()`, `nfc()` |
| `md-frontmatter-rollup` | `md-graph-multihop` | **코드 import** — `graph_builder.build_graph()`, `nfc()` |
| `md-graph-multihop` | `md-scaffolding-design` | **설정 파일** — `graph-config.yaml` 생성 → 소비 |
| `md-graph-multihop` | `md-ralph-etl` | **데이터** — entity MD 파일 추가/확장 |
| `md-graph-multihop` | `md-rdf-owl-bridge` | **데이터** — RDF import → entity MD 파일 생성 |
| `md-graph-multihop` | `md-obsidian-cli` | **데이터** — 노트 CRUD → entity MD 파일 변경 |
| `md-data-analysis` | `md-graph-multihop` | **데이터** — frontmatter 추출 결과 분석 (느슨한 결합) |
| `md-kb-rewrite` | `md-scaffolding-design` | **워크플로우** — Workflow D raw→wiki 컴파일 연동 |
| `md-kb-rewrite` | `ollama_mcp` | **보조 추론** — concept extraction / lightweight drafting |
| `md-scaffolding-design` | `md-mece-validator` | **스크립트 import** — `--mece` 플래그로 `mece_interview.py` 직접 호출 |
| `md-rdf-owl-bridge` | `md-mece-validator` | **워크플로우** — 외부 온톨로지 import 후 MECE 구조 재검증 |
| `md-ralph-etl` | `md-mece-validator` | **워크플로우** — Bottom-Up ETL로 새 클래스 추가 후 MECE 재검증 |

---

## 문서

| 문서 | 설명 |
|------|------|
| [빠른 시작](docs/guides/quickstart.md) | 설치, 지원 소스, 기본 명령어 |
| [온톨로지 설정](docs/guides/ontology-config.md) | graph-ontology.yaml, Morphism Extension, 설정 파일 |
| [KB 디렉토리 구조](docs/kb-directory-structure.md) | concept/instance 도메인 분리, ETL 흐름, 상태 모델 |
| [KB 구축 흐름](docs/guides/kb-build-flows.md) | Top-Down / Bottom-Up 전략, 검증 깊이 루브릭 |
| [워크플로우 A~D](docs/guides/workflows.md) | 상황별 스킬 조합, ollama_mcp 연동 패턴 |
| [KB 유지보수](docs/guides/kb-maintenance.md) | Rewrite loop, H-A~H-X 휴리스틱, Workflow D |
| [스킬 구성](docs/skills.md) | 전체 스킬 목록, 역할, 레퍼런스 링크 |
| [Changelog](docs/changelog.md) | 전체 버전별 변경 이력 |

---

## Roadmap

```text
v0.1.x  개인 업무 환경 검증 — Evidence-first KB 구조 정립
v0.2.x  rewrite/governance/semantic framing 레이어 고도화
```

---

## 의존성

- Python 3.10+
- `pip install -r requirements.txt`
- 선택적 보조 레이어: `ollama_mcp` + Ollama 로컬 모델 (`qwen3.5:4b` 권장)

## License

MIT
