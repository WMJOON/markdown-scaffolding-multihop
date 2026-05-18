# Memory Tier Contract

SPEC: `msm-harness-SPEC` §4.

## 2-Tier

| Tier | 경로 | 수명 | 쓰기 주체 |
|------|------|------|----------|
| task-context | `memory/task-context/` | 단기 (실행/세션) | run 종료 시 harness가 요약 |
| workspace-index | `memory/ontology-index/` | 영구 | drift 발생 시 harness가 재계산 |

`user-memory`는 MSM 범위 밖.

## task-context 하위

| 디렉토리 | 내용 | 파일명 |
|----------|------|--------|
| `work-log/` | 매 run의 요약 | `<run_id>.md` |
| `decision-history/` | HITL 응답·옵션 선택 | `<run_id>__<topic>.md` |
| `troubleshooting/` | L2/L3 실패·오라클 위반 | `<run_id>__<issue>.md` |
| `release-note/` | 사용자 보고 가능 변경 | `<date>__<topic>.md` |

## work-log 포맷 (harness 기본)

```markdown
---
run_id: 20260518T120000Z
workflow_id: evidence.collection.default
skill: msm-evidence
tier: L0
mode: dry-run
exit_code: 0
duration_seconds: 8
started_at: 2026-05-18T12:00:00Z
finished_at: 2026-05-18T12:00:08Z
---

# Run 20260518T120000Z

## 5-Axis

- non_determinism: 0.04
- trajectory_complete: true
- oracle_score: 0.92 (threshold 0.85)
- cost: 1200 tokens · 8s · 0 Wh (fallback)
- hitl: 0/0

## Outputs

- evidence/seeds.jsonl: +12 appended
- evidence/md/: 2 created
```

## 보존 정책

| 항목 | 보존 |
|------|------|
| work-log, decision-history, troubleshooting, release-note | 무기한 |
| ontology-index | 항상 최신 (덮어쓰기) |
| `.msm-context/active/<run_id>/` | run 종료 후 7일, 이후 archive |
| `.msm-context/archive/` | 30일, 이후 GC |
