# Module: Preprocess (Step C)

헤딩 경계 기반 청킹 엔진. 증거 단위(chunk) 생성. LLM 호출 0.

## 청킹 사양

| Parameter | Default | Description |
|-----------|---------|-------------|
| chunk_max_words | 400 | chunk당 최대 단어 수 |
| chunk_overlap_words | 50 | 인접 chunk 간 오버랩 |
| chunk_min_words | 40 | 이하면 이전 chunk에 병합 |
| metadata_prefix | true | `[doc_type \| section_path]` 접두사 |

## 알고리즘

1. H1-H3 헤딩 경계로 Section 분할
2. Section별 word-count 기반 슬라이딩 윈도우 청킹
3. 잔여 fragment가 min_words 미만이면 이전 chunk에 병합
4. 메타데이터 접두사 부착: `[paper | 3. Methods > 3.2 Model]`
5. chunk_id = sha256(doc_id + section_path + chunk_idx)[:16]

## Skip 조건

- `--mode enrich`: skip

## 산출물

- `evidence_corpus/chunks/all_chunks.jsonl`
