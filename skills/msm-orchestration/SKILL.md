---
name: msm-orchestration
version: "0.13.6"
description: |
  MSM v0.13.6 정책·라우팅 레이어. 현재 명칭은 가칭이며, 스코프는 ontology
  knowledge base 구성과 AI 추론 경로 제약으로 좁힌다. 사용자 의도를 ontology
  구축/정합성 검증 워크플로우로 라우팅하고, CC 계약·HITL 정책·5-axis gate를
  강제한다. 일반 리서치·리포트 수집/표현 워크플로우는 각 consumer repository의
  일반 구성이 소유한다.
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

# msm-orchestration (v0.13.6)

## What

MSM(가칭)의 단일 사용자 진입점. 트리거 매칭 → ontology workflow 선택 → harness 호출 → 측정값 소비 → gate 판정.
정책은 본 스킬이, 측정은 `msm-harness`가 담당 (책임 분리).

상세 동작은 [core.md](core.md).

## Scope Boundary

- **In scope**: ontology KB 구성, TBox/RBox/ABox 정합성, MECE/parent-alignment, RDF/OWL/LinkML 기반 추론 경로 제약, ontology drift/orphan 탐지.
- **Out of scope**: 일반 리서치 수집, 리포트 작성, 소비자-facing projection 디자인. 이런 워크플로우는 각 repository가 MSO workflow와 자체 도구로 구성한다.
- **Consumer relation**: MSO는 workflow/task rail/work-memory를 소유하고, MSM(가칭)이 제공한 ontology를 소비해 실행 경로와 검증 기준을 제한한다.
- **UUG relation**: UUG는 사용자가 MSO와 MSM(가칭)을 쉽게 쓰도록 target/intent/entity-filling proposal을 제공하지만, ontology 정본은 MSM(가칭)이, workflow slot spec은 MSO가 소유한다.

MSO v0.6.3 정렬: hook side effect는 hand-off 보장이 아니다. Codex cloud 같은 ephemeral runtime에서는
최종 답변, diff, 커밋 가능한 tracked file이 다음 에이전트 인계 기준이다.
MSO v0.6.3의 Stop reminder throttle은 사용자에게 보이는 Stop reminder adapter에만 적용한다.
MSM `PreToolUse` hook은 정책 차단/허용 adapter이므로 `stop-check.sh` 대상이 아니다.

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
- workflow TTL 구조 검증 (기계적) → workflow TTL/SHACL 계층. YAML은 migration layer
