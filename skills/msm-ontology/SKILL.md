---
name: msm-ontology
description: |
  MSM KB의 entity / relation / instance를 JSONL에 등록하고, MECE를 강제하며,
  Markdown projection을 유지하는 Fat Skill. v0.13.0부터 LinkML OWL reasoning layer 추가:
  YAML → OWL/Turtle 컴파일, owlready2 class inference, inferred facts JSONL 역주입.
  v0.13.1: PROV-O 출처 레이어 — owl:Class를 source_refs와 조인해 prov:hadPrimarySource를
  투영하고, SHACL로 근거 미상 노드를 차단(shapes-validate 자동 병합).
  트리거: "entity 등록", "relation 등록", "instance 등록", "MECE 검증", "온톨로지 확장",
  "msm-ontology add", "OWL 추론", "class inference", "compile", "materialize", "prov", "출처 강제"
---

# msm-ontology

책임: add(등록) · mece(검증) · project(MD 갱신) · compile(YAML→OWL) · postprocess(OWL 보강) · abox-compile(ABox→individual) · **rbox(Role/Property 1급 — 선언/list/compile/validate)** · axiom(TBox classification-rule + **RBox property** 공리 HITL 저작) · reason(TBox+RBox+ABox 병합 추론, property=graph-diff) · materialize · explain · **prov(PROV-O 출처 레이어 — v0.13.1)**

자세한 파일 레이아웃 · ID 규칙 · JSONL 스키마는 [references/core.md](references/core.md) 참조.

## CLI 요약

```
# 등록
msm-ontology add --target REPO --cluster NAME
  --entity LABEL [...]      | --relation LABEL --source ID --target-id ID
  | --instance LABEL --type ID
  --evidence URI [...] [--status draft|accepted|stable|deprecated] [--apply]

# 검증 / 조회
msm-ontology mece     --target REPO [--cluster NAME]
msm-ontology list     --target REPO [--cluster NAME] [--kind entity|relation|instance]
msm-ontology project  --target REPO --cluster NAME [--apply]

# 정의 / 검증 (v0.13.0 — SHACL 기반)
msm-ontology definition       --target REPO --domain NAME [--list]
msm-ontology shapes-validate  --target REPO {--domain NAME | --all | --classes PATH --shapes PATH}
                              [--inference {none,rdfs,owlrl,both}]   # 기본 none
                              # v0.13.1: 같은 디렉토리 *.prov.ttl·*.prov.shapes.ttl 자동 병합
msm-ontology gen-ddl          --target REPO --domain NAME [--apply]

# PROV-O 출처 강제 (v0.13.1)
msm-ontology prov             --target REPO {--domain NAME | --all} [--apply]
  # classes.ttl(dct:identifier) ⋈ entities.jsonl(source_refs)
  #   → {name}.prov.ttl (1차 출처 prov:Entity + prov:hadPrimarySource)
  #   + {name}.prov.shapes.ttl (네임스페이스 owl:Class 출처 minCount 1 게이트)
  # 조인 키(dct:identifier) 없는 도메인은 skip + 경고 (compile 단계 출처 주입 필요)

# ECA
msm-ontology eca-run      --target REPO --table TABLE --row JSON
msm-ontology eca-schedule --target REPO [--domain NAME] [--dry-run]

# RBox — Role/Property layer (v0.13.0, 1급)
msm-ontology rbox add-relation --target REPO --domain D --label L [--alt SYN ...] [--description T] --evidence URI [--status draft|accepted] [--apply]  # role 선언 (LLM 제안, 추론 0)
msm-ontology rbox list      --target REPO --domain D [--status S]   # 선언 role + status 조회
msm-ontology rbox compile   --target REPO [--domain D] [--apply]    # roles YAML → {domain}.rbox.ttl (+postprocess)
msm-ontology rbox validate  --target REPO --domain D                # Abox 술어 ↔ roles ↔ MECE 정합 게이트 (AC-R7)
msm-ontology axiom property --target REPO --domain D --role R [--characteristic X] [--inverse R2] [--subproperty-of R2] [--chain R_a R_b ...] [--domain-class C] [--range C] [--show-inferences] [--apply]  # RBox 공리 HITL 저작

# OWL reasoning (v0.13.0 RBox)
msm-ontology compile      --target REPO [--domain NAME] [--out-dir DIR] [--no-postprocess] [--apply]  # TBox YAML → .ttl (+postprocess)
msm-ontology postprocess  --ttl PATH | --target REPO [--apply]     # owlgen 미지원 OWL(FunctionalProperty/subPropertyOf/propertyChain/inverseOf/다국어 label) 주입
msm-ontology abox-compile --target REPO [--domain NAME] [--apply]  # ABox YAML → individual .abox.ttl
msm-ontology axiom classification-rule --target REPO --domain D --class C --is-a B --some SLOT:RANGE [--show-inferences] [--apply]  # OWL TBox 공리 HITL 저작
msm-ontology reason       --target REPO [--out-dir DIR] [--inferred-dir DIR] [--apply]  # owl/*.ttl 병합 추론 → inferred.jsonl (type=객체모델, property=graph-diff)
msm-ontology materialize  --target REPO [--domain NAME] [--apply]  # compile + rbox-compile + abox-compile + reason
msm-ontology explain      --target REPO --instance ID               # 추론 근거 출력

# Harness
harness/run.sh --skill msm-ontology --tier L0 --mode validate-only --target REPO
```

## Dependencies

- Python 3.10+, Bash
- OWL reasoning / RBox 시 추가: `pip install linkml owlready2 rdflib ruamel.yaml` + Java (Pellet/HermiT)
  - RBox property 추론(chain/transitive/inverse → inferred.jsonl)은 owlready2 Pellet + graph-diff 로 동작

## Non-Goals

- evidence 수집 → `msm-evidence`
- graph traversal → `msm-graph-reasoning`
- 벡터 검색 → `msm-semantic-search`
- SPARQL endpoint, 실시간 inference → v0.14.0+ 후보
