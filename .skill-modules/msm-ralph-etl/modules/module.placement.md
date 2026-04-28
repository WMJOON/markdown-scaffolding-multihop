# Module: Placement (Step E)

3-tier 유사도 기반 그래프 위치 판정. LLM 자동 병합 금지.

## 3-Tier Similarity

### Tier 1 — Lexical (항상 사용)
- **Normalized Levenshtein** — entity_id, label_en, label_ko, aliases 간 최대값
- 대소문자 무시, 공백/언더스코어 정규화

### Tier 2 — Sparse Semantic (stdlib fallback)
- **TF-IDF cosine** — char 3-gram + word unigram
- 코퍼스: 기존 엔티티 summary + 후보 텍스트로 fit

### Tier 3 — Dense Semantic (opt-in)
- **BERT** — subprocess `bert_embed_worker.py` 호출
- Apple Silicon MPS GPU 자동 감지
- 모델: `all-MiniLM-L6-v2` (384d) / `bge-base-en-v1.5` (768d)

## 판정 규칙

| Condition | Label | Note |
|-----------|-------|------|
| evidence = 0 | REJECT | 근거 없음 |
| alias_sim >= 0.92 & same type | MERGE_CANDIDATE | 자동 확정 금지 |
| alias_sim >= 0.80 | EXTEND | 기존 노드 확장 |
| embed_sim >= 0.75 & alias < 0.80 | RELATION_ONLY | 관계만 추가 |
| close_matches > 1 | HOLD | 모호 — 사람 판단 |
| else | NEW | 신규 엔티티 |

## CLI 옵션

```
--embed-mode auto   # BERT available → BERT, else TF-IDF (default)
--embed-mode bert   # BERT 강제
--embed-mode tfidf  # TF-IDF만
--bert-model BAAI/bge-base-en-v1.5  # 모델 지정
```

## 산출물

- `placement_report.jsonl`
- `hold_registry.yaml` (hold 존재 시)
