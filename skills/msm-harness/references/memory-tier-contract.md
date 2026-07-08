# Memory Tier Contract

SPEC: `msm-harness-SPEC` §4.

## 2-Tier

| Tier | 경로 | 수명 | 쓰기 주체 |
|------|------|------|----------|
| worklog | `agent-context/work-memory/worklog/` | workflow rail 실행 기록 | workflow TTL node/run context가 명시된 writer |
| audit/index | `agent-context/work-memory/{auditlog,index.md}` | 영구 | orchestration/harness가 갱신 |

`user-memory`는 MSM 범위 밖.

## task-context 하위

| 디렉토리 | 내용 | 파일명 |
|----------|------|--------|
| `worklog/` | workflow TTL node 실행 기록 | `<run_id>.md` 또는 `<node_id>.md` |
| `auditlog/` | HITL 응답·옵션 선택·감사 이벤트 | `<run_id>__<topic>.md` |
| `track-record/` | workflow rail 밖의 진행·판단·이슈 기록 | `<date>__<topic>.md` |
| `insight-record/` | L2/L3 실패·오라클 위반에서 얻은 인사이트 | `<run_id>__<issue>.md` |

## work-log 포맷 (workflow node 실행 기록)

```markdown
---
run_id: 20260518T120000Z
workflow_id: evidence.collection.default
workflow_node: evidence.collect
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

workflow_id 또는 workflow_node를 특정할 수 없는 run은 worklog를 만들지 않는다. 그런 실행은
`harness/trajectory/run-<id>.jsonl`에 계측 이벤트로 남기고, 의미 있는 판단은 `track-record/` 또는
`insight-record/` 후보로 기록한다.

## 보존 정책

| 항목 | 보존 |
|------|------|
| worklog, auditlog, track-record, insight-record | 무기한 |
| index.md | 항상 최신 (덮어쓰기) |
| `.msm-context/active/<run_id>/` | run 종료 후 7일, 이후 archive |
| `.msm-context/archive/` | 30일, 이후 GC |
