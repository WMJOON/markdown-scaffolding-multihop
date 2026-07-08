# 스킬 구성 (v0.14.0)

MSM v0.14.0는 `msm-orchestration`을 진입점으로 사용한다. 실행 정본은 `agent-context/workflow/**/*.abox.ttl`이며, YAML은 편집·마이그레이션 레이어다.
worklog는 workflow TTL node/run context가 명시된 실행 기록으로만 쓰고, hook side effect를 hand-off 보장으로 보지 않는다. MSO v0.6.3 Stop reminder throttle은 사용자 reminder adapter에만 적용하며, MSM `PreToolUse` 정책 hook에는 적용하지 않는다.

---

## Canonical Skills

| 스킬 | 책임 |
|------|------|
| `msm-repository-setup` | 신규 KB를 `ontology/`, `evidence/`, `record-archive/`, `agent-context/`, `harness/` 구조로 부트스트랩 |
| `msm-evidence` | URL/로컬 MD/Graphify 산출물을 `evidence/seeds.jsonl`, `evidence/md/`, `evidence/graphify/`로 적재 |
| `msm-ontology` | entity/relation 생성, MECE 검증, `ontology/explain/` 승격, `ontology/system/**/*.ttl` formal graph/PROV-O projection |
| `msm-record-archive` | `record-archive/` runtime DB, append-only event, derived record, snapshot 관리 |
| `msm-explain` | `record-archive/snapshots/`를 `ontology/explain/` Markdown/Base generated artifact로 렌더링 |
| `msm-maintain` | orphan/drift/parent-alignment scan, rewrite, 상태 리포트 |
| `msm-semantic-search` | zvec 기반 semantic expansion index. `rg` seed 이후 인접 개념·근거 후보 확장, relation 후보 연결 |
| `msm-harness` | memory 2-tier, L0~L3 런타임, 5-Axis 계측 |
| `msm-orchestration` | 자연어 intent → workflow TTL 라우팅, CC 계약, HITL 정책 |

KB 탐색성 작업은 모든 canonical skill에서 동일한 기본 레일을 따른다: `rg`로 seed를 잡고, `zvec`으로 의미상 인접 후보를 확장한 뒤, graph 관계와 원문 근거로 검증한다. exact ID/문자열 조회만 `rg` 단독을 허용한다.
relation이 희박한 KB는 `msm-semantic-search link-relations`로 `evidence/semantic-link/relation_candidates.jsonl` 후보를 만든 뒤, source validation을 거쳐 `msm-ontology add --relation`으로 승격한다.
predicate 의미와 risk tier는 [Semantic Relations](semantic-relations.md)를 따른다. KB 구축은 원문/candidate를 먼저 Load하고 검증 뒤 Transform/Promote하는 ELT 흐름으로 운용한다.

## Legacy Aliases

| Legacy | Canonical | 비고 |
|--------|-----------|------|
| `msm-instance` | `msm-record-archive` | 기존 `instance/runtime.db`, `instance/snapshots/` 워크플로우 호환 |
| `msm-obsidian-projection` | `msm-explain` | 기존 Obsidian projection 명칭 호환 |

신규 문서와 workflow는 legacy alias 대신 canonical 스킬명을 사용한다.

---

## 주요 명령

```bash
# 새 KB 부트스트랩
skills/msm-repository-setup/scripts/msm init \
  --target my-kb --domain ai_agent --apply --yes

# evidence 수집
skills/msm-evidence/scripts/msm-evidence collect \
  --target my-kb --source https://example.com/paper --apply

# record archive 초기화
skills/msm-record-archive/scripts/msm-record-archive init \
  --target my-kb --apply

# snapshot projection
skills/msm-explain/scripts/msm-explain run \
  --target my-kb --domain instance --apply

# 자연어 라우팅
skills/msm-orchestration/msm-orchestrate run \
  --intent "evidence 수집 후 ontology 반영해줘" \
  --target my-kb --tier L0 --mode dry-run
```

---

## 스킬 레퍼런스

| 스킬 | SKILL.md | 주요 참조 |
|------|---------|---------|
| `msm-repository-setup` | [SKILL.md](../skills/msm-repository-setup/SKILL.md) | [scaffold-tree.md](../skills/msm-repository-setup/references/scaffold-tree.md) |
| `msm-evidence` | [SKILL.md](../skills/msm-evidence/SKILL.md) | [core.md](../skills/msm-evidence/core.md) |
| `msm-ontology` | [SKILL.md](../skills/msm-ontology/SKILL.md) | [references/core.md](../skills/msm-ontology/references/core.md) |
| `msm-record-archive` | [SKILL.md](../skills/msm-record-archive/SKILL.md) | [core.md](../skills/msm-record-archive/core.md) |
| `msm-explain` | [SKILL.md](../skills/msm-explain/SKILL.md) | [core.md](../skills/msm-explain/core.md) |
| `msm-maintain` | [SKILL.md](../skills/msm-maintain/SKILL.md) | [core.md](../skills/msm-maintain/core.md) |
| `msm-semantic-search` | [SKILL.md](../skills/msm-semantic-search/SKILL.md) | [core.md](../skills/msm-semantic-search/core.md) |
| `msm-harness` | [SKILL.md](../skills/msm-harness/SKILL.md) | [references/tier-contract.md](../skills/msm-harness/references/tier-contract.md) |
| `msm-orchestration` | [SKILL.md](../skills/msm-orchestration/SKILL.md) | [references/router-trigger-map.yaml](../skills/msm-orchestration/references/router-trigger-map.yaml) |

> 예정: `msm-graph-reasoning` (multi-hop·BFS·GraphRAG·RDF/OWL). `msm-semantic-search`는 v0.1 wrapper로 먼저 제공하며, 추후 dense/local/openai/qwen embedder와 RRF hybrid search를 확장한다.
