---
name: msm-repository-setup
version: "1.0.0"
description: |
  MSM v1.0.0 Fat Skill — 신규 KB 프로젝트를 5-Layer 구조로 부트스트랩한다.
  canonical_root_hub.yaml, workflow 템플릿, memory/harness/docs 골격, .claude/.codex skill scaffold를 생성한다.
triggers:
  - "msm init"
  - "5-layer bootstrap"
  - "repository scaffold"
  - "canonical_root_hub 초기화"
  - "MSM v1.0.0 init"
spec: planning/msm_v1.0.0/msm-repository-setup-SPEC.md
prd: planning/msm_v1.0.0/msm_v1.0.0-PRD.md
---

# msm-repository-setup (v1.0.0)

## What

신규 markdown KB를 MSM v1.0.0의 5-Layer 토폴로지로 부트스트랩하는 Fat Skill.
실제 entity/relation/instance/evidence 내용은 만들지 않는다 — 골격, 템플릿, 계약만 채운다.

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI | `scripts/msm init [options]` |
| Harness | `harness/run.sh --skill msm-repository-setup --tier L0 --mode validate-only --target PATH` |

## Triggers

- "msm init", "이 KB 부트스트랩", "5-Layer 스캐폴드 생성"
- "canonical_root_hub.yaml 만들어줘"
- "MSM v1.0.0 repository 구조"

## Dependencies

- Python 3.10+
- 외부 패키지 없음 (stdlib만 사용; 검증은 텍스트 기반)
- Bash (CLI wrapper, harness stub)

## Non-Goals

- entity/relation 생성 → `msm-ontology`
- evidence 수집 → `msm-evidence`
- full harness runtime → `msm-harness`
- HITL gate 판정 → `msm-orchestration`
