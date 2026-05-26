---
name: msm-repository-setup
version: "1.2.0"
description: |
  MSM v1.2.0 Fat Skill — 신규 KB 프로젝트를 5-Layer 구조로 부트스트랩한다.
  canonical_root_hub.yaml, workflow 템플릿, memory/harness/docs 골격, .claude/.codex skill scaffold를 생성한다.
  v1.2.0: init 완료 시 index.yaml 자동 생성·갱신 (mso-scaffold-design v2 스키마).
triggers:
  - "msm init"
  - "5-layer bootstrap"
  - "repository scaffold"
  - "canonical_root_hub 초기화"
  - "MSM v1.0.0 init"
  - "index.yaml 생성"
spec: planning/msm_v1.0.0/msm-repository-setup-SPEC.md
prd: planning/msm_v1.2.0/msm_v1.2.0-PRD.md
---

# msm-repository-setup (v1.2.0)

## What

신규 markdown KB를 MSM v1.0.0의 5-Layer 토폴로지로 부트스트랩하는 Fat Skill.
실제 entity/relation/instance/evidence 내용은 만들지 않는다 — 골격, 템플릿, 계약만 채운다.

**v1.2.0 추가:** `init --apply` 완료 시 `index.yaml`을 자동 생성·갱신한다.

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI | `scripts/msm init [options]` |
| index.yaml 단독 생성 | `python scripts/gen_index.py --target PATH [--name NAME] [--domain DOMAIN]` |
| Harness | `harness/run.sh --skill msm-repository-setup --tier L0 --mode validate-only --target PATH` |

## index.yaml 자동 생성 규칙 (v1.2.0)

`apply_init.py`가 init 완료 후 `gen_index.py`를 호출한다.

| 상태 | 동작 |
|------|------|
| `index.yaml` 없음 | MSM 표준 모듈 포함 신규 생성 |
| `index.yaml` 있음 + `x_msm_generated` 마커 | MSM 모듈(`msm-instance`, `msm-ontology-layer`) 병합, 기존 모듈 보존 |
| `index.yaml` 있음 + 마커 없음 | skip (사용자 관리 파일 — HITL 정책 준수) |

생성된 `index.yaml`은 `sf_node.py validate`로 자동 검증 가능:
```bash
python sf_node.py validate index.yaml
```

## Triggers

- "msm init", "이 KB 부트스트랩", "5-Layer 스캐폴드 생성"
- "canonical_root_hub.yaml 만들어줘"
- "MSM v1.0.0 repository 구조"
- "index.yaml 자동 생성"

## Dependencies

- Python 3.10+
- `pyyaml>=6.0` (gen_index.py용 — 없으면 index.yaml 생성 건너뜀)
- Bash (CLI wrapper, harness stub)

## Non-Goals

- entity/relation 생성 → `msm-ontology`
- evidence 수집 → `msm-evidence`
- full harness runtime → `msm-harness`
- HITL gate 판정 → `msm-orchestration`
- index.yaml의 사용자 모듈 자동 추가 (사용자가 직접 편집)
