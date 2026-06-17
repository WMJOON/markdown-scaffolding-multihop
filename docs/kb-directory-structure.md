# KnowledgeBase 디렉토리 구조 (v0.11.1)

> **MSM = Human-Agent KnowledgeBase Management System**
> 인간과 에이전트가 함께 운용하는 KnowledgeBase를 관리하는 시스템.
> 본 문서는 v0.11.0 디렉토리 룰(D-1~D-7) + v0.11.1 거버넌스 오버레이를 기준으로 한다.

---

## 거버넌스 오버레이 (v0.11.1)

> [!important] Concept/Instance 관리 정책
> Concept은 HITL 필수, Instance는 연결 깊이에 따라 차등 자동화.

| 계층 | 관리 정책 | 자동화 |
|------|---------|--------|
| **Concept** (이론/정의, Tbox) | HITL / HITLFE 검수 필수 | ❌ 사람 승인 없이 자동 생성·수정 금지 |
| **Instance — 상위 Concept 직접 연결** | 관리 대상 (Human-supervised) | ⚠️ 수동 생성 또는 검수 후 자동화 |
| **Instance — 하위 Concept 간접 연결** | 동적 자동화 (Self-healing) | ✅ 에이전트 자율 처리 |

### 적용 예

```text
concept__statistics                          ← Concept (HITL 필수)
  └─ Has Instances (직접 연결)
      ├─ instance__descriptive-statistics    ← 관리 대상 (상위 직접)
      ├─ instance__inferential-statistics    ← 관리 대상 (상위 직접)
      └─ instance__regression-analysis       ← 관리 대상 (상위 직접)

concept__descriptive-statistics              ← 하위 Concept (HITL 필수)
  └─ Has Instances (간접 연결, 동적)
      ├─ instance__descriptive-example-1     ← 동적 자동화 (하위 간접)
      ├─ instance__descriptive-example-2     ← 동적 자동화 (하위 간접)
      └─ ...                                  ← 자동 생성 가능
```

### Why

- **Concept = 온톨로지 백본** → 실수 시 전체 구조 붕괴 → HITL 필수
- **상위 Instance** = 대표 사례 → 품질 보증 필요 → 관리 대상
- **하위 Instance** = 패턴화된 대량 사례 → 자동화 효율 우선 → 동적 처리

> [!note] Enforcement
> 정책의 자동 강제(가드, 검증)는 v0.12.0에서 `msm-ontology` HITL 가드 및 `msm-maintain` instance 티어 검증으로 구현 예정. v0.11.1은 문서화 레이어.

---

## 전체 구조 (D-7)

```text
{kb-root}/                          ← knowledgeBase 루트
  canonical_root_hub.yaml           ← locked SSOT (도메인·경로 선언)
  ontology/
    system/                         ← 형식 표현 (machine-readable, OWL/RDF/JSON-LD)
      system__class.md              ← L1 anchor
      semantic/                     ← 정적 의미 관계
        semantic__class.md          ← L2 anchor
      kinetic/                      ← 작용·변환 (workflow, action)
        kinetic__class.md
      dynamic/                      ← 변화·시간성 (event, state-change)
        dynamic__class.md
    explain/                        ← 자연어 표현 (human-readable, narrative)
      explain__class.md             ← L1 anchor
      concept/                      ← 추상 개념 (Class)
        concept__class.md           ← L2 anchor
        {cluster}/                  ← 도메인 클러스터 (L0 of explain.concept)
          {cluster}__class.md
          {entity-type}__{slug}.md  ← Class (type=concept/pattern/technique/...)
          {sub-class}/
            {sub-class}__class.md
            ...
      instance/                     ← 구체 사례 (Instance)
        instance__class.md
        {cluster}/
          {slug}__entity.md         ← Instance (ABox 룰, TBD v0.12.0)
  evidence/                         ← 원본·seed (sources, citations)
    seeds.jsonl
    md/
    graphify/                       ← Graphify ETL 출력
      entity_candidates.jsonl
      relation_candidates.jsonl
  planning/                         ← 장기 태스크 계획
  report/                           ← 설명 문서·논문
  workflow/                         ← yaml 정의 워크플로우
    {category}/*.yaml
    index.yaml
  memory/                           ← 2-tier 메모리
    task-context/
    ontology-index/
  harness/                          ← 하네스·런타임
    run.sh
    reports/
  .claude/                          ← 스킬·훅
    skills/
    hooks/
```

---

## v0.11.0 결정사항 (D-1 ~ D-7)

| D# | 결정 | 비고 |
|----|------|------|
| **D-1** | 부모 노드 명명: `{dir-name}__class.md` | 디렉토리 anchor |
| **D-2** | 단일 부모 원칙 | 다중 도메인 = `cross_reference` |
| **D-3** | L0~L4 권장, L5+ 자유 | L0=Canonical Cluster |
| **D-4** | 5축 분류(Model/Runtime/...) 비강제 | `--template 5axis` 옵션 |
| **D-5** | `unclassified/` 디렉토리 운영 | 분류 보류 entity |
| **D-6** | TBox=Class / ABox=Instance | 의미 차원 분리 |
| **D-7** | 4계층 구조 (system / explain / evidence) | MSM identity |

---

## 두 큰 분기: `system/` vs `explain/`

| 영역 | 책임 | 표현 방식 | 상태 |
|------|------|----------|------|
| **ontology/system/** | 형식 logic — 기계 추론용 | RDF/OWL/JSON-LD | ⏳ v0.12.0 (advanced, optional) |
| **ontology/explain/** | 자연어 narrative — 인간 이해용 | Markdown (frontmatter + body) | ✅ 운영 중 (기본) |
| **evidence/** | 1차/2차 출처 자료 | URL, source-note, citation | ✅ 운영 중 (기본) |

- **explain ↔ system** 매핑: 같은 의미를 두 표현으로 (cross-cutting)
- **ontology ↔ evidence** 매핑: 모든 개념·사례는 evidence 근거 (Sorcelink Rule)

> [!tip] 기본 운영 원칙 — Narrative-first
> 대부분의 KB는 **`evidence/` + `ontology/explain/`만으로 충분**하다.
> `system/`은 OWL/RDF 학습이 필요한 advanced layer로, 명시적 필요(기계 추론, SPARQL 쿼리, 외부 RDF 통합 등)가 있을 때만 도입한다.
> MSM의 기본 모드는 narrative-first이며, formal logic은 선택사항이다.

---

## explain의 두 분기 (D-6)

### `ontology/explain/concept/` — 추상 Class

```yaml
---
entity: concept__reinforcement-learning
type: concept            # Class의 sub-category (concept/pattern/technique/...)
cluster: technical
status: draft
relations:
  - type: belongs_to
    target: "[[reinforcement-learning__class|Reinforcement Learning Class]]"
    category_axis: cluster
---
```

prefix(`concept__`, `pattern__`, `technique__` 등)는 모두 **Class의 type-axis**.
TBox 영역의 모든 노드는 본질적으로 Class.

### `ontology/explain/instance/` — 구체 Instance

```yaml
---
entity: gpt4__entity
type: instance
type_of: "[[language-model__class|Language Model Class]]"
cluster: technical
status: experimental
source_doc_id: evidence__openai_gpt4
---
```

ABox 영역의 모든 노드는 인스턴스. `type_of` 관계로 TBox class와 연결.

> ⚠️ ABox SPEC은 v0.12.0에서 확정 (OI-E).

---

## 부모 노드 anchor 패턴 (D-1 ~ D-3)

```
{cluster}/
├── {cluster}__class.md             ← L0 (Canonical Cluster anchor)
├── concept__X.md                    ← 자식 Class (type=concept)
├── pattern__Y.md                    ← 자식 Class (type=pattern)
└── {sub-class}/                     ← 더 세분화
    ├── {sub-class}__class.md        ← L1 anchor
    └── ...
```

- **부모 anchor**: `{dir-name}__class.md`
- **자식 Class**: `{type}__{slug}.md`
- **레벨**: L0 (cluster) → L1 (sub-cluster) → ... → L4 (권장 최대) → L5+ (경고만)

---

## `unclassified/` 디렉토리 (D-5)

분류 보류 entity는 클러스터별 unclassified로 격리:

```
ontology/explain/concept/unclassified/{cluster}__unclassified.md
ontology/explain/instance/unclassified/{cluster}__unclassified.md
```

scan/validator는 정상 디렉토리로 인식하되 잔여 카운트를 리포트에 포함.

---

## ETL 흐름

```
Evidence 수집
  (msm-evidence: URL/MD → seeds.jsonl)
  (graphify_to_msm.py: graph.json → entity_candidates.jsonl)
      ↓
Ontology 승격
  (msm-ontology: MECE 검증 → explain/concept/ + entities.jsonl)
      ↓
Status 승격
  draft → experimental → validated
      ↓
parent_alignment scan
  (msm-maintain: D-1~D-7 6규칙 검증)
```

---

## canonical_root_hub.yaml 스키마 (v0.11.0)

```yaml
version: "1.1"
locked: true
identity: "Human-Agent KnowledgeBase Management System"
domains:
  technical:
    concept: ontology/explain/concept/technical/
    instance: ontology/explain/instance/technical/
    relations: ontology/explain/concept/technical/entities.jsonl
  marketing:
    concept: ontology/explain/concept/marketing/
    instance: ontology/explain/instance/marketing/
system:                              # v0.12.0 예정
  semantic: ontology/system/semantic/
  kinetic:  ontology/system/kinetic/
  dynamic:  ontology/system/dynamic/
```

`locked: true`인 경우 `msm-ontology`를 통해서만 갱신 가능.

---

## v0.10.0 → v0.11.0 마이그레이션 매핑

| v0.10.0 | v0.11.0 |
|--------|--------|
| `ontology/Tbox/{cluster}/` | `ontology/explain/concept/{cluster}/` |
| `ontology/Abox/{cluster}/` | `ontology/explain/instance/{cluster}/` |
| `{name}__hub.md` | `{name}__class.md` (D-1) |
| (없음) | `ontology/system/{semantic, kinetic, dynamic}/` (placeholder) |
| (없음) | `unclassified/` 패턴 (D-5) |

---

## 관련 문서

- [빠른 시작](guides/quickstart.md)
- [온톨로지 설정](guides/ontology-config.md)
- [KB 구축 흐름](guides/kb-build-flows.md)
- [PRD v0.11.0](../../planning/msm_v0.11.0/msm_v0.11.0-PRD.md)
- [Parent Alignment SPEC](../../planning/msm_v0.11.0/msm-parent-alignment-SPEC.md)
