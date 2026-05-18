# Ralph ETL — Core Architecture

## 파이프라인 상태 머신

```
RUN_CREATED → A_INTAKE → B_CRAWL → C_PREPROCESS → D_PARSE → E_PLACE → F_SEAL → DONE
                 │           │            │
              (always)   (skip: local,  (skip: enrich)
                          enrich)
```

## 3-Tier Similarity Engine

| Tier | Engine | Dependency | Use |
|------|--------|-----------|-----|
| 1 | Levenshtein | stdlib | alias_sim — merge/extend 1차 필터 |
| 2 | TF-IDF cosine | stdlib | embed_sim fallback — char 3-gram + word unigram |
| 3 | BERT (MPS) | torch + transformers | dense embedding — subprocess worker |

## Placement 판정 트리

```
evidence = 0        → REJECT
alias_sim >= 0.92   → MERGE_CANDIDATE
alias_sim >= 0.80   → EXTEND
embed_sim >= 0.75   → RELATION_ONLY
ambiguity > thresh  → HOLD
else                → NEW
```

## 멱등성 보장

```
idempotency_key = sha256(batch_id + step + input_snapshot_hash + config_hash)
```

동일 키로 재실행 시 산출물을 덮어쓰지 않고 재사용.
