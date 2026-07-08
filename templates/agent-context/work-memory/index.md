---
msm:generated:file: true
---

# Work Memory Index

MSO 표준 `agent-context/work-memory/`의 MSM 작업 메모리 인덱스.

| 디렉토리 | 역할 |
|----------|------|
| `auditlog/` | 도구·정책·HITL 감사 이벤트 |
| `worklog/` | workflow TTL node/run context가 명시된 실행 기록 |
| `track-record/` | workflow rail 밖의 진행·판단·이슈 기록 |
| `insight-record/` | 실패·오라클 위반·반복 패턴 학습 |

`worklog/`는 세션 종료 hook의 자동 요약 저장소가 아니다. cloud/ephemeral runtime에서는 hook side effect를
다음 에이전트 기억 보장으로 보지 않고, 최종 답변·diff·tracked file을 hand-off 기준으로 삼는다.
