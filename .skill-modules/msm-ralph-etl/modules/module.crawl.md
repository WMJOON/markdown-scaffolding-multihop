# Module: Crawl (Step B)

원문(raw) 보존 크롤링. LLM 호출 금지.

## URL 종류별 처리 경로

### HTML (기본)
1. intake_manifest에서 active URL 목록 로드
2. Scrapling으로 HTML 페치
3. `pandoc --from html --to gfm` 으로 Markdown 변환
4. `clean_markdown()` — 잔여 HTML 태그 제거
5. 최소 인덱스 추출: title, headings, doc_type, length, outbound_links

### PDF (`step_pdf.py`)
1. `is_pdf_url()` 로 PDF 판정 (URL 패턴 + `.pdf` 확장자)
2. `download_pdf()` 로 바이너리 다운로드 → magic bytes(`%PDF`) 검증
3. 변환 우선순위:
   - **opendataloader-pdf** (Java 11+ 필요): `pip install opendataloader-pdf`
   - **pymupdf4llm** (순수 Python fallback): `pip install pymupdf4llm`
4. `build_pdf_md()` — frontmatter만 붙이고 **본문은 그대로 저장** (`clean_markdown()` 우회)

원문 보존 원칙: PDF 변환 출력에 추가 가공 없음. 페이지 구분자 등 변환기 출력을 그대로 유지.

## 로컬 파일 처리

`file://` URL(local/directory 모드)은 `shutil.copy2`로 raw/에 복사.  
local 모드의 `.pdf` 파일은 PDF 처리 경로로 자동 라우팅.

## Skip 조건

- `--mode local`: skip HTML 크롤 (파일이 이미 로컬)
- `--mode enrich`: skip
- PDF 변환 라이브러리 미설치: 경고 출력 후 해당 항목 skip (파이프라인 중단 없음)

## 산출물

- `evidence_corpus/raw/{doc_id}.md`   — 변환된 Markdown (HTML/PDF 공통)
- `evidence_corpus/raw/{doc_id}.html` — HTML 원본 (HTML URL만)
- `evidence_corpus/raw/{doc_id}.pdf`  — PDF 원본 (PDF URL만)
- `evidence_corpus/index/{doc_id}.yaml`
- `evidence_corpus/index/doc_index.jsonl`
