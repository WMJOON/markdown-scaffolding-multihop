# core - msm-semantic-search

## 1. Responsibility

`msm-semantic-search` owns the local zvec semantic expansion index for MSM KBs.
It does not replace `rg`, graph traversal, or source validation.

| Stage | Owner |
|-------|-------|
| lexical seed | `rg` / caller |
| semantic expansion | `msm-semantic-search` |
| graph traversal | explorer / graph reasoning |
| source validation | caller + evidence/source refs |

## 2. Default Index

Default path:

```text
<target>/memory/ontology-index/zvec
```

The default path intentionally follows the historical `memory/ontology-index`
layer. Use `--path` when the target path contains spaces or when a shared index
location is preferred.

Schema:

| Field | Type |
|-------|------|
| `text` | string |
| `title` | string |
| `source_path` | string |
| `tags` | string |
| `created_at` | string |
| `chunk_index` | int64 |
| `dense_embedding` | vector fp32, dimension 384 |

## 3. Commands

```bash
scripts/msm-semantic-search init --target REPO
scripts/msm-semantic-search add --target REPO --input ontology --input evidence
scripts/msm-semantic-search search --target REPO "agent friendly website"
scripts/msm-semantic-search link-relations --target REPO --cluster marketing \
  --output evidence/semantic-link/relation_candidates.jsonl
scripts/msm-semantic-search stats --target REPO
```

Common options:

| Option | Meaning |
|--------|---------|
| `--target` | KB root, default `.` |
| `--path` | explicit zvec collection path |
| `--dimension` | vector dimension, default 384 |
| `--embedder hash` | deterministic offline embedder |

## 4. Relation Linking Flow

`link-relations` is a candidate-generation flow for sparse ontology graphs:

```text
entities.jsonl -> entity query -> zvec expansion -> content window scan
  -> directed relation inference -> relation_candidates.jsonl
  -> source validation -> msm-ontology add --relation
```

Inputs:

- entity records from `ontology/Tbox/**/entities.jsonl`,
  `ontology/explain/concept/**/entities.jsonl`, and
  `ontology/system/semantic/**/entities.jsonl`
- an existing zvec index built from ontology/evidence/paper text

Output records are candidates only. They include:

- `source`, `predicate`, `target`
- `confidence` and raw `semantic_score`
- zvec evidence pointer: `source_path`, `chunk_index`, `zvec_doc_id`
- `direction_evidence`, `lexical_cue`, and `match_reason`
- `requires_source_validation: true`

By default, registry files such as `entities.jsonl`, `relations.jsonl`, and
`instances.jsonl` are not accepted as candidate evidence. Use
`--include-registry-evidence` only when auditing registry co-location itself.
`--direction-mode infer` is the default. It reads the local content window
around source/target mentions and prefers directed predicates such as
`implements`, `depends_on`, `enables`, `contains`, `part_of`, `causes`,
`optimizes`, `uses`, or `maps_to`. If no lexical cue is found, the row falls
back to `related_to` and is deduplicated as an undirected review candidate.
Use `--direction-mode directed` (or `--directed`) when the query entity should
always point to the matched target. Use `--direction-mode undirected` for pure
co-mention review queues.

Recommended hand-off:

1. Run `link-relations` into `evidence/semantic-link/relation_candidates.jsonl`.
2. Validate each candidate against source lines or `evidence/seeds.jsonl`.
3. Promote only validated candidates with `msm-ontology add --relation`.

## 5. Operational Rules

- Search output is a candidate set. Do not write ontology from zvec results
  without source validation.
- Relation candidates are not ontology relations. Treat them as review queue
  rows until source validation supplies `evidence:seed:*` refs.
- If the index is missing or stale, continue with lexical seed results and
  record `semantic_expansion_skipped` in the response or trajectory.
- Re-run `add` after bulk KB updates. Upsert semantics make repeated ingestion
  safe.
- Keep generated index files out of ontology/evidence source-of-truth paths.
