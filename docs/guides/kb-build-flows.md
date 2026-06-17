# KB 구축 흐름 가이드

v0.10.0은 3가지 evidence 수집 경로와 Top-Down / Bottom-Up 구축 전략을 지원합니다.

---

## Evidence 수집 경로

| 경로 | 언제 | 스크립트 |
|------|------|---------|
| URL / 로컬 MD | 논문·문서·웹 페이지 수집 | `msm-evidence collect` |
| Graphify ETL | 코드베이스를 KB에 수집 | `graphify_to_msm.py` |
| 수동 작성 | 직접 `evidence/seeds.jsonl`에 추가 | — |

### Graphify ETL 흐름

코드베이스를 KB evidence로 수집할 때 씁니다. `file_type == "concept"` 노드만 통과시켜 시맨틱 추상화를 유지합니다.

```
graphify .
    ↓ Step 1–2: Tree-sitter AST + LLM 시맨틱 추출
graph.json (nodes: code + concept + document)
    ↓ graphify_to_msm.py (concept 필터 + god node 탐지)
evidence/graphify/entity_candidates.jsonl   ← concept 노드만
evidence/graphify/relation_candidates.jsonl ← concept 간 엣지
    ↓ msm-ontology add --apply
ontology/explain/concept/{cluster}/entities.jsonl      ← MECE 검증 후 승격
```

---

## 전략 선택 기준

| 조건 | 전략 |
|------|------|
| 도메인 구조가 선명하고 evidence 미수집 | **Top-Down** |
| 도메인 구조 불명확하고 evidence 이미 있음 | **Bottom-Up** |
| 코드베이스 구조를 KB로 수집 | **Graphify ETL** |

---

## Top-Down Flow

구조를 먼저 설계하고 evidence를 채웁니다.

```
msm init (explain/concept · explain/instance 골격)
    ↓
msm-ontology add (explain/concept (TBox) 클래스 정의)
    ↓
msm-evidence collect (URL/MD → seeds)
    ↓
msm-ontology add (explain/instance (ABox) 인스턴스 승격)
    ↓
msm-ontology mece (MECE 검증)
    ↓
status: draft → experimental → validated
```

---

## Bottom-Up Flow

evidence를 먼저 수집하고 구조를 귀납합니다.

```
msm-evidence collect (URL/MD → seeds)
    ↓
반복 등장 개념 추출
    ↓
msm-ontology add (explain/concept (TBox) 클래스 귀납 정의)
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

**Rule 2. 검증 깊이**

| 수준 | 대상 | `msm-ontology mece --depth` |
|------|------|--------------------------|
| light | 정착된 개념 | `light` — 구조 배치만 확인 |
| medium | 도메인 특화 claim | `medium` — evidence 2개 대조 |
| deep | 신규 synthesis | `deep` — 반박 가능성 포함 |

**Rule 3. 종료 조건**
재시도 1회 후 미달이면 status를 한 단계 낮춰 기록하고 종료합니다. 루프를 계속 돌리는 것보다 낮은 status로 기록하는 편이 효율적입니다.
