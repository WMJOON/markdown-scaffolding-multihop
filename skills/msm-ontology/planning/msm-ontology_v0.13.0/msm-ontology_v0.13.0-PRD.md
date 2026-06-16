---
title: msm-ontology v0.13.0 — LinkML OWL Reasoning Layer
type: PRD
skill: msm-ontology
version: v0.13.0
prev_version: v0.12.0
date: 2026-05-26
status: final
implementation_status: "type reclassification 경로(compile+owl_postprocess+abox-compile+axiom HITL+reason) = 구현·검증(gemma4 AC-2). property-value 추론(AC-3 inverseOf/AC-4 transitive)은 owlready2 한계로 미검증 — 후속."
addendum: msm-ontology_v0.13.0-owl-postprocess-and-ssot-adoption-PRD.md
author: WMJOON
tags: [msm-ontology, linkml, owl, reasoning, owlready2]
---

# msm-ontology v0.13.0 — LinkML OWL Reasoning Layer

> [!success] 구현 현황 (2026-06-02, A 작업)
> **검증 완료 (type reclassification 경로):**
> - ✅ **compile**(YAML→TTL) + **owl_postprocess**(FunctionalProperty/다국어 label, addendum).
> - ✅ **abox-compile**(ABox YAML→individual TTL, owl:NamedIndividual) + **reason**(owl/*.ttl 병합, owlready2 Turtle 미지원 → rdflib NTriples 변환). asserted/inferred-delta 구분 기록.
> - ✅ **AC-2 reclassification**: `gemma4:e4b` asserted=`TransformerMLMModel` → inferred=`MultimodalModel`(충분조건 GCI, `is_a` 추론). test_abox_reasoning.py T3 green.
> - ✅ **axiom(OWL HITL 저작)**: classification_rule preview(OWL+추론 consequence)→승인(`--apply`, ruamel 주석 보존).
> - ✅ **AC-5 explain** 신규 스키마 호환.
>
> **한정/미검증 (property-value 추론 — AC-3/AC-4):**
> - 🟡 **AC-3(inverseOf)/AC-4(transitive)는 견고히 검증되지 않음.** owlready2/Pellet은 type(`is_a`)은 추론을 채우지만 **property value(`prop[ind]`)는 post-reason에 안 돌려줌**(알려진 비대칭). inverse는 owlready2가 **load 시 auto-materialize**(reason 아님)하므로 inferred-delta로 잡히지 않음. owlgen은 inverseOf/TransitiveProperty 트리플은 정상 방출하나, 이를 inferred fact로 캡처하려면 reasoner-agnostic graph-diff(`world.as_rdflib_graph()` 비교)로 재설계 필요 → 후속.
> - reason은 property-delta 코드를 보유(explain 호환·비크래시)하나 실측상 `inferred_properties:{}`.
>
> 📐 **설계 원칙**: RDF/ABox=LLM 자동화, OWL/TBox=사람 HITL (core.md §7.5). owlgen `classification_rules`는 **충분조건 GCI**(≠ `owl:equivalentClass`) — 원 PRD §3의 `equals_expression`은 실제 LinkML 구문이 아니며 `classification_rules`로 대체.

## 1. 배경 (Why)

### 1.1 v0.12.0이 남긴 문제

v0.12.0은 entity/relation/instance를 JSONL에 등록하고 MECE를 강제한다.
그러나 두 가지 pain이 해결되지 않았다:

**관계 추적/관리 불가**
- relation은 JSONL의 source/target 쌍일 뿐 — inverse, transitive, subPropertyOf 없음
- `A hasSegment B`를 추가해도 `B isSegmentOf A`가 자동으로 생기지 않음
- 관계를 역방향·계층 방향으로 추적하려면 매번 수동 쿼리

**복잡한 class inference 불가**
- instance가 특정 property를 가지더라도 class 자동 분류 없음
- 예: `gemma4:e2b`가 `TransformerMLMModel`이고 `canBeUsedFor ImageGeneration`이면
  자동으로 `MultimodalModel`로 분류돼야 하지만, 현재는 수동 태깅 필요
- `SubClassOf`, `equivalentClass`, `someValuesFrom`, `disjointWith` 표현 불가

### 1.2 설계 원칙

1. **YAML = 작성 레이어**: 인간이 읽고 쓰는 형식. OWL/XML·Turtle은 컴파일 결과물
2. **LinkML = 브릿지**: YAML 스키마 → OWL 컴파일 + JSON Schema + SQL DDL 동시 생성
3. **owlready2 = 추론 엔진**: Python stdlib 수준으로 사용 가능한 OWL2 DL reasoner
4. **Obsidian 호환 유지**: 추론 결과를 기존 JSONL/MD projection으로 역주입 — Obsidian 레이어는 변경 없음
5. **기존 CLI 호환**: v0.12.0 add/mece/list/project CLI 그대로 유지, 신규 compile/reason 추가

---

## 2. 아키텍처

```
[작성]  ontology/definition/*.yaml  ← LinkML YAML (인간 작성)
              ↓  msm-ontology compile
[변환]  ontology/owl/*.ttl           ← Turtle (컴파일 결과, 직접 편집 금지)
              ↓  msm-ontology reason
[추론]  owlready2 reasoner           ← OWL2 DL inference
              ↓  msm-ontology materialize
[저장]  ontology/Abox/*.jsonl        ← 추론 결과 역주입 (기존 레이어)
              ↓  msm-ontology project (기존)
[출력]  ontology/Abox/*.md           ← Obsidian projection (변경 없음)
```

---

## 3. LinkML YAML 문법

### TBox — 클래스 정의

```yaml
classes:
  LanguageModel:
    abstract: true
    description: "언어 모델 기반 클래스"

  TransformerMLMModel:
    is_a: LanguageModel
    description: "Transformer 기반 MLM 모델"

  MultimodalModel:
    is_a: TransformerMLMModel
    description: "이미지 생성 등 멀티모달 태스크 가능 모델"
    equals_expression:           # OWL equivalentClass
      and:
        - is_a: TransformerMLMModel
        - some:
            canBeUsedFor: ImageGeneration
```

### TBox — 관계 정의

```yaml
slots:
  canBeUsedFor:
    domain: LanguageModel
    range: Task
    multivalued: true
    inverse: usedByModel         # owl:inverseOf → 자동 materialization

  hasSubModel:
    domain: LanguageModel
    range: LanguageModel
    transitive: true             # owl:TransitiveProperty
    subproperty_of: hasPart
```

### ABox — 인스턴스

```yaml
# ontology/Abox/models.yaml
instances:
  gemma4_e2b:
    instance_of: TransformerMLMModel
    canBeUsedFor:
      - ImageGeneration
    # → reason 후: instance_of에 MultimodalModel 자동 추가
```

---

## 4. 신규 CLI

| 명령 | 동작 |
|------|------|
| `msm-ontology compile --target REPO [--apply]` | YAML → Turtle 변환. `ontology/owl/` 에 생성 |
| `msm-ontology reason --target REPO [--apply]` | Turtle → owlready2 추론 → inferred facts JSONL 역주입 |
| `msm-ontology materialize --target REPO [--apply]` | compile + reason 연속 실행 |
| `msm-ontology explain --target REPO --instance ID` | 특정 instance에 대한 추론 근거 출력 |

기존 CLI (`add`, `mece`, `list`, `project`, `definition`, `contract-validate`, `eca-run`, `eca-schedule`, `gen-ddl`) 변경 없음.

> [!note] addendum 보강 (표현력 갭 + 경로)
> owlgen이 못 내는 `owl:FunctionalProperty`/다국어 `rdfs:label@lang`은 [[msm-ontology_v0.13.0-owl-postprocess-and-ssot-adoption-PRD]]가 추가하는 `postprocess` 서브명령(compile 기본 자동 적용, `--no-postprocess` off)으로 보강한다. compile/reason 출력 경로는 동 addendum에서 `--out-dir`/`--inferred-dir`로 인자화된다(기본값=현 경로 유지).

---

## 5. 구체 예시 — gemma4:e2b

**입력 (YAML 작성)**
```yaml
instances:
  gemma4_e2b:
    instance_of: TransformerMLMModel
    canBeUsedFor: [ImageGeneration]
```

**compile 결과 (Turtle, 자동 생성)**
```turtle
:gemma4_e2b a :TransformerMLMModel ;
    :canBeUsedFor :ImageGeneration .
```

**reason 결과 (owlready2 추론)**
```
:gemma4_e2b a :MultimodalModel .        # equivalentClass 조건 충족
:ImageGeneration :usedByModel :gemma4_e2b .  # inverseOf 자동 생성
```

**materialize 결과 (JSONL 역주입)**
```jsonl
{"id": "gemma4_e2b", "type": ["TransformerMLMModel", "MultimodalModel"], "canBeUsedFor": ["ImageGeneration"], "inferred": true}
```

---

## 6. 의존성 변경

| 항목 | v0.12.0 | v0.13.0 |
|------|---------|---------|
| 외부 패키지 | 없음 (stdlib만) | `linkml`, `owlready2` 추가 |
| Python | 3.10+ | 3.10+ (유지) |
| Obsidian 호환 | ✓ | ✓ (유지) |

설치:
```bash
pip install linkml owlready2
```

---

## 7. 마이그레이션 (v0.12.0 → v0.13.0)

1. 기존 `ontology/definition/*.yaml` 파일에 LinkML 헤더 추가 (하위 호환)
2. `msm-ontology compile --target REPO` 최초 1회 실행 → `ontology/owl/` 생성
3. 기존 JSONL/MD 변경 없음 — `reason`을 실행하지 않으면 추론 결과 역주입 안 됨

---

## 8. Non-Goals

- SPARQL endpoint 제공 → v0.14.0 후보
- 실시간 inference (변경 감지 + 자동 reason) → v0.15.0 후보
- OWL Full (규칙 기반 추론 복잡도 무제한) — OWL2 DL로 제한
- Protégé / 외부 OWL editor 직접 연동

---

## 9. 인수 조건 (AC)

| # | 조건 |
|---|------|
| AC-1 | `compile` 실행 시 LinkML YAML → valid Turtle 생성 |
| AC-2 | `reason` 실행 시 equivalentClass 조건 충족 instance에 inferred type 추가 |
| AC-3 | `reason` 실행 시 inverseOf 선언된 relation의 역방향 fact 자동 생성 |
| AC-4 | `reason` 실행 시 transitive property chain 계산 |
| AC-5 | `explain` 실행 시 추론 근거 (사용된 axiom) 출력 |
| AC-6 | 기존 v0.12.0 CLI (`add`, `mece`, `list`, `project`) 동작 변화 없음 |
| AC-7 | Obsidian MD projection 변경 없음 |
