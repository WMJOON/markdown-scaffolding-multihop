---
name: msm-obsidian-projection
version: "0.12.0"
description: |
  MSM v1.2.0 — DuckDB → Obsidian MD + .base 생성 스킬.
  explain layer. 모든 출력 파일은 generated artifact — 직접 편집 금지.
triggers:
  - "obsidian projection 생성"
  - "DuckDB → Obsidian"
  - "msm-obsidian-projection run"
  - ".base 생성"
  - "KB projection"
  - "obsidian projection"
---

# msm-obsidian-projection (v1.2.0)

## What

DuckDB parquet snapshot을 읽어서 Obsidian 호환 Markdown + Bases 플러그인 JSON을 생성하는 Explain Layer.

모든 출력은 자동 생성 artifact이므로 직접 편집하지 않는다.

책임:
1. **read-snapshot**: DuckDB로 parquet snapshot 로드
2. **render-md**: Jinja2 템플릿으로 MD 파일 생성
3. **render-base**: Obsidian Bases 호환 JSON 생성
4. **artifact-mark**: `<!-- msm:generated -->` marker 부착

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — run | `scripts/msm-obsidian-projection run --target REPO [--domain NAME] [--apply]` |
| CLI — list | `scripts/msm-obsidian-projection list --target REPO` |
| Harness | `harness/run.sh --skill msm-obsidian-projection --tier L0 --mode validate-only --target REPO` |

## Triggers

- "obsidian projection", "DuckDB → Obsidian", "msm-obsidian-projection run"
- ".base 생성", "KB projection"

## Dependencies

- Python 3.10+
- `duckdb>=0.9` (parquet read)
- `jinja2>=3.0` (template render)
- SQLite 3.35+ (built-in)

## Non-Goals

- instance DB 조작 → `msm-instance`
- evidence 수집 → `msm-evidence`
- entity/relation 생성 → `msm-ontology`
