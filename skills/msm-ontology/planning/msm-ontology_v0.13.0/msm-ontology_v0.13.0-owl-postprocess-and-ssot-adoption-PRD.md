---
title: msm-ontology v0.13.0 — LinkML-as-SSOT 실전 검증 & 표현력 갭 보강 (owl_postprocess)
type: PRD
skill: msm-ontology
version: v0.13.0
prev_version: v0.13.0
addendum_to: msm-ontology_v0.13.0-PRD.md
date: 2026-06-02
status: final
decisions_resolved: 2026-06-02
author: WMJOON
tags: [msm-ontology, linkml, owl, owlgen, postprocess, ssot, functional-property, multilingual-label]
validated_in: my-knowledge-base (enterprise-workflow 파일럿)
---

# msm-ontology v0.13.0 — LinkML-as-SSOT 실전 검증 & 표현력 갭 보강

> [!note] 위치
> 본 문서는 [[msm-ontology_v0.13.0-PRD]]의 **addendum(실전 검증 + 갭 보강)**이다. v0.13.0이 도입한 LinkML compile/reason 레이어를 실제 KB(my-knowledge-base)에 적용해 검증하면서 드러난, 원 PRD가 다루지 않은 3가지 갭과 그 해결책을 규정한다.

## 1. 배경 (Why)

### 1.1 v0.13.0이 선언한 것 — 이미 LinkML-as-SSOT

원 PRD §1.2 설계원칙은 정확히 **"형식 정의를 단일 정본으로, 실행/저장 형태는 컴파일 산출물로"** 라는 정통 패턴을 선언했다:

> "YAML = 작성 레이어 (인간이 읽고 쓰는 형식). OWL/Turtle은 컴파일 결과물."

이 방향 자체는 타당하다(아래 §2에서 무손실 입증). 문제는 **선언과 실제 구현/배선 사이의 갭**이다.

### 1.2 실전 적용에서 드러난 3가지 갭 (원 PRD 미수록)

my-knowledge-base에 v0.13.0 compile.py를 실제로 돌려 손-작성 OWL과 대조한 결과:

**갭 A — owlgen 표현력 한계 (가장 중요)**
`linkml.generators.owlgen.OwlSchemaGenerator`는 다음을 생성하지 못한다(소스 직접 확인):
- `owl:FunctionalProperty` — owlgen의 relationship characteristics dict(`symmetric`/`asymmetric`/`transitive`/`reflexive`/`irreflexive`)에 **functional 없음**. LinkML `SlotDefinition`에도 functional 메타슬롯 없음(cardinality/multivalued만 존재).
- `rdfs:label "..."@ko` — owlgen은 **단일 언어 label만** 생성. 다국어 라벨 미지원.
- ⇒ 손-작성 OWL을 LinkML로 옮기면 위 두 종류가 **소실**된다.

**갭 B — 경로 불일치**
원 PRD §2 아키텍처와 실제 스크립트 출력 경로가 어긋난다:

| 단계 | 스크립트 실제 출력 | canonical/파이프라인 기대 |
|---|---|---|
| compile | `ontology/owl/{domain}.ttl` | `ontology/system/semantic/{cluster}/{domain}.ttl` |
| reason | `ontology/Abox/_inferred/inferred.jsonl` | `ontology/system/semantic/{cluster}/inferred.jsonl` |
| add | `ontology/Tbox/{cluster}/entities.jsonl` | `ontology/system/semantic/{cluster}/` (v0.12 이전 완료) |

**갭 C — 기존 데이터 세대 충돌**
- 현 KB의 `entities.jsonl`은 구세대 `yaml_to_jsonl.py`(graph-ontology.yaml 기반)가 생성 — 스키마 `entity_id`/`extra.node_id`/`label_en`.
- `add.py`(v0.11.0) 스키마는 `id`/`label`/`kind`/`md_path` — **서로 다름**.
- compile.py는 LinkML→OWL/TTL만 하고 **LinkML→jsonl 생성기가 없음** → jsonl이 독립 source로 남아 정본 모호(dual-SoT).

---

## 2. 실증 — enterprise-workflow 파일럿 (무손실 입증)

손-작성 `enterprise-workflow.classes.ttl`(18 클래스 + 11 property + cross-ontology 매핑)을 LinkML 정본으로 옮긴 뒤 compile + 후처리 → 원본과 rdflib 의미 대조.

| 항목 | 손-TTL | LinkML(compile) | LinkML+후처리 |
|---|---|---|---|
| owl:Class | 19 | 19 ✅ | 19 ✅ |
| rdfs:subClassOf | 11 | 11 ✅ | 11 ✅ |
| ObjectProperty | 10 | 10 ✅ | 10 ✅ |
| SymmetricProperty | 1 | 1 ✅ | 1 ✅ |
| skos:closeMatch (cross-ontology) | 8 | 8 ✅ | 8 ✅ |
| domain / range | 7 / 10 | 7 / 10 ✅ | 7 / 10 ✅ |
| **owl:FunctionalProperty** | 2 | **0** 🔴 | **2** ✅ |
| **rdfs:label @ko** | 19 | **0** 🔴 | **19** ✅ |
| **손실 총계** | — | **21** | **0** ✅ |

**결론**: 논리 골격(클래스·계층·property·domain/range·cross-ontology 매핑)은 owlgen이 완벽 재현. 갭 A의 2종(FunctionalProperty·다국어 label)만 후처리로 보강하면 **손-작성 OWL을 LinkML 정본이 무손실 대체**한다.

---

## 3. 제안 변경

### 3.1 owl_postprocess — 표현력 갭 보강 레이어 (신규)

owlgen이 못 내는 OWL 트리플을, LinkML 정본의 `annotations`에 SSOT로 보존했다가 compile 산출 TTL에 주입한다.

**LinkML 정본 (작성)**
```yaml
classes:
  Draft:
    is_a: WorkflowState
    annotations: { label_ko: 초안 }          # → 후처리가 rdfs:label "초안"@ko 주입
slots:
  fromState:
    domain: StateTransition
    range: WorkflowState
    annotations: { owl_characteristic: FunctionalProperty }  # → owl:FunctionalProperty 주입
```

**후처리 동작**
- `class.annotations.label_ko` → `{class} rdfs:label "..."@ko`
- `slot.annotations.owl_characteristic: {Functional|InverseFunctional|...}Property` → `{prop} a owl:...Property`

**배선 — (a) 채택 (§3.4-1 결정)**
- ✅ **(a) 플러그인 `msm-ontology`에 `postprocess` 서브명령으로 정식 편입 + compile 기본 자동 적용** (`--no-postprocess`로 비활성). `materialize`는 compile 경유로 자동 상속.
- ~~(b) materialize 단계에만 포함~~ → (a)가 compile/materialize 양쪽을 덮으므로 상위 호환.
- ~~(c) consumer repo의 vault-local 스크립트~~ → 파일럿 검증용이었고 표준 아님(§3.4 note: 도구 우선).

> [!note] AC-7 정합 (additive 보증)
> postprocess는 owlgen base TTL을 **변경하지 않고 트리플을 추가만** 한다. `--no-postprocess` 시 산출물은 v0.13.0과 **트리플 동일**(AC-A3). 따라서 "compile 동작 변화 없음"은 "base 출력 불변 + postprocess는 가산"으로 재정의된다(§6 AC-7).

### 3.2 경로 정합 (갭 B) — (a) 채택 (§3.4-2 결정)

compile/reason 출력 경로를 **`--out-dir` 인자화**한다.

- ✅ **(a) `--out-dir`/`--inferred-dir` 인자화.** 기본값은 현 경로(`ontology/owl/`, `ontology/Abox/_inferred/`) 유지 → 인자 미지정 시 v0.13.0과 동일(AC-7 backward-compat). 인자 지정 시 canonical 위치로 배치.
- ~~(b) 2단계 projection (compile→owl/ 후 이동)~~ → 이동 단계가 추가 실패면. 기각.

> [!warning] `system/semantic/` 하드코딩 금지
> addendum이 인용한 `system/semantic/`는 **consumer KB(my-knowledge-base)의 컨벤션**이다. **이 플러그인 자신의 `templates/canonical_root_hub.yaml`은 `ontology/Tbox/`를 선언**한다 — 컨벤션이 repo마다 다르다. 따라서 `system/semantic/`를 기본값으로 박으면 플러그인 자체 템플릿이 깨진다. 자동 배치가 필요하면 `canonical_root_hub.yaml`이 **선언한** 경로를 읽어 따른다(리터럴 금지). 기본 동작은 현 경로 유지.

### 3.3 LinkML→jsonl 생성기 (갭 C) — 점진

compile이 OWL/TTL만 내고 jsonl을 안 만드는 문제. 점진 전략:
- 단기: jsonl은 구세대(`yaml_to_jsonl.py`) 유지, `scan_ttl_bridge.py`(owl_class↔TTL 정합 게이트)로 drift 감시.
- 중기: LinkML→jsonl projection을 compile/materialize에 추가하고, 스키마(`entity_id`/`extra` vs `id`/`label`) 통일.

### 3.4 결정 (Resolved 2026-06-02)

> [!important] 진행 순서 — 사용자 결정(2026-06-02): **도구 우선, 마이그레이션 후행**
> consumer repo(my-knowledge-base)에서 vault-local 스크립트로 점진 이행하지 **않는다**. 대신 **MSM v0.13.0 도구 자체를 먼저 완성**(owl_postprocess를 플러그인에 정식 편입 + 경로 정합)한 뒤, 그 완성된 표준 도구로 KB를 마이그레이션한다.

| # | 쟁점 | 결정 | 근거 |
|---|------|------|------|
| 1 | owl_postprocess 배선 | **(a) 플러그인 `postprocess` 서브명령 정식 편입 + compile 기본 자동 적용**(`--no-postprocess`로 off). materialize는 compile 경유 상속. | "도구 우선" 원칙. (a)가 compile/materialize 양쪽을 덮음. vault-local(c)은 파일럿 한정·비표준. AC-7은 §3.1 note대로 additive로 재정의. |
| 2 | 경로 정합 | **(a) `--out-dir`/`--inferred-dir` 인자화**, 기본값=현 경로 유지. canonical은 허브가 **선언한** 경로를 따름(`system/semantic/` 리터럴 금지). | 컨벤션이 repo마다 다름(이 repo 허브=`ontology/Tbox/`, consumer KB=`system/semantic/`). 하드코딩은 플러그인 자체 템플릿을 깸. 2단계 projection(b)은 이동 실패면 증가로 기각. |
| 3 | 다국어 라벨 | **`annotations.label_<lang>` 컨벤션 확정** (`label_ko`/`label_en`…). | LinkML `structured_aliases`는 skos:altLabel 계열로 매핑 → `rdfs:label "..."@ko` 트리플을 **정확히 재현 못 함**. 손-TTL 무손실 대체 목표에 부적합. |
| 4 | functional 표현 | **`annotations.owl_characteristic`** 채택. 지원: `FunctionalProperty`/`InverseFunctionalProperty`(owlgen 미지원 주 타깃) + `Symmetric`/`Asymmetric`/`Transitive`/`Reflexive`/`Irreflexive`(보강). | `maximum_cardinality: 1`은 owlgen이 **클래스 cardinality restriction**으로 내며, 전역 property 특성 `owl:FunctionalProperty`와 **의미가 다름**(손-TTL 무손실 재현 불가). |

> [!note] 체크포인트 (2026-06-02, 결정 완료)
> 방법론·실증(enterprise-workflow 무손실)·갭 식별·**4개 결정 모두 해소**. 다음 작업 = **MSM v0.13.0 도구 구현**(owl_postprocess 편입 + 경로 정합) → 완성 후 KB 도메인별 마이그레이션. 파일럿 산출물은 §7 참조(구현 시 레퍼런스).

---

## 4. 마이그레이션 (점진, 도메인별)

손-작성 TTL이 있는 KB에서 LinkML 정본으로 무손실 이행:

1. **A0** — `ontology/system/TBox/`(LinkML 정본)·`ABox/` 디렉토리. compile.py 입력경로(`ontology/definition/`)는 symlink로 우회(플러그인 무수정).
2. **A1 (파일럿)** — 1개 도메인 LinkML 작성 → compile + postprocess → 손-TTL과 rdflib 대조 → 손실 0 확인.
3. **A2** — 무손실 확인 후 손-TTL을 generated로 전환(`# GENERATED — DO NOT EDIT` 헤더). 자유형 주석 중 살릴 것은 `description`으로 이관.
4. **확산** — TTL 기존 도메인(legal/healthcare/semantic-web) → 대형 도메인(technical) 순.
5. **정본 선언** — 전 도메인 전환 후 `canonical_root_hub.yaml`의 `structural_ssot: jsonl → linkml`. (그 전엔 dead declaration이므로 보류.)

> [!warning] 자유형 주석 손실 주의
> 손-TTL의 `#` 자유 주석(설계 철학·대응표)은 트리플이 아니라 `description`으로 옮긴 만큼만 `rdfs:comment`로 보존. A2 덮어쓰기 전 중요 설명 이관 필수.

---

## 5. Non-Goals

- LinkML→jsonl 스키마 완전 통일(갭 C 중기) — 본 addendum은 감시(scan_ttl_bridge)까지, 통일은 별도.
- canonical_root_hub `structural_ssot` 실제 전환 — 마이그레이션 완료 후(§4-5).
- owlgen 자체 패치(functional 메타슬롯 추가) — upstream 의존, 후처리로 우회.

---

## 6. 인수 조건 (AC)

| # | 조건 |
|---|------|
| AC-A1 | LinkML 정본 + compile + owl_postprocess 결과가 손-작성 OWL과 의미 트리플 손실 0 (enterprise-workflow에서 입증 완료) |
| AC-A2 | `owl_postprocess`가 `annotations.label_<lang>` → `rdfs:label@<lang>`, `annotations.owl_characteristic` → `owl:...Property` 주입 |
| AC-A3 | `compile --no-postprocess` 산출 TTL은 v0.13.0 owlgen base와 **트리플 동일**(postprocess는 순수 가산). 결정적 검증. |
| AC-B1 | compile/reason 출력 경로가 **`--out-dir`/`--inferred-dir`로 인자화**되고, 미지정 시 v0.13.0 기본 경로 유지. canonical 배치는 `canonical_root_hub.yaml`이 **선언한** 경로를 따름(리터럴 `system/semantic/` 비의존). |
| AC-C1 | `scan_ttl_bridge`로 owl_class↔TTL 정합 커버리지 측정 가능 (별도 게이트, 파일럿 레퍼런스) |
| AC-M1 | 도메인별 마이그레이션이 dry-run 대조 → 손실 0 확인 후에만 A2(덮어쓰기) 진행 |
| AC-7 | **재정의:** owlgen base 출력 불변 + postprocess는 가산(additive) — `--no-postprocess`(AC-A3) 시 v0.13.0과 동일. Obsidian projection 불변. 기존 v0.12.0 CLI(add/mece/list/project) 동작 변화 없음. |

---

## 7. 참고 — 산출물 (my-knowledge-base 파일럿)

- LinkML 정본: `ontology/system/TBox/enterprise-workflow.yaml`
- 후처리 레이어: `.claude/scripts/owl_postprocess.py` (도메인 무관, 재사용)
- 정합 게이트: `.claude/scripts/scan_ttl_bridge.py`
- 자체 평가/로드맵: `paper/research/property-graph-vs-rdf-owl/2026-06-02_MSM-KB-자체평가-하이브리드컴파일-패턴-적합도.md`
