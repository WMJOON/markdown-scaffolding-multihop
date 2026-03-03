# Module: Intake (Step A)

URL/파일 정규화, 중복 제거, 배치 생성. LLM 호출 금지.

## 입력 포맷

| Format | Option | Structure |
|--------|--------|-----------|
| TSV | `--manifest data.tsv` | case_id, source_type, industry_mapping, title, url, start_marker |
| JSONL | `--manifest src.jsonl` | `{"url":"...","title":"...","source_type":"...","tags":[...]}` |
| Directory | `--input-dir ./docs/` | .md/.txt/.html 자동 스캔 |

## URL 정규화 규칙

1. scheme → https
2. trailing slash 제거
3. tracking params 제거 (utm_*, fbclid, gclid 등)
4. fragment 제거 (start_marker가 fragment면 보존)
5. `sha256(normalized_url)` → url_fingerprint
6. 동일 fingerprint 재수집: 30일 이상 → 업데이트 후보

## 산출물

- `intake_manifest.yaml`
- `.run_meta.json` (run_mode, input_format, scope_targets)
