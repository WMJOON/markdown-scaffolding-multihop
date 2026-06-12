---
name: msm-ontology
description: |
  MSM KB의 entity / relation / instance를 JSONL에 등록하고, MECE를 강제하며,
  Markdown projection을 유지하는 Fat Skill. v0.13.0부터 LinkML OWL reasoning layer 추가:
  YAML → OWL/Turtle 컴파일, owlready2 class inference, inferred facts JSONL 역주입.
  트리거: "entity 등록", "relation 등록", "instance 등록", "MECE 검증", "온톨로지 확장",
  "msm-ontology add", "OWL 추론", "class inference", "compile", "materialize"
---

# msm-ontology

책임: add(등록) · mece(검증) · project(MD 갱신) · compile(YAML→OWL) · postprocess(OWL 보강) · abox-compile(ABox→individual) · axiom(OWL 공리 HITL 저작) · reason(TBox+ABox 병합 추론) · materialize · explain

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

# 정의 / 검증 (v0.14.0 — SHACL 기반)
msm-ontology definition       --target REPO --domain NAME [--list]
msm-ontology shapes-validate  --target REPO {--domain NAME | --all | --classes PATH --shapes PATH}
                              [--inference {none,rdfs,owlrl,both}]   # 기본 none
msm-ontology gen-ddl          --target REPO --domain NAME [--apply]

# ECA
msm-ontology eca-run      --target REPO --table TABLE --row JSON
msm-ontology eca-schedule --target REPO [--domain NAME] [--dry-run]

# OWL reasoning (v0.13.0)
msm-ontology compile      --target REPO [--domain NAME] [--out-dir DIR] [--no-postprocess] [--apply]  # TBox YAML → .ttl (+postprocess)
msm-ontology postprocess  --ttl PATH | --target REPO [--apply]     # owlgen 미지원 OWL(FunctionalProperty/다국어 label) 주입
msm-ontology abox-compile --target REPO [--domain NAME] [--apply]  # ABox YAML → individual .abox.ttl
msm-ontology axiom classification-rule --target REPO --domain D --class C --is-a B --some SLOT:RANGE [--show-inferences] [--apply]  # OWL 공리 HITL 저작
msm-ontology reason       --target REPO [--out-dir DIR] [--inferred-dir DIR] [--apply]  # owl/*.ttl 병합 추론 → inferred.jsonl
msm-ontology materialize  --target REPO [--domain NAME] [--apply]  # compile + abox-compile + reason
msm-ontology explain      --target REPO --instance ID               # 추론 근거 출력

# Harness
harness/run.sh --skill msm-ontology --tier L0 --mode validate-only --target REPO
```

## Dependencies

- Python 3.10+, Bash
- OWL reasoning 시 추가: `pip install linkml owlready2` + Java (Pellet/HermiT)

## Non-Goals

- evidence 수집 → `msm-evidence`
- graph traversal → `msm-graph-reasoning`
- 벡터 검색 → `msm-semantic-search`
- SPARQL endpoint, 실시간 inference → v0.14.0+ 후보
