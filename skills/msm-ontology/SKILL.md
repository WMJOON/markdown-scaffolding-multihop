---
name: msm-ontology
version: "1.1.0"
description: |
  MSM v1.1.0 Fat Skill — evidence seed를 입력으로 받아 entity / relation / instance를
  JSONL에 등록하고, MECE 원칙을 강제하며, Markdown projection을 유지한다.
  v1.1.0: 실시간 진행상황 로깅 추가, continue-on-error 동작 개선.
triggers:
  - "msm-ontology add"
  - "entity 등록"
  - "relation 등록"
  - "instance 등록"
  - "MECE 검증"
  - "온톨로지 확장"
  - "Knowledge Graph"
  - "KB 구조화"
spec: planning/msm_v1.0.0/msm-ontology-SPEC.md
prd: planning/msm_v1.0.0/msm_v1.0.0-PRD.md
---

# msm-ontology (v1.1.0)

## What

evidence seed를 입력으로 받아 structured ontology 객체를 생성하는 Fat Skill.

책임:
1. **add**: entity / relation / instance를 cluster별 JSONL에 등록
2. **link**: 각 객체에 `source_refs: [evidence:seed:...]` 강제
3. **MECE**: 중복 entity / 모호한 cluster boundary 탐지
4. **md projection**: JSONL 변경 시 대응 MD 파일 갱신

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
| Harness | `harness/run.sh --skill msm-ontology --tier L0 --mode validate-only --target REPO` |

## Triggers

- "entity 등록", "relation 등록", "instance 등록"
- "MECE 검증", "온톨로지 확장"
- "msm-ontology add"

## Dependencies

- Python 3.10+
- 외부 패키지 없음 (stdlib만)
- Bash (CLI wrapper, harness)

## Non-Goals

- evidence collection → `msm-evidence`
- LLM 기반 자동 entity 추출 → v1.1
- graph traversal / multi-hop → `msm-graph-reasoning`
- 벡터 검색 → `msm-semantic-search`
