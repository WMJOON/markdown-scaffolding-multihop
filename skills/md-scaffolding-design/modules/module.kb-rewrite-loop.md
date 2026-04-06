# module.kb-rewrite-loop

> 이 모듈은 `planning/kb-heuristic-rewrite-loop.md`의 설계를 스킬 내 실행 가능한 워크플로우로 구체화한다.

## 목적

KB는 한 번 만들고 끝나지 않는다. 시간이 지나면 entropy가 쌓인다.
이 모듈은 **품질 저하 신호를 감지하고, controlled rewrite draft를 생성하고, 선택적 human review를 거쳐 점진적으로 KB를 재정렬**하는 유지보수 루프다.

---

## 6단계 루프

```
Detect → Diagnose → Draft → Review → Merge → Observe
```

---

## 1. Detect — 어떤 문서를 다시 써야 하나

Claude가 아래 heuristic 기준으로 후보 노드를 찾는다.

| 코드 | Heuristic | 감지 조건 | 후보 rewrite 종류 |
|------|-----------|-----------|-------------------|
| H-A | Length | 문단 과다, heading depth 과다, summary 없이 본문만 비대 | summary rewrite, structure rewrite |
| H-B | Redundancy | 같은 주장이 여러 노드에 반복, concept note가 사례 설명으로 오염 | dedupe rewrite, merge rewrite |
| H-C | Drift | 문서 내용이 원래 역할과 어긋남 (ontology note → evidence note화 등) | type alignment rewrite |
| H-D | Link Mismatch | 연결된 노드끼리 설명 구조가 안 맞음, ontology 변경 후 article은 예전 표현 유지 | cross-note consistency rewrite |
| H-E | Evidence Freshness | 새 evidence가 들어왔지만 본문이 업데이트 안 됨 | evidence-integrating rewrite |
| H-F | Readability | block 과도 쪼개짐, bold/heading/list 과다, 팀 공유용인데 너무 압축적 | readability rewrite, format rewrite |
| H-G | Semantic Bias | single framing 고착, uncertainty 삭제, alternative framing 부재 | framing rewrite, bias mitigation rewrite |

**스캔 방법:**
- 특정 노드 지정: "이 노트 점검해줘" → 해당 노드에 적용 가능한 heuristic 전수 체크
- 디렉토리 스캔: "이 폴더 KB 품질 점검해줘" → H-A/H-B/H-F를 자동 적용, H-C/H-D/H-G는 링크 있는 노드에만 적용
- Evidence 업데이트 후: H-E 우선 적용

---

## 2. Diagnose — rewrite 종류를 먼저 분류한다

모든 rewrite를 같은 방식으로 다루면 안 된다.
감지된 heuristic → rewrite type을 명확히 분류한 뒤 draft 생성으로 넘어간다.

| rewrite type | 설명 | 위험도 |
|--------------|------|--------|
| summary rewrite | 서두 요약 추가 또는 압축 | Low |
| structure rewrite | heading 재구성, 섹션 분리/병합 | Low–Medium |
| evidence-integrating rewrite | 새 evidence 반영 | Medium |
| taxonomy rewrite | 분류 체계 변경에 따른 업데이트 | Medium–High |
| dedupe rewrite | 중복 제거 / 두 노트 병합 | Medium |
| style/readability rewrite | 포맷, 가독성 개선 | Low |
| framing rewrite | 시각 다양화, bias 완화 | High |
| type alignment rewrite | 노드 역할 재정의 | High |
| cross-note consistency rewrite | 연결 노드 간 표현 통일 | Medium–High |

위험도가 **High인 rewrite는 반드시 human review** 후 merge.

---

## 3. Draft — controlled rewrite 생성

자유 재생성(free-form regeneration)이 아니라 **reasoned draft revision** 방식으로 생성한다.

Claude가 draft를 생성할 때 반드시 포함해야 할 항목:

```markdown
## Rewrite Rationale
- trigger heuristic: [H-A / H-B / ...]
- rewrite type: [type]
- 유지한 것: ...
- 바꾼 것: ...
- 반영한 evidence: ...
- 아직 불확실한 부분: ...
```

이 rationale은 Review 단계에서 human이 판단하는 근거가 되고,
Sidecar note 방식으로 저장할 경우 그대로 활용된다.

---

## 4. Review — 언제 human review가 필요한가

### Human review 필수
- ontology concept 변경 (H-C, taxonomy rewrite)
- semantic framing 변경 (H-G, framing rewrite)
- article 핵심 주장 수정 (H-D, cross-note consistency rewrite)
- evidence 해석 강도 변화

### 자동 반영 가능
- formatting cleanup (H-F)
- heading 정리, obvious duplication 제거 (H-A, H-B low-risk)
- index refresh, reference 포맷

---

## 5. Merge — 어떻게 반영할까

| 방식 | 적합한 경우 | 예시 |
|------|------------|------|
| **In-place overwrite** | Low-risk, formatting/cleanup | H-A/H-F readability rewrite |
| **New variant** | Semantic change 크거나 human review 필요 | `v2`, `team-share`, `draft` 접미사 파일 생성 |
| **Sidecar note** | 위험한 rewrite를 바로 merge하지 않고 reasoning trail 보존 | `[filename]-rewrite-rationale.md` 생성 |

**Merge 판단 규칙:**
- 위험도 Low → in-place
- 위험도 Medium → variant 생성 후 review
- 위험도 High → sidecar note 먼저, human 승인 후 merge

---

## 6. Observe — rewrite history 기록

루프는 학습 가능한 시스템이어야 한다.
`context/rewrite-log/` 디렉토리에 아래 형식으로 기록한다:

```yaml
# context/rewrite-log/YYYY-MM-DD-[node].md
target_note: ontology/concept/output-assetization.md
date: 2026-04-06
heuristic_trigger: H-E
rewrite_type: evidence-integrating rewrite
auto_or_reviewed: reviewed
accepted: true
rejection_reason: ~
notes: "새 논문 2건 반영, claim 강도 조정"
```

이 기록은 나중에 어떤 heuristic이 실제로 유효했는지, 어떤 rewrite 방식이 자주 실패하는지 분석하게 해준다.

---

## 기존 흐름과의 연결

```
[Top-Down / Bottom-Up 구축]
        ↓
[KB 사용 중 entropy 누적]
        ↓
[Detect] — H-A~H-G heuristic 스캔
        ↓
[Diagnose] — rewrite type 분류
        ↓
[Draft] — controlled rewrite (rationale 포함)
        ↓
[Review] — Low: auto / High: human
        ↓
[Merge] — in-place / variant / sidecar
        ↓
[Observe] — context/rewrite-log/ 기록
        ↓
[다음 루프] — heuristic 정확도 개선
```

evidence-integrating rewrite (H-E)가 발생하면,
Top-Down 흐름의 `evidence 업데이트 → ontology 업데이트` 루프가 다시 트리거될 수 있다.

---

## 최소 실행 버전 (빠른 시작)

처음부터 전체 시스템을 구축할 필요 없다.

1. **Detect**: H-A (너무 긴 문서), H-E (evidence 업데이트 있는데 본문이 낡음), H-F (가독성 낮음) 세 가지만 적용
2. **Rewrite types**: summary rewrite, evidence-integrating rewrite, readability rewrite만 사용
3. **Merge**: Low-risk → in-place, High-risk → variant 생성
4. **Observe**: 로그 없이 시작해도 됨 (나중에 추가)
