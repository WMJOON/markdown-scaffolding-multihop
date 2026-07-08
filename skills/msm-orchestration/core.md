# core — msm-orchestration

## 1. 4가지 책임

| 영역 | 모듈 |
|------|------|
| 라우터 (의도 → workflow) | `router/match_trigger.py`, `router/resolve_workflow.py`, `router/dispatch.py` |
| CC 계약 강제 | `policy/cc_check.py` |
| 5-axis gate 판정 | `policy/gate_evaluator.py`, `policy/threshold_resolver.py` |
| HITL 2-layer | `policy/hitl_router.py`, `hooks/pretool_use.py` |

## 1.1 KB 탐색 레일

MSM에서 KB 탐색은 기본적으로 `rg → zvec → graph → source` 순서를 따른다.

| 단계 | 목적 | 종료 조건 |
|------|------|-----------|
| `rg` lexical seed | 정확한 표면어, ID, 파일 경로, source anchor 발견 | seed 문서/후보 질의 확보 |
| `zvec` semantic expansion | 표면어가 다른 인접 개념·사례·근거 확장 | 유사 후보를 충분히 모음 |
| graph traversal | wikilink/RDF/JSONL 관계로 N-hop 연결 확인 | 후보 간 구조적 관계 확인 |
| source validation | 원문 라인, `evidence/seeds.jsonl`, `source_refs` 검증 | 답변·ontology 변경에 쓸 근거 확정 |

라우팅 규칙:
- 개념 탐색, KB 질의, ontology 후보 생성, drift/orphan 분석, 리포트 합성은 zvec 확장을 포함한다.
- exact string/ID 조회, 파일 존재 확인, 특정 라인 검증은 `rg` 단독을 허용한다.
- zvec index가 없거나 stale이면 `rg` seed 결과로 진행하되, 응답/trajectory에 `semantic_expansion_skipped`와 사유를 남긴다.
- zvec 결과는 후보일 뿐이며, 정본 변경은 반드시 source validation 이후에만 수행한다.

### 1.1.1 관계 연결 후보 레일

관계가 비어 있거나 `no_incoming_relation`이 많은 KB에서는 semantic expansion을 relation 후보 생성에도 쓴다.

```text
entities.jsonl -> zvec expansion -> content window scan
  -> evidence/semantic-link/relation_candidates.jsonl
  -> source validation -> msm-ontology add --relation
```

규칙:
- `msm-semantic-search link-relations`는 후보만 만든다. `relations.jsonl` 정본에 직접 쓰지 않는다.
- 후보는 `source_path`, `chunk_index`, `zvec_doc_id`, `semantic_score`, `matched_terms`, `direction_evidence`를 보유해야 한다.
- chunk의 lexical direction cue가 충분하면 `implements`/`depends_on`/`enables`/`part_of` 같은 directed predicate를 우선 제안한다. cue가 약하면 `related_to` 후보로 낮춘다.
- `source_refs`가 비어 있는 후보는 반드시 `requires_source_validation=true` 상태로 둔다.
- `msm-ontology add --relation --apply`는 검증된 `evidence:seed:*`가 붙은 뒤에만 호출한다.

## 2. 측정 vs 정책 분리

`msm-harness`는 `governance_measurement`를 emit, 본 스킬은 그 결과를 소비해 `gate_decision`을 emit.
두 이벤트는 다른 파일에 기록 (정합성 보장):

- harness: `harness/trajectory/run-<id>.jsonl`
- orchestration: `harness/trajectory/run-<id>.orchestration.jsonl`

본 스킬 trajectory에만 등장하는 필드: `gate_passed`, `next_action`, `routing_decision`, `cc_violation`, `deprecated_route`, `hooks_disabled`.

## 3. CLI

```bash
# 사용자 의도 → workflow 라우팅 + 실행
router/dispatch.py --intent "evidence 수집" --target REPO

# 직접 workflow 호출
router/dispatch.py --workflow agent-context/workflow/evidence/evidence-collection.abox.ttl --target REPO

# harness가 남긴 measurement 소비 → gate_decision 기록
policy/gate_evaluator.py --target REPO --run-id RUN_ID

# CC 계약 검증
policy/cc_check.py --target REPO
```

## 4. Exit Code 도메인 (caller-facing)

| 코드 | 의미 |
|------|------|
| 0 | 정상 + gate passed |
| 1 | CC 위반 |
| 100 | HITL pending (사용자 ack 필요) |
| 101 | gate fail, retry 불가 |
| 102 | v1-strict 모드에서 legacy 라우팅 거부 |

harness가 던지는 0/1/2/64-79와 orchestration이 던지는 100번대는 분리된 도메인.

## 5. Threshold 해결 순서

1. workflow_id override (`overrides.by_workflow_id.<id>`)
2. category override (`overrides.by_category.<category>`)
3. defaults

먼저 매칭되는 값이 그대로 적용. 다중 매칭 시 우선순위 1번이 이김.

## 6. HITL 2-layer

### Layer 1 — always_hitl
측정값과 무관하게 차단되는 단계 (예: canonical_root_hub locked 변경, dependency 변경).
이벤트: `hitl_request` + 종료코드 100.

### Layer 2 — observability-triggered
threshold 위반 시 자동 escalate. 트리거 매트릭스:

| 축 | 위반 | 트리거 reason |
|----|------|---------------|
| non-determinism | value > max | `non_determinism_high` |
| oracle | score < min | `oracle_below_threshold` |
| cost | budget breach | `cost_budget_exceeded` |
| trajectory | incomplete | `trajectory_incomplete` |

## 7. Migration mode

`pack_config.migration.mode`:

| 모드 | 동작 |
|------|------|
| compatibility | legacy 별칭 허용 + `deprecated_route` 이벤트 |
| strict-soft | legacy 허용 + warn 로그 |
| v1-strict | legacy 거부, 종료코드 102 |

## 8. PreToolUse Hook

stdin으로 PreToolUse payload 수신. always_hitl 패턴 매칭 시 stderr에 reason 출력 + exit 1로 차단.
환경변수 `MSM_HOOKS_DISABLED=1`로 우회 가능 (trajectory에 `hooks_disabled` 기록).

hook은 정책 판정의 adapter일 뿐 worklog 생성기나 hand-off 저장소가 아니다. Claude/Codex/Antigravity 등
provider별 adapter는 분리하고, 정책 로직은 `policy/`와 `references/hitl-policy.yaml`에 둔다.
Codex cloud 같은 ephemeral runtime에서는 hook side effect를 다음 에이전트 기억 보장으로 보지 않는다.
MSO v0.6.3의 Stop reminder throttle은 사용자에게 보이는 Stop reminder adapter에만 적용한다.
`PreToolUse`는 정책 차단/허용 adapter이므로 `stop-check.sh` 대상이 아니다.
