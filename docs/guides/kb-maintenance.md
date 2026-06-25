# KB 유지보수 가이드

`msm-maintain`이 담당합니다. scan → analyze → rewrite → report 순서로 진행합니다.

---

## 언제 유지보수가 필요한가

| 증상 | 적용 |
|------|------|
| orphan 노드 (wikilink 0개) | `scan --check orphan` |
| 노트가 너무 길어졌다 | `scan --check length` |
| 같은 내용이 여러 곳에 흩어졌다 | `scan --check redundancy` |
| 새 evidence를 추가했는데 ontology에 미반영 | `scan --check drift` |
| KB 전체 상태 리포트가 필요하다 | `report` |

---

## 기본 명령

```bash
# 상태 스캔
skills/msm-maintain/scripts/msm-maintain scan \
  --target my-kb [--check orphan|drift|length|redundancy]

# 통계 분석
skills/msm-maintain/scripts/msm-maintain analyze --target my-kb

# rewrite (dry-run 먼저)
skills/msm-maintain/scripts/msm-maintain rewrite \
  --target my-kb --node ontology/explain/concept/ai_agent/md/concept__rlhf.md \
  --dry-run

# 리포트
skills/msm-maintain/scripts/msm-maintain report --target my-kb
```

---

## 시나리오 1: 새 evidence 추가 후 ontology 업데이트

```
1. msm-evidence collect → evidence/seeds.jsonl 갱신
2. msm-maintain scan --check drift
   → ontology 노드 중 새 evidence를 미반영한 노드 목록
3. msm-maintain rewrite --dry-run → 변경 사항 미리보기
4. msm-maintain rewrite --apply → 승인된 노드만 적용
5. agent-context/work-memory/worklog/ 에 변경 이력 기록
```

---

## 시나리오 2: orphan 노드 연결

```
1. msm-maintain scan --check orphan
   → wikilink 0개 노드 목록
2. msm-ontology list → 연결 후보 탐색
3. msm-ontology add (relation 추가) --apply
4. msm-maintain scan --check orphan (재확인)
```

---

## 시나리오 3: KB 전체 상태 점검

```bash
skills/msm-maintain/scripts/msm-maintain report --target my-kb
# → report/maintenance/ 에 리포트 저장
#   - entity 수, orphan 수, drift 비율
#   - 최근 변경 이력 요약
```

---

## 거버넌스 통합

`msm-harness`가 유지보수 실행 결과를 trajectory에 기록합니다.

```
agent-context/work-memory/worklog/       ← 단기 작업 이력
agent-context/work-memory/auditlog/      ← 감사 로그
agent-context/work-memory/track-record/  ← 진행·성과 기록
harness/trajectory/                      ← 5-Axis 계측값
```

위험도 High 변경은 `msm-orchestration`의 HITL 게이트를 통과해야 합니다.

| 위험도 | 처리 |
|--------|------|
| Low | 자동 반영 |
| Medium | dry-run 확인 후 적용 |
| High | HITL 승인 필수 (`msm-orchestrate cc-check`) |
