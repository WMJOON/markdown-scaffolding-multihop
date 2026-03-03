# Module: Crawl (Step B)

원문(raw) 보존 크롤링. curl + pandoc HTML→GFM 변환. LLM 호출 금지.

## 동작

1. intake_manifest에서 active URL 목록 로드
2. `curl -L --compressed` 로 HTML 페치
3. `pandoc --from html --to gfm` 으로 Markdown 변환
4. `clean_markdown()` — 이미지/analytics/잔여 HTML 태그 제거
5. 최소 인덱스 추출: title, headings, doc_type, length, outbound_links

## 로컬 파일 처리

`file://` URL(local/directory 모드)은 `shutil.copy2`로 raw/에 복사.

## Skip 조건

- `--mode local`: skip (파일이 이미 로컬)
- `--mode enrich`: skip

## 기존 도구 재사용

`collect_case_study_raw_data.py`의 `fetch_html()`, `pandoc_to_markdown()`, `clean_markdown()` 직접 import.

## 산출물

- `evidence_corpus/raw/{doc_id}.md`
- `evidence_corpus/raw/{doc_id}.html`
- `evidence_corpus/index/{doc_id}.yaml`
- `evidence_corpus/index/doc_index.jsonl`
