---
name: msm-semantic-search
version: "0.1.0"
description: |
  MSM KB semantic expansion layer. Build and query a local zvec index from
  Markdown/text/json/jsonl notes so MSM exploration can run rg lexical seed
  followed by zvec semantic expansion before source validation.
---

# msm-semantic-search

## What

Local semantic lookup and relation-candidate linking for MSM repositories.

This skill is the operational bridge between exact `rg` lookup and graph/source
validation:

```
rg lexical seed -> zvec semantic expansion -> graph traversal -> source validation
```

For sparse ontology graphs, `link-relations` reads the expanded content window
around entity mentions and proposes directed relation candidates before
`msm-ontology` promotion.

The default embedder is deterministic hash embedding, so bootstrap works
offline and does not download models. Higher-quality embedders can replace this
later without changing the command surface.

Details: [core.md](core.md).

## Entry Points

| Entry | Command |
|-------|---------|
| init | `scripts/msm-semantic-search init --target REPO` |
| add | `scripts/msm-semantic-search add --target REPO --input ontology --input evidence` |
| search | `scripts/msm-semantic-search search --target REPO "query text"` |
| link-relations | `scripts/msm-semantic-search link-relations --target REPO --cluster CLUSTER --output evidence/semantic-link/relation_candidates.jsonl` |
| stats | `scripts/msm-semantic-search stats --target REPO` |

## Triggers

- "semantic search", "zvec", "유사도검색", "의미 확장"
- "관련 노트 찾아줘", "인접 개념 확장", "KB에서 비슷한 근거"
- "관계 연결", "relation 후보", "semantic relation linking"

## Dependencies

- Python 3.10+
- `zvec>=0.2`

## Non-Goals

- Final evidence judgment. Search results are candidates only.
- Ontology writes. Use `msm-ontology` after source validation.
- Graph traversal. Use explorer / graph reasoning after semantic expansion.
