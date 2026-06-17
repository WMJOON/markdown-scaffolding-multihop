---
name: msm-maintain
version: "0.12.0"
description: |
  MSM v0.10.0 KB 유지보수 스킬. drift/orphan/eval 탐지, 정합 복구 계획 생성,
  analysis report 산출, troubleshooting 기록을 담당한다.
  새 entity 생성은 하지 않는다 — 변경은 plan으로 산출 후 사용자 ack 필요.
spec: planning/msm_v0.10.0/msm-maintain-SPEC.md
prd: planning/msm_v0.10.0/msm_v0.10.0-PRD.md
---

# msm-maintain (v0.10.0)

## What

KB의 무결성·일관성·관측성을 점검하고 정정 계획을 생성하는 Fat Skill.

책임:
1. **scan**: drift / orphan / inconsistency 탐지
2. **rewrite**: md ↔ jsonl 정합 회복 계획
3. **analysis**: cluster 통계, evidence 커버리지, status 분포
4. **report**: 결과를 `memory/task-context/troubleshooting/` 및 `harness/reports/`에 기록

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — scan | `scripts/msm-maintain scan --target REPO [--cluster NAME] [--kind drift|orphan|eval|all]` |
| CLI — rewrite | `scripts/msm-maintain rewrite --target REPO --plan PATH [--apply]` |
| CLI — analyze | `scripts/msm-maintain analyze --target REPO [--cluster NAME]` |
| CLI — report | `scripts/msm-maintain report --target REPO --since YYYY-MM-DD` |
| Harness | `harness/run.sh --skill msm-maintain --tier L0 --mode validate-only --target REPO` |

## Triggers

- "drift 탐지", "orphan 탐지", "KB 정리"
- "KB 무결성 검사", "maintenance scan"
- "msm-maintain scan", "msm maintain"

## Dependencies

- Python 3.10+ (stdlib only)
- Bash (CLI wrapper, harness)

## Non-Goals

- entity 생성 → `msm-ontology`
- evidence 수집 → `msm-evidence`
- graph 추론 → `msm-graph-reasoning`
- 검색 인덱스 갱신 → `msm-semantic-search`
- 자동 ID rename (HITL 필요)
