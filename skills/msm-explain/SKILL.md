---
name: msm-explain
version: "0.13.4"
description: |
  MSM explain projection layer. record-archive snapshots and ontology semantics
  are rendered into human-readable Markdown/Base generated artifacts.
---

# msm-explain (v0.13.4)

## What

`record-archive/` snapshots and `ontology/` semantics are rendered into
human-readable Markdown + Base-compatible JSON.

모든 출력은 자동 생성 artifact이므로 직접 편집하지 않는다.

책임:
1. **read-snapshot**: DuckDB로 parquet snapshot 로드
2. **render-md**: Jinja2 템플릿으로 MD 파일 생성
3. **render-base**: Base-compatible JSON 생성
4. **artifact-mark**: `<!-- msm:generated -->` marker 부착

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — run | `scripts/msm-explain run --target REPO [--domain NAME] [--apply]` |
| CLI — list | `scripts/msm-explain list --target REPO` |
| Harness | `harness/run.sh --skill msm-explain --tier L0 --mode validate-only --target REPO` |

## Triggers

- "msm-explain"
- "explain projection"
- "Markdown projection"
- "instance snapshot"
- ".base 생성"

## Dependencies

- Python 3.10+
- `duckdb>=0.9` (parquet read)
- `jinja2>=3.0` (template render)
- SQLite 3.35+ (built-in)

## Non-Goals

- record mutation → `msm-record-archive`
- evidence 수집 → `msm-evidence`
- entity/relation 생성 → `msm-ontology`
