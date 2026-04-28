# Module: Workflow Design & Termination Rules

Ralph형 업무를 수행할 때 Claude가 따라야 하는 워크플로우 설계 프로토콜.
단순히 CLI를 실행하는 것이 아니라, **설계 → 실행 → 판단 → 종료** 루프를 매 run마다 수행한다.

---

## 1. 워크플로우 3-Phase 구조

```
┌─────────────────────────────────────────────────────┐
│ Phase 0: DESIGN (실행 전 — 반드시 선행)               │
│   scope 확정 → 모드 선택 → 종료 기준 합의            │
├─────────────────────────────────────────────────────┤
│ Phase 1: EXECUTE (파이프라인 실행)                    │
│   A→B→C→D→E→F 상태 머신 진행                        │
│   매 step 후 gate check                             │
├─────────────────────────────────────────────────────┤
│ Phase 2: EVALUATE (실행 후 — 종료 판정)               │
│   acceptance criteria 검증 → 종료 or 재실행 결정      │
└─────────────────────────────────────────────────────┘
```

---

## 2. Phase 0: DESIGN (실행 전 필수)

Ralph 파이프라인을 실행하기 전에 다음 5개 항목을 확정해야 한다.
**사용자에게 확인받지 않으면 실행하지 않는다.**

### 2.1 Scope Definition (무엇을)

```yaml
design:
  input_source: <manifest_path | input_dir | url_list>
  input_format: <tsv | jsonl | directory>
  scope_targets: [CaseStudy, Model, ...]   # 추출할 entity type
  batch_size: <N>                           # 한 번에 처리할 건수
```

질문 템플릿:
> "어떤 소스에서 어떤 entity type을 추출할까요? (예: 논문 폴더에서 Model만, TSV에서 CaseStudy+Work)"

### 2.2 Mode Selection (어떻게)

| 사용자 의도 | 모드 | 스킵 단계 |
|------------|------|----------|
| 새 URL에서 엔티티 수집 | `full` | 없음 |
| 이미 받은 파일 처리 | `local` | B_CRAWL |
| 기존 엔티티에 관계만 추가 | `enrich` | B_CRAWL, C_PREPROCESS |

### 2.3 Similarity Strategy (무엇으로 비교)

| 상황 | embed_mode | 근거 |
|------|-----------|------|
| 빠른 탐색 / 외부 패키지 없음 | `tfidf` | 가벼움, 대략적 판별 |
| 정확한 의미 비교 필요 | `bert` | dense embedding, MPS GPU |
| 판단 위임 | `auto` | torch 있으면 BERT, 없으면 TF-IDF |

### 2.4 Termination Criteria (언제 끝나는가)

**실행 전에 종료 기준을 명시적으로 합의한다.** 기본값:

```yaml
termination:
  # --- Hard Stop (하나라도 위반 시 즉시 종료) ---
  max_runs: 3                          # 동일 scope 최대 반복 횟수
  max_total_candidates: 500            # 누적 entity 후보 상한
  seal_blocked_consecutive: 2          # 연속 SEAL_BLOCKED 2회 → 중단

  # --- Success Exit (모두 충족 시 정상 종료) ---
  seal_passed: true                    # V1-V8 전체 통과
  hold_count: 0                        # 미해소 hold 0건
  new_entity_ratio_min: 0.0            # 신규 엔티티 비율 하한 (0 = 0건도 OK)

  # --- Diminishing Returns (점진적 수확 체감) ---
  new_entity_delta_min: 1              # 직전 run 대비 신규 엔티티 증분이 이 이하면 종료
```

### 2.5 Output Contract (무엇을 남기는가)

```yaml
outputs:
  run_report: true                     # 항상
  seed_candidate: true                 # seal 통과 시
  entity_files: <apply 여부>            # --apply 시에만
  cost_report: true                    # 항상
```

---

## 3. Phase 1: EXECUTE (단계별 gate 판단)

### 3.1 Step 실행 + Gate Check 루프

```
for step in [A, B, C, D, E, F]:
    if step in skip_steps(mode):
        log "skipped"
        continue

    result = execute_step(step)

    if result == FAILED and retries >= max_retry:
        → TERMINATE(reason="step_failed", step=step)

    gate = check_gates(state)
    if gate == H1:
        → PAUSE + 사용자에게 보고
        → 사용자 승인 후 계속 or TERMINATE
    if gate == H2:
        → PAUSE + topology 변경 제안
        → 사용자 승인 필수 (자동 진행 금지)
```

### 3.2 Step 간 중간 판단 (Claude가 수행)

각 step 완료 후 Claude는 다음을 확인한다:

| After Step | Check | Action |
|------------|-------|--------|
| A_INTAKE | active 건수 = 0? | → TERMINATE("no active entries") |
| B_CRAWL | 성공률 < 50%? | → PAUSE + 사용자에게 URL 품질 경고 |
| C_PREPROCESS | chunks = 0? | → TERMINATE("no chunks produced") |
| D_PARSE | candidates = 0? | → TERMINATE("no candidates found") |
| E_PLACE | hold_ratio > 50%? | → H1 gate (과도한 모호성) |
| E_PLACE | 100% reject? | → TERMINATE("all candidates rejected") |
| F_SEAL | SEAL_BLOCKED? | → 원인 분석 후 사용자에게 보고 |

---

## 4. Phase 2: EVALUATE (종료 판정)

### 4.1 Single-run 종료 판정

하나의 `ralph_cli.py run` 완료 후:

```
if state.status == "DONE":
    if seal_passed AND hold_count == 0:
        → EXIT_SUCCESS
    elif seal_passed AND hold_count > 0:
        → 사용자에게 hold 목록 제시 + 해소 여부 질문
    else:
        → EXIT_WITH_WARNINGS (V5, V6 warning만 있는 경우)

if state.status == "RUN_FAILED":
    → 실패 원인 분석 + 사용자에게 보고
    → 재시도 가능 여부 판단
```

### 4.2 Multi-run 반복 판정 (핵심)

동일 scope에서 여러 배치를 처리할 때 — 반복 종료 기준:

```python
def should_continue(history: list[RunResult], criteria: TerminationCriteria) -> bool:
    # Hard Stop
    if len(history) >= criteria.max_runs:
        return False  # "최대 반복 횟수 도달"

    total_candidates = sum(r.candidates for r in history)
    if total_candidates >= criteria.max_total_candidates:
        return False  # "누적 후보 상한 초과"

    consecutive_blocked = 0
    for r in reversed(history):
        if r.seal_blocked:
            consecutive_blocked += 1
        else:
            break
    if consecutive_blocked >= criteria.seal_blocked_consecutive:
        return False  # "연속 SEAL_BLOCKED"

    # Diminishing Returns
    if len(history) >= 2:
        prev_new = history[-2].new_entities
        curr_new = history[-1].new_entities
        delta = curr_new - prev_new
        if delta <= criteria.new_entity_delta_min:
            return False  # "수확 체감 — 신규 엔티티 증분 부족"

    # Success Exit
    latest = history[-1]
    if latest.seal_passed and latest.hold_count == 0:
        return False  # "완전 성공 — 추가 실행 불필요"

    return True  # 다음 배치 진행
```

### 4.3 종료 시 필수 산출물

어떤 경로로 종료하든 Claude는 다음을 반드시 보고한다:

```markdown
## Ralph ETL 실행 결과

| 항목 | 값 |
|------|-----|
| Run ID | R-20260303-NNNN |
| 종료 사유 | <success / seal_blocked / max_runs / diminishing_returns / ...> |
| 처리 문서 | N건 |
| Entity 후보 | N건 (new: N, extend: N, merge: N, hold: N, reject: N) |
| Seal 결과 | PASSED / BLOCKED (V1: ..., V7: ...) |
| HITL 이벤트 | N건 |
| 다음 액션 | <없음 / hold 해소 필요 / 추가 배치 권장 / ...> |
```

---

## 5. 종료 유형 정리

| 종료 유형 | 조건 | Claude 행동 |
|-----------|------|------------|
| **EXIT_SUCCESS** | seal 통과 + hold 0 | 결과 보고 + "완료" 선언 |
| **EXIT_WITH_WARNINGS** | seal 통과 + V5/V6 warning | 결과 보고 + warning 목록 제시 |
| **EXIT_HOLD_PENDING** | seal 통과 + hold > 0 | hold 목록 제시 + 해소 방법 제안 |
| **EXIT_SEAL_BLOCKED** | V1-V4/V7/V8 실패 | 차단 원인 분석 + 수정 방안 제안 |
| **EXIT_DIMINISHING** | 신규 엔티티 증분 <= threshold | "수확 체감" 보고 + 종료 권고 |
| **EXIT_MAX_RUNS** | 반복 횟수 상한 도달 | 누적 결과 요약 + 종료 |
| **EXIT_STEP_FAILED** | step 실패 + retry 소진 | 실패 원인 + 재시도 가능 여부 |
| **EXIT_HITL_REJECTED** | H1/H2 gate에서 사용자 거부 | 거부 사유 기록 + 종료 |
| **EXIT_NO_INPUT** | active entries = 0 | "처리할 입력 없음" |

---

## 6. Claude 판단 규칙 (시스템 프롬프트용)

Ralph형 업무 수행 시 Claude는 다음 규칙을 따른다:

1. **실행 전 반드시 설계한다.** scope, mode, similarity, termination criteria를 사용자와 합의하지 않으면 CLI를 실행하지 않는다.
2. **dry-run을 먼저 실행한다.** `--apply` 없이 한 번 돌려서 결과를 확인한 후, 사용자 승인을 받고 `--apply`를 실행한다.
3. **매 step 후 gate를 평가한다.** gate가 트리거되면 자동으로 다음 step으로 넘어가지 않고 사용자에게 보고한다.
4. **종료 기준을 준수한다.** diminishing returns 감지 시 무한 반복하지 않고 종료를 권고한다.
5. **결과를 구조적으로 보고한다.** 자연어 요약이 아니라 표 형식으로 placement 분포, validation 결과, 다음 액션을 제시한다.
6. **hold는 사용자 판단이다.** hold 엔티티를 자동으로 merge/reject 하지 않고, 선택지를 제시한다.
7. **topology 변경은 H2 gate다.** 새 entity type이나 relation type이 필요하다고 판단되면 자동 생성하지 않고 H2 gate로 에스컬레이션한다.
