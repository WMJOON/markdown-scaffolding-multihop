# KB 구축 ELT 흐름 가이드

v0.14.0의 KB 구축은 ETL보다 ELT에 가깝습니다. 원문과 후보를 먼저 `evidence/`와 candidate queue에 적재하고, source validation·MECE·HITL·inference preview 이후 검증된 subset만 ontology 정본으로 승격합니다.

---

## Evidence 수집 경로

| 경로 | 언제 | 스크립트 |
|------|------|---------|
| URL / 로컬 MD | 논문·문서·웹 페이지 수집 | `msm-evidence collect` |
| Graphify ELT | 코드베이스 graph를 evidence 후보로 적재 | `graphify_to_msm.py` |
| Semantic relation 후보 | 기존 KB chunk에서 directed relation 후보 생성 | `msm-semantic-search link-relations` |
| 수동 작성 | 직접 `evidence/seeds.jsonl`에 추가 | — |

### ELT 기본 흐름

```
Extract
  URL / Markdown / graph.json / 기존 ontology registry
    ↓
Load
  evidence/seeds.jsonl
  evidence/md/
  evidence/graphify/*_candidates.jsonl
  evidence/semantic-link/relation_candidates.jsonl
  evidence/semantic-link/axiom_candidates.jsonl
  zvec index
    ↓
Transform / Promote
  source validation
  MECE + parent-alignment
  relation predicate review
  axiom risk tier + inference preview
    ↓
ontology/explain/ + ontology/system/ + relations.jsonl
```

### Graphify ELT 흐름

코드베이스를 KB evidence로 수집할 때 씁니다. `file_type == "concept"` 노드만 통과시켜 시맨틱 추상화를 유지합니다.

```
graphify .
    ↓ Step 1–2: Tree-sitter AST + LLM 시맨틱 추출
graph.json (nodes: code + concept + document)
    ↓ Extract/Load: graphify_to_msm.py (concept 필터 + god node 탐지)
evidence/graphify/entity_candidates.jsonl   ← concept 노드만
evidence/graphify/relation_candidates.jsonl ← concept 간 엣지
    ↓ Transform/Promote: source validation + msm-ontology add --apply
ontology/explain/concept/{cluster}/entities.jsonl      ← MECE 검증 후 승격
```

### Semantic Relation ELT 흐름

기존 KB에 entity는 있지만 관계가 희박할 때 씁니다. 자세한 predicate 의미와 승격 기준은 [Semantic Relations](../semantic-relations.md)를 따릅니다.

```
ontology/**/entities.jsonl
    ↓ Extract: entity label/alias/description
zvec semantic expansion
    ↓ Load: 유사 chunk 후보 + content window
evidence/semantic-link/relation_candidates.jsonl
    ↓ Transform: direction cue 검토 + source validation
relations.jsonl
    ↓ 필요 시 axiom 후보 분리
evidence/semantic-link/axiom_candidates.jsonl
```

---

## 전략 선택 기준

| 조건 | 전략 |
|------|------|
| 도메인 구조가 선명하고 evidence 미수집 | **Top-Down** |
| 도메인 구조 불명확하고 evidence 이미 있음 | **Bottom-Up** |
| 코드베이스 구조를 KB로 수집 | **Graphify ELT** |
| entity는 있으나 관계가 희박함 | **Semantic Relation ELT** |

---

## Top-Down Flow

구조를 먼저 설계하고 evidence/candidate를 채웁니다.

```
msm init (explain/concept · explain/instance 골격)
    ↓
msm-ontology add (explain/concept (TBox) 클래스 정의)
    ↓
msm-evidence collect (URL/MD → seeds)
    ↓
Load: evidence/seeds.jsonl + semantic candidate queues
    ↓
msm-ontology add (검증된 explain/instance (ABox) 인스턴스 승격)
    ↓
msm-ontology mece (MECE 검증)
    ↓
status: draft → experimental → validated
```

---

## Bottom-Up Flow

evidence와 후보를 먼저 적재하고 구조를 귀납합니다.

```
msm-evidence collect (URL/MD → seeds)
    ↓
반복 등장 개념 추출
    ↓
Load: relation_candidates.jsonl / axiom_candidates.jsonl 후보 분리
    ↓
msm-ontology add (검증된 explain/concept (TBox) 클래스 귀납 정의)
    ↓
msm-ontology add (explain/instance (ABox) 인스턴스 배치)
    ↓
msm-ontology mece (MECE 검증 + 보완)
    ↓
status 승격
```

---

## 핵심 규칙

**Rule 1. ontology ≠ evidence**
- `ontology/explain/concept/` = 클래스·관계 정의 (normalization)
- `ontology/explain/instance/` = 인스턴스 (normalization)
- `evidence/` = 정당화 근거 (justification)
- `evidence/semantic-link/` = relation/axiom 후보 review queue. 정본이 아니다.

**Rule 2. 검증 깊이**

| 수준 | 대상 | `msm-ontology mece --depth` |
|------|------|--------------------------|
| light | 정착된 개념 | `light` — 구조 배치만 확인 |
| medium | 도메인 특화 claim | `medium` — evidence 2개 대조 |
| deep | 신규 synthesis | `deep` — 반박 가능성 포함 |

**Rule 3. 종료 조건**
재시도 1회 후 미달이면 status를 한 단계 낮춰 기록하고 종료합니다. 루프를 계속 돌리는 것보다 낮은 status로 기록하는 편이 효율적입니다.
