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

## 기본 탐색 레일: rg seed → zvec expansion → source validation

KB 유지보수와 개념 탐색은 `rg` 키워드 검색만으로 끝내지 않는다. `rg`는 빠른 seed 단계이고, `zvec`은 표면어가 다른 인접 노트를 끌어오는 의미 확장 단계다.

```
1. rg로 정확한 용어·ID·파일 경로 seed 확보
2. zvec으로 유사 개념·사례·근거 후보 확장
3. wikilink/RDF/JSONL 관계로 후보 간 연결 확인
4. 원문 라인 또는 evidence seed로 최종 근거 검증
```

`zvec`을 생략할 수 있는 경우는 exact string 조회, 파일 존재 확인, 특정 ID/라인 검증처럼 의미 확장이 필요 없는 작업뿐이다. index가 없거나 오래된 경우에는 `semantic_expansion_skipped`로 기록하고, 다음 유지보수 작업에 ontology-index 갱신을 큐잉한다.

---

## 시나리오 1: 새 evidence 추가 후 ontology 업데이트

```
1. msm-evidence collect → evidence/seeds.jsonl 갱신
2. msm-maintain scan --check drift
   → ontology 노드 중 새 evidence를 미반영한 노드 목록
3. msm-maintain rewrite --dry-run → 변경 사항 미리보기
4. msm-maintain rewrite --apply → 승인된 노드만 적용
5. workflow TTL node가 명시된 유지보수 실행이면 `agent-context/work-memory/worklog/`에 node 실행 기록 작성
   (node 맥락이 없으면 `track-record/` 또는 `insight-record/` 후보로 기록)
```

---

## 시나리오 2: orphan 노드 연결

```
1. msm-maintain scan --check orphan
   → wikilink 0개 노드 목록
2. msm-semantic-search link-relations
   → evidence/semantic-link/relation_candidates.jsonl 후보 생성
3. 후보별 source_path/chunk 원문 검증 + evidence:seed:* 부착
4. msm-ontology add --relation ... --evidence evidence:seed:* --apply
5. msm-maintain scan --check orphan (재확인)
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

`msm-harness`가 유지보수 실행 결과를 trajectory에 append-only 이벤트로 기록합니다.

```
agent-context/work-memory/worklog/       ← workflow TTL node 실행 기록
agent-context/work-memory/auditlog/      ← 도구·정책·HITL 감사 이벤트
agent-context/work-memory/track-record/  ← workflow rail 밖의 진행·판단·이슈 기록
agent-context/work-memory/insight-record/← 실패·오라클 위반·반복 패턴 학습
harness/trajectory/                      ← append-only 5-Axis 계측 이벤트
```

위험도 High 변경은 `msm-orchestration`의 HITL 게이트를 통과해야 합니다.

| 위험도 | 처리 |
|--------|------|
| Low | 자동 반영 |
| Medium | dry-run 확인 후 적용 |
| High | HITL 승인 필수 (`msm-orchestrate cc-check`) |
