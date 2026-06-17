---
name: msm-orchestration
version: "0.12.0"
description: |
  MSM v0.10.0 정책·라우팅 레이어. 사용자 의도를 워크플로우로 라우팅하고,
  CC 계약·HITL 정책·5-axis gate를 강제한다. msm-harness의 측정값을 소비해
  gate_decision을 emit. PreToolUse hook으로 위험 동작을 차단.
triggers:
  - "msm 실행"
  - "워크플로우 디스패치"
  - "ontology 작업"
  - "evidence 수집"
  - "MECE 검증"
  - "GraphRAG"
  - "5-axis gate"
  - "HITL 정책"
spec: planning/msm_v0.10.0/msm-orchestration-v0.10.0-SPEC.md
---

# msm-orchestration (v0.10.0)

## What

MSM의 단일 사용자 진입점. 트리거 매칭 → 워크플로우 선택 → harness 호출 → 측정값 소비 → gate 판정.
정책은 본 스킬이, 측정은 `msm-harness`가 담당 (책임 분리).

상세 동작은 [core.md](core.md).

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI | `router/dispatch.py --intent TEXT --target REPO` |
| Gate | `policy/gate_evaluator.py --target REPO --run-id RUN_ID` |
| Hook | `hooks/pretool_use.py` (stdin payload, PreToolUse) |
| CC check | `policy/cc_check.py --target REPO` |

## Dependencies

- Python 3.10+ (stdlib only)
- `msm-harness` (run dispatch)

## Non-Goals

- 측정값 생성 → `msm-harness`
- 디렉토리 부트스트랩 → `msm-repository-setup`
- 도메인 작업 실행 → 도메인 스킬
- workflow yaml 구조 검증 (기계적) → `msm-workflow-yaml-schema-SPEC` 검증기
