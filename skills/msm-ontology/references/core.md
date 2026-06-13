# msm-ontology — Core Reference

## 1. 파일 레이아웃

```
{target}/
  ontology/
    Tbox/
      {cluster}/
        entities.jsonl
        relations.jsonl
        md/
          {snake_label}.md
    Abox/
      {cluster}/
        instances.jsonl
        md/
          {snake_label}.md
```

## 2. ID 규칙

| 종류 | 패턴 | 예시 |
|------|------|------|
| entity | `entity:<snake_case_label>` | `entity:ai_agent` |
| instance | `instance:<snake_case_label>` | `instance:codex` |
| relation | `rel:<src_local>:<predicate>:<tgt_local>` | `rel:ai_agent:uses:tool` |

- 충돌 시 `_2`, `_3` 접미
- `accepted` 이상으로 승격된 id는 변경 금지

## 3. source_refs 강제

모든 add 호출에 `--evidence evidence:seed:...` 1개 이상 필수.
없으면 exit 1 + `source_refs_missing` 메시지.

## 4. MECE 검증

| 탐지 | 기준 |
|------|------|
| label_duplicate | 동일 cluster 내 normalized label 동일 |
| jaccard_overlap | label+synonyms Jaccard >= 0.7 |
| cluster_boundary | Tbox relation source/target이 다른 cluster |
| orphan_entity | source_refs 비어 있음 |
| missing_md | md_path 없거나 파일 없음 |

violation ≥ 1 → exit 1.

## 5. MD Projection

- `<!-- msm:generated:file ... -->` 첫 줄 마커
- frontmatter: id, label, cluster, kind/type, status, source_refs
- `<!-- msm:generated:start -->` ~ `<!-- msm:generated:end -->` 블록 갱신
- Notes 영역 (블록 아래) 보존

## 6. Oracle — `ontology_mece_readiness`

score = (entity≥1 ? 0.25 : 0)
      + (all_source_refs ? 0.25 : 0)
      + (mece_violations==0 ? 0.25 : 0)
      + (md_projection_complete ? 0.25 : 0)

## 7. OWL Reasoning Layer (v0.13.0)

LinkML YAML(TBox 정의) → OWL/Turtle 컴파일 → owlready2 추론 → inferred JSONL 역주입.

```
ontology/definition/{domain}.yaml   ← LinkML TBox (사람/HITL — axiom 도구)
        ↓ compile (owlgen + owl_postprocess 자동)
ontology/owl/{domain}.ttl           ← TBox Turtle (생성물, 직접 편집 금지)
ontology/Abox/{domain}.yaml         ← LinkML ABox 인스턴스 (LLM/evidence — RDF 사실)
        ↓ abox-compile
ontology/owl/{domain}.abox.ttl      ← ABox individual Turtle (owl:NamedIndividual)
        ↓ reason (owl/*.ttl 전부 병합 → NTriples → owlready2 Pellet/HermiT)
ontology/Abox/_inferred/inferred.jsonl   ← asserted vs inferred(gained) 구분
```

| 명령 | 동작 |
|------|------|
| `compile --target REPO [--domain N] [--out-dir DIR] [--no-postprocess] [--apply]` | TBox YAML → TTL (+postprocess) |
| `postprocess --ttl PATH \| --target REPO [--out-dir DIR] [--keep-carriers] [--apply]` | owlgen 미지원 OWL 주입 |
| `abox-compile --target REPO [--domain N] [--out-dir DIR] [--apply]` | ABox YAML → individual TTL |
| `axiom classification-rule --target REPO --domain D --class C --is-a B --some SLOT:RANGE [--show-inferences] [--apply]` | OWL 공리 HITL 저작 |
| `reason --target REPO [--out-dir DIR] [--inferred-dir DIR] [--apply]` | owl/*.ttl 병합 추론 → inferred.jsonl |
| `materialize --target REPO [...] [--apply]` | compile + abox-compile + reason |

### 7.1 owl_postprocess — 표현력 갭 보강 (addendum §3.1)

`linkml.generators.owlgen`는 `owl:FunctionalProperty`/`owl:InverseFunctionalProperty`와
다국어 `rdfs:label@lang`을 못 낸다. owlgen은 annotations를 `<prefix>:<key> "<value>"`
**carrier 트리플**로 직렬화하므로, postprocess가 이를 정식 OWL로 변환한다(carrier 제거):

| LinkML annotation | carrier (owlgen) | postprocess 산출 |
|---|---|---|
| `label_<lang>: "..."` | `ex:label_ko "초안"` | `rdfs:label "초안"@ko` |
| `owl_characteristic: "<X>Property"` | `ex:owl_characteristic "FunctionalProperty"` | `a owl:FunctionalProperty` |

- 허용 characteristic: `Functional`/`InverseFunctional`/`Symmetric`/`Asymmetric`/`Transitive`/`Reflexive`/`Irreflexive`Property.
- **idempotent**(rdflib 집합) · **TTL-only**(소스 YAML 재파싱 불필요, rdflib만 의존).
- compile 기본 자동 적용. `--no-postprocess` 시 base owlgen 출력 그대로(= v0.13.0, AC-A3).

### 7.2 경로 인자화 (addendum §3.2)

`--out-dir`/`--inferred-dir` 미지정 시 기본 경로(`ontology/owl`, `ontology/Abox/_inferred`)
유지(backward-compat). canonical 위치는 `canonical_root_hub.yaml`이 **선언한** 경로를
따르며, `system/semantic/` 같은 리터럴을 하드코딩하지 않는다(repo마다 컨벤션 상이).

### 7.3 ABox 추론 — 병합 그래프 + inferred-delta

owlready2는 Turtle을 직접 파싱하지 못해(RDF/XML·OWL/XML·NTriples만) reason이 rdflib로
변환한다. **reason은 `owl/*.ttl`(TBox + ABox)을 하나의 그래프로 병합**해 함께 추론한다 —
TBox 공리와 ABox individual이 같은 그래프에 있어야 reclassification이 동작한다.

- **abox-compile**: `Abox/{domain}.yaml`의 `instances:`를 individual TTL로. 각 individual은
  `owl:NamedIndividual`로 명시(owlready2 `.individuals()`가 NamedIndividual만 셈) + 네임스페이스는
  TBox(default_prefix)와 동일해야 함(아니면 추론 불가).
- **capability = individual** (punning 회피): `gemma4_e4b canBeUsedFor image_generation`에서
  `image_generation`은 `ImageGeneration`의 individual. `someValuesFrom`이 건전하게 fire.
- **inferred-delta**: reason 전 asserted 타입/property 스냅샷 → reason 후 diff. `inferred.jsonl`은
  `asserted_types` / `inferred_types`(gained) / `all_types` / `inferred_properties` / `source_ontology`를 기록.

검증 예 (main PRD §5): `gemma4_e4b` asserted=`[TransformerMLMModel]` → inferred=`[MultimodalModel]`.

> [!success] property-value 추론 — 해소됨 (v0.13.0 RBox P3, 2026-06-12)
> ~~owlready2/Pellet은 property value(`prop[ind]`)를 post-reason에 안 돌려준다~~ → **객체모델 접근(`prop[ind]`)의
> 비대칭일 뿐, Pellet 은 추론 결과를 quadstore(`world.as_rdflib_graph()`)에는 실제로 쓴다**(probe 검증).
> v0.13.0 부터 `reason.py` 는 **graph-diff** 로 전환: pre = raw asserted 병합 그래프, post = reason 후
> `as_rdflib_graph()`, gained = (post−raw) 중 `(s∈Ind ∧ p∈ObjProp ∧ o∈Ind)`. 이로써 **chain / transitive /
> inverse 가 `inferred_properties` 에 기록**된다(멀티홉 실측). type 재분류는 `_type_names` 객체모델 diff 유지(견고).

### 7.4 axiom — OWL 공리 HITL 저작

TBox 공리는 추론 blast-radius가 커서 자동 생성하지 않고 **사람이 대화로 결정**한다.
`axiom classification-rule`은 결과를 커밋 전에 가시화한다:
- 기본(preview, compile만 — 빠름): LinkML 스니펫 + 컴파일된 OWL(충분조건 GCI).
- `--show-inferences`(Pellet, 느림): 현 ABox에 무엇이 재분류되는지.
- `--apply`(HITL gate): **ruamel 라운드트립으로 주석 보존**하며 LinkML 정본에 병합.
  ruamel 부재 시 스니펫만 출력(주석 먹는 lossy 쓰기 금지).

> `classification_rules` → owlgen은 **충분조건 GCI**(`intersection ⊑ Class`)를 낸다.
> 이는 `owl:equivalentClass`(양방향 ≡)가 **아니다** — reclassification엔 단방향으로 충분.

### 7.5 설계 원칙 — RDF=LLM / OWL=HITL (recorded 2026-06-02)

KB 스택을 두 층으로 나눈다: **RDF/ABox**(개별 사실: `instance_of`, property assertion)는
양이 많고 출처에서 추출 가능하므로 **LLM/evidence가 파싱·populate**하는 자동화 층이다.
**OWL/TBox**(클래스 계층, classification_rule, restriction, property characteristic, disjoint)는
공리 하나가 전체를 오분류할 수 있어 **사람-에이전트 대화(HITL)로 만드는** 층이다.
도구는 OWL을 생성하지 않고 — 사람이 쓴 의도를 **컴파일**(owl_postprocess)하거나 결과를
**가시화 후 승인 시 병합**(axiom)할 뿐이다.

의존성: `pip install linkml owlready2 rdflib ruamel.yaml` + Java(Pellet/HermiT).

## 8. RBox — Role/Property Layer (v0.13.0, 1급)

> SPEC: `planning/msm-ontology_v0.14.0/msm-ontology_v0.14.0-RBox-firstclass-SPEC.md`.
> "RBox=SKOS" 안은 기각 — OWL 이 이미 들어가면 술어 통제어휘는 `owl:ObjectProperty`+`rdfs:label`+
> à-la-carte `skos:altLabel`/`skos:definition`(owlgen 이 `aliases`/`description` 에서 자동 방출)로 충분.

### 8.1 파일 레이아웃 + 티어링

```
ontology/Rbox/roles/{domain}.yaml   ← LinkML role schema (단일 정본, ruamel 라운드트립)
ontology/owl/{domain}.rbox.ttl      ← compiled (생성물)
```

role = LinkML slot. **티어는 파일이 아니라 공리 무게**로 가른다 (write-path 게이트):
- **선언부** (`rbox add-relation` — LLM/evidence): label/aliases/description + `status:draft` annotation. **추론 0**.
- **공리부** (`axiom property` — HITL `--apply`): characteristic / inverse / subPropertyOf / chain / domain·range.

네임스페이스: role IRI 는 도메인 TBox 의 `ex` prefix(`definition/{domain}.yaml`)를 재사용 → reason 병합 정렬.

### 8.2 공리 = annotation 단일 경로 (owl_postprocess 확장)

owlgen 이 드롭/미지원하는 RBox 공리를 **annotation carrier → owl_postprocess** 단일 경로로 주입한다
(native owlgen 안 씀 → split-brain·double-emit 회피):

| annotation (slot) | postprocess 산출 |
|---|---|
| `owl_characteristic: TransitiveProperty` | `a owl:TransitiveProperty` (7종) |
| `subproperty_of: R` | `rdfs:subPropertyOf <ns:R>` |
| `inverse_of: R` | `owl:inverseOf <ns:R>` |
| `property_chain: "R_a,R_b"` | `owl:propertyChainAxiom ( <ns:R_a> <ns:R_b> )` — **순서 보존** |

- chain 은 콤마-리터럴(단일 트리플)로 순서 보존(R∘S≠S∘R). 멱등성은 **carrier 제거** 설계로 보장
  (blank-node list 는 `triple not in g` 무력 → `--keep-carriers`+chain 은 double-emit 주의).
- 대상 role(inverse/subproperty/chain)은 선언돼 있어야 한다(D-1 authoring-time 게이트).

### 8.3 추론 캡처 = graph-diff (§7.3 해소)

`reason.py` 는 type=객체모델 diff(견고), **property=graph-diff**. Pellet 단일 reasoner.
chain/transitive/inverse 가 `inferred.jsonl` 의 `inferred_properties` 에 기록된다(§7.3 참조).

### 8.4 정합 게이트 — `rbox validate`

Abox object-property 술어가 모두 `roles/` 에 선언(accepted+)됐는지 + role MECE(label 중복/alias 충돌).
violation ≥ 1 → exit 1.

### 8.5 materialize 순서

`compile(TBox) → rbox-compile(RBox) → abox-compile(ABox) → reason`. 각 단계는 소스 디렉토리가 있을 때만
실행(TBox/RBox/ABox-only KB 지원). RBox 공리가 reason 의 `owl/*.ttl` 병합 그래프에 들어가야 chain 이 fire 한다.
