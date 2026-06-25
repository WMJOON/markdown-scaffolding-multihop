# 스킬 구성 (v0.13.4)

MSM v0.13.4는 `msm-orchestration`을 진입점으로 사용한다. 실행 정본은 `agent-context/workflow/**/*.abox.ttl`이며, YAML은 편집·마이그레이션 레이어다.

---

## Canonical Skills

| 스킬 | 책임 |
|------|------|
| `msm-repository-setup` | 신규 KB를 `ontology/`, `evidence/`, `record-archive/`, `agent-context/`, `harness/` 구조로 부트스트랩 |
| `msm-evidence` | URL/로컬 MD/Graphify 산출물을 `evidence/seeds.jsonl`, `evidence/md/`, `evidence/graphify/`로 수집 |
| `msm-ontology` | entity/relation 생성, MECE 검증, `ontology/explain/` 승격, `ontology/system/**/*.ttl` formal graph/PROV-O projection |
| `msm-record-archive` | `record-archive/` runtime DB, append-only event, derived record, snapshot 관리 |
| `msm-explain` | `record-archive/snapshots/`를 `ontology/explain/` Markdown/Base generated artifact로 렌더링 |
| `msm-maintain` | orphan/drift/parent-alignment scan, rewrite, 상태 리포트 |
| `msm-harness` | memory 2-tier, L0~L3 런타임, 5-Axis 계측 |
| `msm-orchestration` | 자연어 intent → workflow TTL 라우팅, CC 계약, HITL 정책 |

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
| `msm-ontology` | [SKILL.md](../skills/msm-ontology/SKILL.md) | [core.md](../skills/msm-ontology/core.md) |
| `msm-record-archive` | [SKILL.md](../skills/msm-record-archive/SKILL.md) | [core.md](../skills/msm-record-archive/core.md) |
| `msm-explain` | [SKILL.md](../skills/msm-explain/SKILL.md) | [core.md](../skills/msm-explain/core.md) |
| `msm-maintain` | [SKILL.md](../skills/msm-maintain/SKILL.md) | [core.md](../skills/msm-maintain/core.md) |
| `msm-harness` | [SKILL.md](../skills/msm-harness/SKILL.md) | [references/tier-contract.md](../skills/msm-harness/references/tier-contract.md) |
| `msm-orchestration` | [SKILL.md](../skills/msm-orchestration/SKILL.md) | [references/router-trigger-map.yaml](../skills/msm-orchestration/references/router-trigger-map.yaml) |

> 예정: `msm-graph-reasoning` (multi-hop·BFS·GraphRAG·RDF/OWL), `msm-semantic-search` (zvec·RRF)
