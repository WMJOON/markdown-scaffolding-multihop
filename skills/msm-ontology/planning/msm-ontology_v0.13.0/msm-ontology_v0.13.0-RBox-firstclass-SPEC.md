---
title: RBox First-Class Layer — Implementation SPEC
type: SPEC
skill: msm-ontology
version: v0.14.0
parent_prd: msm-ontology_v0.14.0-SEOS-research-PRD (Part B §11)
prev_version: v0.13.0
date: 2026-06-12
status: draft
author: WMJOON
tags: [msm-ontology, rbox, role-box, owl, property-chain, graph-diff, hitl, multihop]
---

> [!info] 이 문서의 위치
> 본 SPEC은 [[msm-ontology_v0.14.0-SEOS-research-PRD]] **Part B §11(RBox)** 의 **구현 명세**다.
> PRD는 RBox를 AC-R1~R5까지 규정했으나 **0% 구현 상태**로 남아 있었다(검증: 2026-06-12,
> `axiom.py`=classification-rule만 / `owl_postprocess.py`=owl_characteristic만 / `reason.py`=graph-diff 부재).
> 본 SPEC은 그 구현을 재개하되, **2026-06-12 설계 세션에서 확정된 구조 결정**(아래 §0)을 §11에 amend한다.

---

# RBox First-Class Layer — SPEC

## 0. 2026-06-12 설계 결정 (Decision Record)

세션에서 RBox 표현을 두고 세 갈래를 검토했고, 다음으로 확정한다.

### D-1 — SKOS 기각, 단일 OWL role 층
- **검토안**: "OWL은 TBox, RBox는 SKOS"(사용자 초기 직관).
- **기각 사유**: SKOS는 concept scheme(시소러스)용이며 **추론 의미론을 의도적으로 안 가진다**
  (`skos:broader`조차 비-transitive). RBox 공리(propertyChain / Transitive / inverseOf / subPropertyOf)는
  바로 그 추론을 표현하는 층이라 SKOS로는 **표현 불가**. 또한 OWL이 이미 들어가는 이상,
  술어 통제어휘(목록·label·정의·동의어·계층)는 `owl:ObjectProperty` + `rdfs:label`/`rdfs:comment`/
  `rdfs:subPropertyOf` + à-la-carte `skos:altLabel` annotation으로 충분히 표현된다.
  SKOS 별도 층은 **두 번째 표현 + 매핑 동기화 부담**만 추가(심플화 아님).
- **결론**: RBox = **단일 OWL 층**. 티어링은 *파일 분리*가 아니라 **공리 무게**로 한다
  (선언=LLM 제안 / 공리=HITL). 이는 PRD가 SKOS를 쓰지 않은 것과 이미 일치한다.
- **회수 가능성**: 미래에 시소러스 interop 필요 시 OWL→SKOS **단방향 projection** 생성기로 회수(YAGNI, 락인 없음).

### D-2 — RBox는 구조적 1급 (`Rbox/roles/{domain}.yaml`)
- **검토안 A(PRD 원안)**: 공리를 `definition.yaml`(TBox) 안의 annotation으로 — 최소 변경.
- **검토안 B(채택)**: `ontology/Rbox/roles/{domain}.yaml` **전용 아티팩트**.
- **채택 사유**: 사용자 의도가 "RBox를 **공식적으로** 추가"였다. role 선언+공리가 TBox 파일 안 annotation으로
  묻히면 구조적 1급이 아니다. 전용 파일이 LLM-제안/HITL-공리 **write-path 게이트**의 자연스러운 대상이 된다.
- **불변 사항**: 두 안 모두 **AC-R1~R5를 동일하게 만족**한다. owl_postprocess 확장 / `axiom property` /
  graph-diff 캡처 **파이프라인은 공통**. 달라지는 건 *소스가 어디 사는가*뿐.

### D-3 — 버전 = v0.14.0 (신규 v0.15.0 아님)
- RBox는 v0.14.0 PRD Part B의 미착수분이다. v0.15.0은 PRD §12에서 **SEOS 자동 Discovery Agent
  (auto-propose)** 로 이미 예약됨. 따라서 본 작업은 v0.14.0 RBox **구현 완료**이지 새 버전이 아니다.

---

## 1. 아티팩트 레이아웃

```
ontology/
  Tbox/{cluster}/          classes (entities) — 기존, 불변
  Rbox/                    ← NEW (1급)
    roles/{domain}.yaml         LinkML role schema (단일 정본)
    md/{snake_label}.md         role projection (선택, 후속)
  Abox/{cluster}/          instances — 기존, 불변
  owl/
    {domain}.ttl                TBox (기존)
    {domain}.rbox.ttl      ← NEW  RBox compiled
    {domain}.abox.ttl           ABox (기존)
```

### 1.1 `Rbox/roles/{domain}.yaml` 스키마 (LinkML)

```yaml
id: https://msm/rbox/{domain}
name: {domain}-rbox
prefixes: { ex: "https://msm/{domain}/" }
default_prefix: ex

slots:
  uses:
    # ── 선언부 (LLM/evidence 제안, status=draft 로 진입) ──
    description: "주체가 대상을 사용한다"          # → rdfs:comment
    aliases: [utilizes, employs]                  # → skos:altLabel (postprocess)
    status: accepted                              # draft | accepted | stable | deprecated
    source_refs: [evidence:seed:...]              # 선언도 evidence 강제 (add 와 동일)
    # ── 공리부 (HITL, axiom property 로만 주입) ──
    # owl_characteristic: TransitiveProperty
    # subproperty_of: depends_on
    # property_chain: [uses, requires]            # uses ∘ requires ⊑ depends_on
    # domain: Agent
    # range: Tool
```

> [!note] 선언/공리 경계 = write-path 게이트 (D-1 티어링 구현)
> - `rbox add-relation` → **선언부만** 생성(`status: draft`, 공리 키 없음). **추론 0 → 안전 → LLM 허용**.
> - `axiom property` → 기존 role 위에 **공리부 주입**(`--apply` HITL). blast-radius 큰 부분만 사람이.
> - 동일 패턴이 TBox에 이미 있음: `add`(선언) vs `axiom classification-rule`(공리).

---

## 2. CLI 표면

```
# 선언 (LLM/evidence — 추론 0)
msm-ontology rbox add-relation --target REPO --domain D --label L
    [--alt SYNONYM ...] [--description TEXT] --evidence URI [...]
    [--status draft|accepted] [--apply]
msm-ontology rbox list      --target REPO --domain D [--status S]

# 공리 (HITL — preview → --show-inferences → --apply)
msm-ontology axiom property --target REPO --domain D --role R
    [--characteristic Transitive|Symmetric|Functional|InverseFunctional|...]
    [--inverse R2] [--subproperty-of R2] [--chain R_a R_b ...]
    [--domain CLASS] [--range CLASS]
    [--show-inferences] [--apply]

# 컴파일 / 추론 (확장)
msm-ontology rbox compile   --target REPO [--domain D] [--apply]   # roles/*.yaml → {domain}.rbox.ttl (+postprocess)
msm-ontology rbox validate  --target REPO --domain D               # roles ↔ Abox 사용 술어 정합
msm-ontology materialize    --target REPO [...]                    # compile + rbox-compile + abox-compile + reason
```

---

## 3. 파이프라인 변경 (AC-R1~R5 매핑)

| AC | 변경 파일 | 내용 |
|----|----------|------|
| **AC-R1** | `owl_postprocess.py` | owlgen 드롭분 주입 확장: `subproperty_of`→`rdfs:subPropertyOf`, `property_chain`→`owl:propertyChainAxiom`. 기존 `owl_characteristic` 패턴(TTL-only·idempotent) 재사용 |
| **AC-R2** | `axiom.py` | `cmd_property` 신설 — `classification-rule`의 RBox 짝. ruamel 라운드트립 주석 보존, owlgen 미지원분은 annotation 기록 |
| **AC-R3** | `reason.py` | `_prop_map`(owlready2 `prop[ind]`) → **`world.as_rdflib_graph()` 전/후 트리플 diff**(reasoner-agnostic)로 교체. inverse/transitive property fact가 `inferred.jsonl`에 기록 |
| **AC-R4** | `reason.py` + fixture | property chain 멀티홉: `a R b`, `b S c` + `R∘S ⊑ T` → `a T c`가 `inferred.jsonl`에 (multihop 실측) |
| **AC-R5** | (회귀) | v0.13.0 동작(type reclassification·owl_postprocess characteristic·capture) 불변 |
| **AC-R6** (신규, D-2) | `add.py`/신규 `rbox.py`, `compile.py` | `Rbox/roles/{domain}.yaml` 1급 아티팩트 + `rbox compile`→`{domain}.rbox.ttl` 전용 경로 |
| **AC-R7** (신규, D-1) | `rbox.py` validate | role 선언 게이트: Abox에서 쓰는 모든 술어가 `roles/`에 `accepted`로 존재 |

### 3.1 graph-diff 캡처 상세 (AC-R3/R4 — 핵심)

```
pre  = world.as_rdflib_graph()  복제          # reason 전 트리플 집합
sync_reasoner(infer_property_values=True)
post = world.as_rdflib_graph()                # reason 후
gained = post - pre                            # rdflib 차집합
# 필터: subject 가 Abox NamedIndividual 이고 predicate 가 ObjectProperty 인 트리플만
#       (owlready2 내부/공리 트리플 노이즈 제거 — PRD §14 Open Q1)
inferred_properties[ind] = gained 중 해당 individual 대상 fact
```

> [!warning] 노이즈 필터 (PRD §14 Open Question 1)
> `as_rdflib_graph()` 차집합엔 owlready2 내부·TBox 공리 트리플이 섞인다.
> **Abox individual subject + ObjectProperty predicate** 화이트리스트로 한정해 fact만 추출.

---

## 4. 구현 위험 (implementation risk)

> [!success] Probe 결과 (2026-06-12, linkml owlgen + rdflib, `/tmp/msm-rbox-probe/`)
> 위험 #1·#2 **둘 다 PASS** → P1 설계 unblocked.

1. **cross-schema 참조** — ✅ **PASS(probe1)**. TBox schema가 `imports: demo-rbox` 로 별도 rbox 스키마의
   `uses` slot을 해결. TBox 컴파일 산출 TTL에서 `ex:uses a owl:ObjectProperty` + `classification_rules`의
   restriction(`uses someValuesFrom Tool`)이 정상 방출. → **definition.yaml에 `imports: {domain}-rbox` 추가**가
   P1 구현 계약.
2. **owlgen standalone slot** — ✅ **PASS(probe2)**. 어떤 class에도 `slot_usage`로 부착 안 한 standalone slot도
   `range`가 클래스면 `owl:ObjectProperty` 방출. `transitive: true` → `owl:TransitiveProperty`까지 방출.
   - 주의(구현 계약): `range` 미지정 slot(`bare_slot`)도 ObjectProperty로 나왔으나(default_range:string 무시),
     **RBox role은 항상 `range: <class>` 명시**해 거동 고정. slot은 `linkml:SlotDefinition` rdf:type도 함께
     달리므로(메타 노이즈), graph-diff 필터·projection이 이를 무시해야 함.
3. **graph-diff 노이즈 규모** — ⏳ P3에서 검증. 필터 화이트리스트(Abox individual subject + ObjectProperty
   predicate)가 과도하면 chain fact 누락, 느슨하면 공리/`SlotDefinition` 트리플 혼입. fixture로 양방 테스트.

> [!warning] 환경 부채 (P1 착수 전 선결)
> repository-test의 `skills/msm-ontology/.venv`는 **베이스 인터프리터(Python 3.10.8 framework) 소실로 깨짐**
> (시스템은 3.13). linkml/owlready2 미설치. probe는 `/tmp/msm-probe-venv`(uv, py3.11)로 우회 검증했으나,
> P1에서 실제 skill 테스트(`pytest`)를 돌리려면 **canonical venv 재건**(`uv venv` + `pip install linkml
> owlready2 rdflib ruamel.yaml pyshacl`)이 선행 필요. linkml 1.10.0 deprecation 경고 다수(무해, owlgen
> 기본값 변경 예고) — 후속 추적.

---

## 5. Phasing (repository-test, 기존 TDD 컨벤션)

| Phase | 산출물 | 게이트 | 상태 |
|-------|--------|--------|------|
| **P0** | 본 SPEC (결정 박제 + §11 amend) | — | ✅ done |
| **P1** | `Rbox/roles/` 1급 + `rbox add-relation/list/compile`→`.rbox.ttl` + 테스트. 위험 #1·#2 probe | AC-R6, compile probe PASS | ✅ **done (2026-06-12)** |
| **P2** | `owl_postprocess` 확장(subPropertyOf/propertyChain) + `axiom property` HITL + reason이 rbox.ttl 병합 + 테스트 | AC-R1, AC-R2 | ✅ **done (2026-06-12)** |
| **P3** | `reason.py` graph-diff 교체 + chain 멀티홉 AC fixture + 테스트 | AC-R3, AC-R4 (multihop 실측) | ✅ **done (2026-06-12)** |
| **P4** | `rbox validate` 게이트 + MECE 확장 + `SKILL.md`/`core.md` §7.6 문서 + 회귀 | AC-R5, AC-R7 | ✅ **done (2026-06-12)** |

> [!success] P4 완료 + v0.14.0 RBox 전체 완료 (2026-06-12)
> - **`rbox validate`(AC-R7)**: G1 Abox 술어↔roles 선언 게이트, G2 status(draft 경고), G3 role MECE(label 중복/alias 충돌). violation≥1 → exit 1.
> - **문서**: `SKILL.md`(rbox/axiom property CLI + 책임/의존성), `core.md`(§7.3 경고 **해소됨**으로 갱신 + §8 RBox 절 신설), `requirements.txt`(owlready2/ruamel 명시).
> - **최종 회귀**: 6종 전부 PASS — test_owl_postprocess / test_abox_reasoning / test_rbox(P1) / test_rbox_axiom(P2) / test_rbox_reason(P3) / test_rbox_validate(P4).
> - **AC 전수 충족**: R1(postprocess 확장) R2(axiom property) R3(inverse/transitive 캡처) R4(chain 멀티홉) R5(회귀 불변) R6(1급 ObjectProperty) R7(validate 게이트).
> - **통합 테스트(advisor 검증 #2)**: `tests/test_rbox_integration.py` — 실제 파이프라인(definition+roles+Abox YAML → materialize
>   = compile+rbox-compile+**abox-compile**+reason)으로 `agent1 depends_on runtime1` chain 멀티홉 inferred. 단위 테스트의 hand-ttl 가정(NamedIndividual 타이핑·ns)을 실제 abox-compile 산출로 실측 검증. **최종 회귀 7종 PASS.**
>
> > [!warning] 채널 주의 (거버넌스, 2026-06-12 발견)
> > `repository-test/skills/msm-ontology` 는 `../../repository/skills/msm-ontology` 로의 **symlink** 다.
> > 즉 본 세션의 모든 코드 편집은 **active `repository/` 채널에 직접 반영**됐다(격리 test 채널 아님).
> > AGENTS.md "검증 없이 release 채널로 승격 금지" 관점에서, 본 작업은 work 채널(repository)에서 검증 완료된 상태이며
> > release 채널 승격은 별도 게이트. (test 채널 격리를 원하면 symlink 해제 후 분리 필요 — 사용자 판단.)

> [!success] P3 완료 기록 (2026-06-12) — §7.3 3년 한계 해소, probe-first
> - **결정 probe(probe3)**: chain 시나리오(`a uses b`, `b requires c` + `uses∘requires⊑depends_on`)를
>   reason.py 실제 코드패스로 돌려 2 reasoner 측정. 결과: **Pellet·owlrl 둘 다 `a depends_on c` 추론**,
>   Pellet 의 **`as_rdflib_graph`(quadstore)에는 chain fact 가 실재**(§7.3 비관론은 `prop[ind]` 객체모델 한정).
> - **결정(advisor 트리)**: Pellet 단일 reasoner 채택 — 이미 reason.py 에 있어 **새 의존성 0**. owlrl 미도입.
> - **graph-diff 설계**: pre = **raw asserted 병합 그래프**(정적, inverse load-time 도 gained 로 포착),
>   post = reason 후 `world.as_rdflib_graph()` 정적 스냅샷. gained = (post − raw) 중 **(s∈Ind ∧ p∈ObjProp ∧ o∈Ind)** 필터.
>   probe 실측: 필터 후 gained 정확히 1개(`a depends_on c`), **asserted fact 누수 0**(owlready2 가 IRI 동일 보존 → 상쇄).
> - **surgical cut(AC-R5)**: type 재분류는 `_type_names` 객체모델 diff 그대로(견고), **property 경로만** graph-diff 로 교체.
>   `_merge_ttls_to_nt` → `_merge_ttls_to_graph`+`_graph_to_nt` 분리(raw 그래프 재사용). `_prop_map`/`_snapshot` 폐기.
> - 신규 `tests/test_rbox_reason.py`: chain 멀티홉(AC-R4)·transitive·inverse(AC-R3)가 `inferred.jsonl`에 기록 + 누수 0. PASS.
> - **회귀**: 5종 전부 PASS — 특히 `test_abox_reasoning`(type 재분류) 불변 확인.
> - TODO(P4): core.md §7.3 의 "inferred_properties 실측상 비어 있음" 경고를 **해소됨**으로 갱신.

> [!success] P2 완료 기록 (2026-06-12) — advisor 검토 반영
> - **owl_postprocess 확장(AC-R1)**: `subproperty_of`→`rdfs:subPropertyOf`, `inverse_of`→`owl:inverseOf`,
>   `property_chain`(콤마 문자열)→`owl:propertyChainAxiom`(순서 보존 RDF list). 타깃 IRI 는 subject 네임스페이스로 해석.
> - **`axiom property`(AC-R2)**: `classification-rule` 의 RBox 짝. 타깃 = `Rbox/roles/{domain}.yaml`.
>   `--characteristic/--inverse/--subproperty-of/--chain/--domain-class/--range`. preview(owlgen+postprocess)→`--apply`(ruamel 주석 보존).
> - **저작 경로 단일화**(advisor Q1): 모든 RBox 공리를 **annotation 단일 경로**로 (owlgen native 안 씀 → split-brain·double-emit 회피). `rbox list` 도 annotation-only 스캔으로 통일.
> - **D-1 게이트**: 공리 부착 전 role 선언 필수 + `--inverse/--subproperty-of/--chain` 타깃도 선언된 role 이어야 (미선언 시 authoring-time fail-loud).
> - **chain 순서·멱등성**(advisor Q2): 단일 콤마-리터럴로 순서 보존(R∘S≠S∘R). 멱등성은 carrier-제거 설계로 보장
>   (`if triple not in g` 는 blank-node list 에 무력 → 전용 멱등성 테스트로 검증). `--keep-carriers`+chain 은 double-emit 주의.
> - **materialize 배선**(advisor Blind #1): `step 1b: rbox-compile` 삽입 → reason 의 `owl/*.ttl` 병합에 RBox 공리 진입.
>   부수: TBox compile 단계를 **조건부(definition 있을 때만)** 로 — RBox-only/ABox-only KB 의 비대칭 hard-abort 제거.
> - **인수 = TTL 트리플 레벨**(advisor Blind #2): `axiom property --show-inferences` 는 P2 에서 type-consequence 만
>   (property round-trip 은 P3 graph-diff 전까지 비동작 — core.md §7.3). 경고 메시지로 명시.
> - 신규 `tests/test_rbox_axiom.py`(A1~A7 PASS). **회귀**: test_owl_postprocess/test_abox_reasoning/test_rbox 전부 여전히 PASS (AC-R5).

> [!success] P1 완료 기록 (2026-06-12)
> - 신규 `scripts/rbox.py`(add-relation/list/compile) + 디스패처 배선 + `tests/test_rbox.py`(전 항목 PASS).
> - role 정본 = `ontology/Rbox/roles/{domain}.yaml`(LinkML, ruamel 라운드트립). 선언만(추론 0), `--evidence` 강제, 중복 거부.
> - **네임스페이스 정렬**: role IRI 가 도메인 TBox 의 `ex` prefix(`definition/{domain}.yaml`)를 재사용 → reason 병합 전제 충족. 없으면 `https://example.org/msm/{domain}/` 컨벤션.
> - **보너스(D-1 실증)**: owlgen 이 LinkML `aliases`→`skos:altLabel`, `description`→`skos:definition` 자동 방출.
>   "SKOS 별도 층 없이 skos 용어를 annotation 으로 à-la-carte 차용" 설계가 **추가 코드 없이** TTL 에 실현됨.
> - **회귀(AC-R5)**: `test_owl_postprocess`/`test_abox_reasoning` 둘 다 여전히 PASS.
> - 환경 부채 해소: 깨진 `.venv` 재건(uv, py3.11, linkml+owlready2+rdflib+ruamel+pyshacl).

검증 AC 예시(P3): `agent uses tool`, `tool requires runtime` + `uses ∘ requires ⊑ dependsOn`
→ `agent dependsOn runtime`이 `inferred.jsonl`에 gained property로 기록.

---

## 6. Non-Goals
- 자동 Role Discovery(에이전트 propose) — PRD §13, v0.15.0+.
- OWL→SKOS projection 생성기 — D-1 회수 경로, 필요 시점에.
- role md projection 완성 — P1은 슬롯만, md는 후속.

## 7. References
- 부모: [[msm-ontology_v0.14.0-SEOS-research-PRD]] Part B §11, AC-R1~R5, §14 Open Questions.
- 설계 원칙(수정 대상): `repository-test/skills/msm-ontology/references/core.md` §7.3(graph-diff 미결), §7.5(RDF=LLM/OWL=HITL).
- 구현 기준: `axiom.py`(classification-rule 패턴), `owl_postprocess.py`(characteristic 패턴), `reason.py`(merge+inferred-delta).
