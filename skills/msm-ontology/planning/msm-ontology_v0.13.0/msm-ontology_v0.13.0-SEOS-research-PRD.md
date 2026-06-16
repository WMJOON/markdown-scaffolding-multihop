---
title: SEOS — Self-Evolving Ontology System (Research PRD)
type: Research-PRD
skill: msm-ontology
version: v0.14.0
seos_research_version: v0.1
prev_version: v0.13.0
date: 2026-06-02
status: draft
author: WMJOON
tags: [msm-ontology, seos, rbox, ontology-evolution, governance, ontology-pr, property-chain, multihop, hitl, hootl]
---

> [!info] MSM Identity
> **MSM = Human-Agent KnowledgeBase Management System.**
> SEOS는 MSM을 한 단계 확장한다 — 관리 대상이 "KB의 내용(ABox)"을 넘어 **KB를 설명하는 언어(TBox/RBox) 자체**가 되고, 그 언어를 인간과 에이전트가 함께 진화시킨다.

# SEOS — Self-Evolving Ontology System

> [!abstract] 이 문서를 읽는 법 (scope)
> - **SEOS** = 연구 우산(research umbrella, `seos v0.1`). discovery·governance·harness 등 **여러 스킬을 가로지르는** 장기 비전.
> - **msm-ontology v0.14.0** = SEOS의 **첫 구현 증분**. 구체 대상은 **RBox 레이어 + Ontology-PR 형식화 + Role-Discovery proposal + 추론 캡처**.
> - 따라서 본 문서는 **Part A(비전)** 와 **Part B(v0.14.0에 실제로 짓는 것)** 로 나뉜다. 월요일에 코드를 시작한다면 곧장 **Part B(§11)** 로 가면 된다.

---

# Part A — SEOS Research Vision

## 1. Vision

현재 대부분의 Ontology System은 **정적 지식 모델(Static Knowledge Model)** 을 전제한다. Ontology Engineer가 TBox/RBox를 설계하고, 시스템은 변하는 ABox를 저장·추론한다.

Agent 시대에는 전제가 달라진다. Agent는 데이터를 소비하기만 하는 존재가 아니라 **지속적으로 관찰하고, 패턴을 발견하고, 새 개념·관계를 제안**할 수 있다. SEOS는 Agent와 Human이 협력해 **Ontology 자체를 진화**시키는 **Living World Model**을 목표로 한다.

## 2. 원칙 전환 — SEOS의 개념적 중심 (중요)

> [!important] v0.13.0의 원칙은 *유지*되지 않고 *수정*된다
> - **v0.13.0** (core.md §7.5, 2026-06-02 기록): *"도구는 OWL을 생성하지 않는다. 사람이 쓴 의도를 컴파일하거나 결과를 가시화 후 승인 시 병합할 뿐."* → **에이전트는 OWL을 제안하지 않는다.**
> - **SEOS** (H1/H2): **에이전트가 Concept(TBox)·Role(RBox) 후보를 제안(propose)한다.** 이는 적용이 아니라 **반전**이다.
> - **살아남는 불변식은 "비생성"이 아니라 "승인(approval)"이다.** 에이전트가 무엇을 제안하든, 모든 변경은 **거버넌스 레벨에 맞는 게이트**를 통과해야 정본이 된다.

이 화해를 구현하는 형식이 **Ontology Pull Request**다: **propose = agent / dispose = human(상위 레벨)**. v0.13.0에서 만든 `axiom`의 `preview→approve(--apply)→merge` 흐름이 이미 이 PR의 원형(proto-PR)이다 — SEOS는 거기에 **자동 propose(discovery)** 와 **레벨별 dispose(governance)** 를 더한다.

```
v0.13.0:  human ──author(LinkML)──▶ axiom preview ──human approve──▶ merge
SEOS:     agent ──discover/propose──▶ Ontology-PR ──gate(by level)──▶ merge | reject | revise
                                          (propose=agent, dispose=human@L0/L1)
```

## 3. Problem Statement

기존 Ontology 시스템의 암묵 가정:
- Concept(TBox)은 고정적이다.
- Role(RBox)은 고정적이다.
- 변하는 것은 Instance(ABox)뿐이다.

그러나 실제 세계는 **세계를 설명하는 언어 자체가 변한다**:
- 새 개념: Remote Worker, Creator Economy, AI Agent, Caregiver …
- 새 관계(Role): `delegatesTo`, `supervises`, `coReasonsWith`, `financiallySupports` …

기존 프레임워크는 이 진화를 체계적으로 다루지 못한다.

## 4. Grounding — SEOS가 올라설 MSM v0.13.0 자산 (증거 수준 명시)

SEOS는 greenfield가 아니다. 각 구성요소의 **현재 증거 수준**을 정직하게 라벨한다.

| SEOS 구성요소 | MSM 대응 | 증거 수준 |
|---|---|---|
| Ontology-PR (propose→dispose) | `axiom` preview→`--apply`→merge (ruamel 주석 보존) | ✅ **구현·검증** (v0.13.0, 이번 세션) |
| ABox 적재·추론 | `abox_compile` + `reason`(TBox+ABox 병합, inferred-delta) | ✅ **구현·검증** (gemma4:e4b 재분류) |
| TBox 저작(HITL) | `definition` YAML + `axiom classification-rule` | ✅ **구현·검증** |
| Governance L0–L3 | MSO **HITL/HITLFE/HOTL/HOOTL** 의사결정 taxonomy | 🟡 **명명된 개념(MSO)** — 코드 grep 결과 msm 측 강제 로직 없음 → **enforcement는 to-build** |
| Ontology Drift 지표 | `msm-maintain/oracle/maintain_drift_readiness` | 🟡 **구조 drift scaffold 존재**(orphan·projection·evidence coverage). SEOS **의미 drift(개념/역할 진화율)는 별개 → 확장 필요** |
| 변경 이력·결정 | `msm-work-memory`(user-decision, agent-decision) | ✅ 존재 (PR 기록 저장소로 활용) |
| 측정 인프라 | `msm-harness` 5-axis · oracle score | ✅ 존재 (survival/intervention 지표의 토대) |
| RBox(역할 공리) | 부분적·흩어짐(§11) | 🔴 **v0.14.0 핵심 갭** |

## 5. Research Questions

- **RQ1.** Agent는 새로운 Concept를 발견할 수 있는가?
- **RQ2.** Agent는 새로운 Role(RBox)을 발견할 수 있는가?
- **RQ3.** Ontology Evolution을 어떤 거버넌스 구조로 관리할 수 있는가?
- **RQ4.** Concept/Role Evolution을 정량 평가할 수 있는가?
- **RQ5.** HOOTL(Human-Out-Of-The-Loop) 수준의 Ontology Evolution이 가능한가? (그리고 *언제* 허용해야 하나?)

## 6. Core Hypotheses

- **H1.** 대규모 ABox observation → Pattern Discovery → **Concept 후보 생성**.
- **H2.** 그래프 패턴 분석(Relation Mining) → **Role 후보 생성**.
- **H3.** 모든 Ontology가 동일 Governance Level일 필요 없다 — 상위는 Human, 하위는 Agent 거버넌스.

## 7. Governance Hierarchy (L0–L3)

MSO의 **HITL/HITLFE/HOTL/HOOTL** taxonomy에 매핑한다. (현재는 명명된 개념 → SEOS가 **레벨별 게이트를 실제 강제**로 구현)

| Level | 레이어 | 예시 | Governance | 게이트(목표 구현) |
|---|---|---|---|---|
| **L0** | Foundational | Person, Event, Organization, Asset | **HITL** — 수동 승인 필수 | `axiom --apply`에 명시 인간 ack, PreToolUse hook 차단 |
| **L1** | Domain | Caregiver, Patient, FinancialObligation | **HITLFE** — 중대 변경만 인간 | impact ≥ threshold일 때만 인간 |
| **L2** | Operational | FamilySupportNetwork, CareBurden, RecoveryEpisode | **HOTL** — 사후 인간 검토 | 자동 merge + 검토 큐 적재 |
| **L3** | Emergent | Pattern_0001, Cluster_032, Temp Role Candidate | **HOOTL** — 인간 무개입 | §7.1 격리 규칙 적용 |

### 7.1 HOOTL(L3) 격리 — 안전 펜스

> [!warning] L3는 "결국 사람이 사라진다"가 아니다
> L3 emergent 개념·역할은 **provisional 네임스페이스/티어**에만 존재한다. 규칙:
> - 항상 **low-trust**(낮은 trust score)로 시작한다.
> - **L0–L1로 자동 승격 금지** — 상위 승격은 반드시 거버넌스 게이트(HITL/HITLFE)를 통과.
> - 추론·질의에서 provisional 표식을 달고 격리 가능해야 한다.
> SEOS의 자율성은 *하위 티어의 실험*이며, 정본(L0/L1)은 끝까지 인간 승인 아래 있다.

## 8. Architecture

### Semantic Layer (느리게 변함, 인간 거버넌스 비중↑)
- **TBox** — Concept Hierarchy, Taxonomy, Constraints → `definition` YAML + `axiom classification-rule`.
- **RBox** — Relation Hierarchy, Property Chains, Causal Relations → **§11 (v0.14.0 신규)**.

### Dynamic Layer (빠르게 변함, 자동화↑)
- **ABox** — Events, Observations, Evidence, Memories, Logs → `msm-evidence`(수집) + `abox_compile` + `reason`.

### Evolution Layer (신규 — SEOS의 본체)
| Agent | 책임 | MSM 결합점 |
|---|---|---|
| **Concept Discovery Agent** | Concept 후보 생성 / merge / split 탐지 | ABox observation → Ontology-PR(TBox) |
| **Role Discovery Agent** | Relation mining / property 일반화·특수화 | ABox graph → Ontology-PR(RBox) — §11과 직결 |
| **Governance Agent** | Trust scoring / 승인 추천 / Change-Impact 분석 | harness 측정 + work-memory |
| **Human Reviewer** | Merge / Promotion / Rejection | `axiom --apply` (L0/L1 게이트) |

## 9. Ontology Pull Request Model

GitHub PR에서 영감. **Agent가 PR을 만들고, 게이트가 dispose한다.**

```jsonc
// Ontology-PR record (work-memory에 저장 제안)
{
  "pr_id": "onto-pr-0001",
  "kind": "concept | role | classification_rule | property_chain | ...",
  "proposed_by": "role-discovery-agent",
  "target_level": "L1",
  "payload": { /* LinkML 스니펫 (axiom 도구가 생성) */ },
  "evidence": { "observations": 1283, "source_refs": ["evidence:seed:..."] },
  "confidence": 0.89,
  "impact": { "instances_affected": 42, "new_inferences": 17 },
  "decision": "approve | reject | request_revision",
  "decided_by": "human | governance-agent",
  "gate": "HITL"
}
```

- **propose**: discovery agent가 payload(LinkML) + evidence + confidence + impact 생성.
- **preview**: `axiom`이 컴파일된 OWL + 추론 consequence를 보여줌(이미 구현).
- **dispose**: target_level의 게이트가 결정(L0/L1=인간, L2=사후, L3=자동·격리).
- **기록**: 결정은 `msm-work-memory`(user-decision/agent-decision)에 영속.

## 10. Evaluation Metrics

| 지표 | 정의 | MSM 토대(증거 수준) |
|---|---|---|
| Semantic Stability | 승인된 개념이 시간이 지나도 유효하게 남는 비율 | harness/oracle (토대 ✅, SEOS 지표 to-build) |
| Concept Survival Rate | 승인 개념 ÷ 제안 개념 | PR 기록 집계 (to-build) |
| Role Survival Rate | 승인 역할 ÷ 제안 역할 | PR 기록 집계 (to-build) |
| Human Intervention Rate | 인간 결정 ÷ 전체 Ontology 변경 | work-memory 집계 (to-build) |
| Ontology Drift | 개념·역할 진화율(시간당) | maintain drift **구조** scaffold 존재 → **의미 drift로 확장** |

---

# Part B — v0.14.0 구현 증분: RBox (the Monday spine)

> Part A는 비전이다. **v0.14.0에 실제로 짓는 것은 RBox 레이어**다 — SEOS의 Role Discovery/진화가 올라설 토대이자, 사용자가 RBox 질문에서 도착한 지점이며, **하드 그라운딩(probe 검증)** 이 있는 유일한 부분이다.

## 11. RBox — Role/Property Axiom Layer

> [!important] 2026-06-12 amend — 구현 구조 확정
> 본 §11은 RBox 공리를 `definition.yaml` annotation으로 두는 **최소 변경**을 가정했으나,
> 구현 세션에서 **RBox를 구조적 1급(`ontology/Rbox/roles/{domain}.yaml` 전용 아티팩트)** 으로 확정했다.
> 파이프라인(owl_postprocess 확장 · `axiom property` · graph-diff 캡처)과 AC-R1~R5는 그대로 유효하며,
> 소스 위치·CLI·티어링·신규 AC(R6/R7)는 [[msm-ontology_v0.14.0-RBox-firstclass-SPEC]] 가 정본이다.
> 또한 "RBox=SKOS" 안은 기각(단일 OWL 층) — 근거는 SPEC §0 D-1.

### 11.1 현 상태 — owlgen 지원 경계 (probe 검증, 2026-06-02)

| RBox 공리 | LinkML metaslot | owlgen 방출 | 현재 처리 |
|---|---|---|---|
| inverseOf / Transitive / Symmetric | `inverse`/`transitive`/`symmetric` | ✅ | LinkML slot |
| **Functional / InverseFunctional** | (없음) | ❌ | `owl_postprocess`(annotation) — 부분 RBox |
| **subPropertyOf** | `subproperty_of` 있음 | **❌ owlgen 드롭** | **미처리** |
| **propertyChainAxiom** | **(metaslot 없음)** | ❌ | **미처리 — 완전 net-new** |

핵심: `owl_postprocess`는 사실상 이미 RBox의 일부(Functional)를 주입한다 → **owlgen이 드롭하는 나머지 RBox 공리의 자연스러운 집**이다.

### 11.2 v0.14.0 작업 항목

1. **`owl_postprocess` 확장 — owlgen 드롭 RBox 공리 주입**
   - `subproperty_of` carrier/annotation → `rdfs:subPropertyOf`.
   - `property_chain`(신규 annotation, 예: `property_chain: [locatedIn, partOf]`) → `owl:propertyChainAxiom`.
   - 기존 `owl_characteristic`(Functional/InverseFunctional)과 동일 패턴(TTL-only, idempotent).
2. **`axiom property` 서브명령 — RBox HITL 저작** (`axiom classification-rule`의 RBox 짝)
   - 특성(characteristic) / inverse / subproperty / **chain** 선언.
   - preview(컴파일된 RBox OWL) → `--show-inferences` → `--apply`(ruamel 주석 보존, owlgen 미지원분은 annotation으로 기록).
3. **graph-diff 추론 캡처 (AC-3/AC-4 미결 해소 + chain 검증 전제)**
   - 현 한계: owlready2 `prop[ind]`가 post-reason에 property value를 안 돌려줌(type `is_a`만 채움) → inverse/transitive/**chain** 추론이 `inferred.jsonl`에 안 잡힘.
   - 해법: reasoner-agnostic **graph-diff** — asserted 그래프(rdflib) vs reason 후 `world.as_rdflib_graph()` 차집합 → 추론된 property fact 캡처.
   - 이로써 **property chain = 멀티홉 추론**(프로젝트 이름 *multihop*의 핵심)을 `inferred.jsonl`에서 실측 검증.

### 11.3 v0.14.0 인수 조건 (AC)

| # | 조건 |
|---|------|
| AC-R1 | `owl_postprocess`가 `subproperty_of`→`rdfs:subPropertyOf`, `property_chain`→`owl:propertyChainAxiom` 주입 |
| AC-R2 | `axiom property`가 RBox 공리를 preview(OWL)→`--apply`(주석 보존) — TBox `classification-rule`과 동일 HITL 패턴 |
| AC-R3 | graph-diff 캡처로 inverse/transitive **property fact가 `inferred.jsonl`에 기록**(AC-3/AC-4 해소) |
| AC-R4 | **property chain 멀티홉**: `a R b`, `b S c` + `R∘S ⊑ T` → `a T c`가 `inferred.jsonl`에 |
| AC-R5 | 기존 v0.13.0 동작(type reclassification·owl_postprocess·capture) 불변 |

## 12. Scope & Phasing

- **v0.14.0 (즉시 구현 = Part B §11)**: RBox 저작(owl_postprocess 확장 + `axiom property`) + graph-diff 추론 캡처. **Role Discovery는 아직 사람이 `axiom property`로 작성** — 자동 propose는 다음 단계.
- **v0.15.0+ (SEOS 본체)**: Role/Concept Discovery Agent(자동 propose) → Ontology-PR 형식화 → Governance Agent(trust/impact) → L0–L3 게이트 강제.
- **연구 지평**: HOOTL(L3) emergent ontology, survival/drift 지표, Living World Model.

## 13. Non-Goals (v0.14.0)

- 자동 Concept/Role Discovery(에이전트 propose) — Part A 비전, v0.15.0+.
- L0–L3 게이트의 완전 강제 구현 — 본 PRD는 매핑까지.
- HOOTL 자율 진화 — 격리 규칙(§7.1)만 규정, 구현은 후속.
- owlgen 자체 패치 — 후처리 주입으로 우회(v0.13.0 패턴 유지).

## 14. Open Questions / Research Risks

1. **graph-diff의 노이즈**: `world.as_rdflib_graph()` 차집합에 owlready2 내부/공리 트리플이 섞일 수 있음 — ABox individual 대상 property fact만 필터하는 기준 필요.
2. **Impact 분석 비용**: 모든 PR마다 추론 consequence 계산(Pellet)은 비쌈 — preview 계층화(§axiom) 원칙 유지, L2/L3 배치화.
3. **Trust score 정의**(RQ4): confidence·evidence count·survival 이력을 어떻게 단일 trust로 합성?
4. **Concept merge/split**(H1): 동의어·상하위 판정은 임베딩 유사도 + 인간 확인 — 오탐 시 정본 오염 위험(→ L0/L1 게이트 필수).
5. **HOOTL 허용 경계**(RQ5): provisional 티어가 정본을 오염시키지 않는다는 보장을 어떻게 형식 검증?

## 15. Long-Term Goal

```
Static Ontology  →  Adaptive Ontology  →  Self-Evolving Ontology  →  Living World Model
```

Agent와 Human이 협력해 현실을 지속적으로 모델링·갱신하는 **Living World Model Infrastructure**. SEOS는 그 경로의 거버넌스·진화·평가 골격을 규정한다.

---

## 16. References

- 직전 버전: [[msm-ontology_v0.13.0-PRD]] (LinkML OWL reasoning), [[msm-ontology_v0.13.0-owl-postprocess-and-ssot-adoption-PRD]] (postprocess+경로).
- 이번 세션 구현(검증): `abox_compile.py`, `axiom.py`(classification-rule), `reason.py`(병합+inferred-delta), `tests/test_abox_reasoning.py`.
- RBox probe: owlgen이 inverse/transitive/symmetric 방출, subPropertyOf/Functional 드롭, property-chain metaslot 없음(2026-06-02).
- 설계 원칙(수정 대상): `msm-ontology/references/core.md` §7.5 (RDF=LLM / OWL=HITL).
- 거버넌스 taxonomy: MSO `mso-workflow-design` (HITL/HITLFE/HOTL/HOOTL).
- 사용자 SEOS 초안(2026-06-02): 본 PRD Part A의 vision spine.
