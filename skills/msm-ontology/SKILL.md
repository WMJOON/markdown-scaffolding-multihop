---
name: msm-ontology
version: "0.13.0"
description: |
  MSM v1.2.0 Fat Skill — evidence seed를 입력으로 받아 entity / relation / instance를
  JSONL에 등록하고, MECE 원칙을 강제하며, Markdown projection을 유지한다.
  v0.12.0: definition/contract-validate/eca-run/eca-schedule/gen-ddl CLI 추가 (skeleton).
  v0.13.0: LinkML OWL reasoning layer 추가 — compile/reason/materialize/explain CLI.
            YAML → Turtle 컴파일, owlready2 추론, inferred facts JSONL 역주입.
spec: planning/msm_v1.0.0/msm-ontology-SPEC.md
prd: planning/msm-ontology_v0.13.0/msm-ontology_v0.13.0-PRD.md
---

# msm-ontology (v0.13.0)

## What

evidence seed를 입력으로 받아 structured ontology 객체를 생성하는 Fat Skill.

책임:
1. **add**: entity / relation / instance를 cluster별 JSONL에 등록
2. **link**: 각 객체에 `source_refs: [evidence:seed:...]` 강제
3. **MECE**: 중복 entity / 모호한 cluster boundary 탐지
4. **md projection**: JSONL 변경 시 대응 MD 파일 갱신
5. **compile**: LinkML YAML → OWL/Turtle 변환
6. **reason**: owlready2로 class inference 실행 → inferred facts JSONL 역주입

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — add entity | `scripts/msm-ontology add --target REPO --cluster NAME --entity LABEL [...] --evidence URI [...] [--apply]` |
| CLI — add relation | `scripts/msm-ontology add --target REPO --cluster NAME --relation LABEL --source ID --target-id ID --evidence URI [...] [--apply]` |
| CLI — add instance | `scripts/msm-ontology add --target REPO --cluster NAME --instance LABEL --type ID --evidence URI [...] [--apply]` |
| CLI — mece | `scripts/msm-ontology mece --target REPO [--cluster NAME]` |
| CLI — list | `scripts/msm-ontology list --target REPO [--cluster NAME] [--kind entity\|relation\|instance]` |
| CLI — project | `scripts/msm-ontology project --target REPO --cluster NAME [--apply]` |
| CLI — definition | `scripts/msm-ontology definition --target REPO --domain NAME [--list]` |
| CLI — contract-validate | `scripts/msm-ontology contract-validate --target REPO --domain NAME --entity TYPE --data JSON` |
| CLI — eca-run | `scripts/msm-ontology eca-run --target REPO --table TABLE --row JSON` |
| CLI — eca-schedule | `scripts/msm-ontology eca-schedule --target REPO [--domain NAME] [--dry-run]` |
| CLI — gen-ddl | `scripts/msm-ontology gen-ddl --target REPO --domain NAME [--apply]` |
| CLI — compile | `scripts/msm-ontology compile --target REPO [--apply]` |
| CLI — reason | `scripts/msm-ontology reason --target REPO [--apply]` |
| CLI — materialize | `scripts/msm-ontology materialize --target REPO [--apply]` |
| CLI — explain | `scripts/msm-ontology explain --target REPO --instance ID` |
| Harness | `harness/run.sh --skill msm-ontology --tier L0 --mode validate-only --target REPO` |

## Triggers

- "entity 등록", "relation 등록", "instance 등록"
- "MECE 검증", "온톨로지 확장"
- "msm-ontology add"
- "OWL 추론", "class inference", "compile", "materialize"

## Dependencies

- Python 3.10+
- `linkml` (YAML → OWL 컴파일)
- `owlready2` (OWL2 DL reasoning)
- Bash (CLI wrapper, harness)

## Non-Goals

- evidence collection → `msm-evidence`
- LLM 기반 자동 entity 추출 → v0.14.0 후보
- graph traversal / multi-hop → `msm-graph-reasoning`
- 벡터 검색 → `msm-semantic-search`
- SPARQL endpoint → v0.14.0 후보
- 실시간 inference (변경 감지 + 자동 reason) → v0.15.0 후보
