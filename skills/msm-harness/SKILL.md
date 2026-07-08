---
name: msm-harness
version: "0.13.6"
description: |
  MSM v0.13.6 측정·저장 레이어. 4-Tier 런타임(L0~L3), run context slot 운영,
  trajectory event ontology 기록, 5-axis 계측, memory 2-tier 운영을 담당한다.
  정책 판정은 하지 않는다 (msm-orchestration 책임). worklog는 MSO v0.6.3 기준에 따라
  workflow TTL node/run context가 명시된 실행 기록으로만 남긴다.
spec: planning/msm_v0.10.0/msm-harness-SPEC.md
---

# msm-harness (v0.13.6)

## What

`harness/run.sh` 본체. workflow TTL(또는 legacy YAML) 또는 skill 진입점을 받아 4-Tier 모델로 실행하고,
모든 측정값을 `harness/trajectory/run-<id>.jsonl`에 append-only로 기록한다.
정책 판정은 하지 않는다.

`agent-context/work-memory/worklog/`는 run 종료 요약의 자동 덤프가 아니다. workflow TTL node 또는
명시적 run context를 특정할 수 있을 때만 workflow rail 실행 기록으로 작성한다. 그렇지 않은 이벤트는
`harness/trajectory/`, `auditlog/`, `track-record/`, `insight-record/` 중 의미에 맞는 저장소에 남긴다.
Stop reminder throttle은 사용자 reminder 출력에만 적용되며, harness trajectory나 worklog writer를 억제하지 않는다.

자세한 동작은 [core.md](core.md).

## Entry Points

| 진입점 | 명령 |
|--------|------|
| Harness | `runtime/run.sh --workflow PATH --tier L0 --mode dry-run --target REPO` |
| Skill-direct | `runtime/run.sh --skill NAME --tier L0 --mode validate-only --target REPO` |

## Dependencies

- Python 3.10+
- stdlib only (yaml/jsonschema 미사용; 텍스트 기반)
- Bash

## Non-Goals

- 게이트 통과 여부 판정 → `msm-orchestration`
- HITL 승인 → `msm-orchestration`
- 워크플로우 라우팅 → `msm-orchestration`
- 디렉토리 부트스트랩 → `msm-repository-setup`
