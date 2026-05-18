# core — msm-maintain

## 1. 공통 프로토콜 (SCAN / REWRITE / ANALYZE / REPORT)

| 단계 | 책임 | 산출 |
|------|------|------|
| SCAN | KB 탐색 → drift/orphan/eval 탐지 → plan JSON 출력 | stdout plan JSON, `harness/trajectory/run-<id>.jsonl` |
| REWRITE | plan.auto_fixes 적용 (create_md_placeholder) | md placeholder 파일, `memory/task-context/troubleshooting/<id>__rewrite.md` |
| ANALYZE | cluster별 eval 통계 계산 → report 저장 | stdout report, `harness/reports/maintain-analysis-<id>.md` |
| REPORT | trajectory 읽기 → troubleshooting 요약 | `memory/task-context/troubleshooting/<id>__report.md` |

## 2. CLI

```bash
# drift/orphan/eval 모두 scan (기본)
scripts/msm-maintain scan --target ./my-kb

# 특정 cluster만
scripts/msm-maintain scan --target ./my-kb --cluster ai_agent

# drift만
scripts/msm-maintain scan --target ./my-kb --kind drift

# dry-run rewrite (기본 — 파일 변경 없음)
scripts/msm-maintain rewrite --target ./my-kb --plan /path/to/plan.json

# rewrite 실제 적용
scripts/msm-maintain rewrite --target ./my-kb --plan /path/to/plan.json --apply

# analysis report 생성
scripts/msm-maintain analyze --target ./my-kb

# troubleshooting report
scripts/msm-maintain report --target ./my-kb --since 2026-05-01
```

## 3. Scan 종류

### drift

| 유형 | 조건 |
|------|------|
| `jsonl_without_md` | entities.jsonl entry는 있는데 md_path 파일이 없음 |
| `md_without_jsonl` | `ontology/Tbox/{c}/md/*.md`은 있는데 entities.jsonl에 entry 없음 |
| `stale_generated_block` | md의 `<!-- msm:generated:start/end -->` 블록 해시가 entity 해시와 불일치 (HITL 전용) |
| `evidence_dangling` | source_refs의 `evidence:seed:…` id가 seeds.jsonl에 없음 |
| `cluster_mismatch` | jsonl `cluster` 필드와 디렉토리 경로 cluster가 다름 |

### orphan

| 유형 | 조건 |
|------|------|
| `md_orphan` | `ontology/Tbox/{c}/md/*.md`인데 어떤 jsonl도 `md_path`로 참조 안 함 |
| `seed_orphan` | `evidence/md/*.md`인데 seeds.jsonl에 없음 |
| `no_incoming_relation` | accepted+ entity인데 in/out relation 수 = 0 |

### eval

cluster별 통계:
- entity / relation / instance 수
- status 분포 (draft/accepted/stable/deprecated)
- evidence coverage = source_refs ≥ 1인 entity 비율
- relation density = relation_count / max(entity_count, 1)

## 4. Auto-fix 허용 범위

| Action | 조건 |
|--------|------|
| `create_md_placeholder` | `jsonl_without_md` 발견 시 → 최소 stub md 파일 생성 |

다음은 항상 `hitl_required`:
- id rename
- entity/relation 삭제
- cluster 이동
- stale_generated_block 재계산 (사용자 작성 내용 손실 가능)
- accepted+ entity에 영향 주는 rewrite

## 5. Bulk Rewrite 가드

`auto_fixes ≥ 100`인 plan에 대해 `rewrite --apply` → exit 100 + hitl_request 발행.

## 6. 산출 위치

| 경로 | 내용 |
|------|------|
| stdout | scan plan JSON / analyze report / report text |
| `harness/trajectory/run-<id>.jsonl` | scan 이벤트 로그 |
| `harness/reports/maintain-analysis-<id>.md` | analyze report 저장 |
| `memory/task-context/troubleshooting/<id>__rewrite.md` | rewrite 적용 로그 |
| `memory/task-context/troubleshooting/<id>__report.md` | troubleshooting report |

## 7. Oracle — maintain_drift_readiness

| 조건 | 점수 |
|------|------|
| drift count = 0 | +0.40 |
| orphan count = 0 | +0.20 |
| evidence coverage avg ≥ 0.80 | +0.20 |
| relation density avg ≥ 0.5 | +0.10 |
| canonical_root_hub.yaml 존재 + locked=true | +0.10 |

Gate: ≥0.85 pass, ≥0.70 warn, <0.70 fail.
