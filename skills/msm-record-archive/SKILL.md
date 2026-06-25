---
name: msm-record-archive
version: "0.13.4"
description: |
  MSM v0.13.4 — record-archive/ 관리.
  SQLite runtime DB, append-only events, derived records, Parquet snapshots,
  temporal fields, ECA rule_runner entrypoint를 담당한다.
---

# msm-record-archive (v0.13.4)

## What

MSM의 Record Archive Layer를 SQLite + DuckDB 하이브리드로 운용하는 Fat Skill.

**원칙: SQLite로 살아가고, DuckDB로 생각한다.**

| 저장소 | 용도 | 경로 |
|--------|------|------|
| `record-archive/registry/instance-ids.jsonl` | stable id + type/source refs registry | `<target>/record-archive/registry/` |
| `record-archive/runtime/runtime.db` | OLTP 상태 기억 (WAL 모드) | `<target>/record-archive/runtime/runtime.db` |
| `record-archive/events/*.jsonl` | append-only occurrence/change events | `<target>/record-archive/events/` |
| `record-archive/derived/*.jsonl` | materialized derived state records | `<target>/record-archive/derived/` |
| `record-archive/snapshots/*.parquet` | OLAP analytics bridge | `<target>/record-archive/snapshots/` |

책임:
1. **init**: schema DDL 생성 + runtime.db 초기화
2. **insert**: evidence/ontology source_refs 기반 row 삽입 (contract validate 선행)
3. **query**: DuckDB로 parquet snapshot 분석
4. **migrate**: schema 버전 마이그레이션
5. **export-snapshot**: runtime.db → parquet 스냅샷 내보내기
6. **eca-run**: ECA(Event-Condition-Action) 규칙 실행

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — init | `scripts/msm-record-archive init --target REPO [--apply]` |
| CLI — insert | `scripts/msm-record-archive insert --target REPO --table TABLE --data JSON [--apply]` |
| CLI — query | `scripts/msm-record-archive query --target REPO --sql SQL` |
| CLI — migrate | `scripts/msm-record-archive migrate --target REPO --to VERSION [--apply]` |
| CLI — export-snapshot | `scripts/msm-record-archive export-snapshot --target REPO [--apply]` |
| CLI — eca-run | `scripts/msm-record-archive eca-run --target REPO --table TABLE --row JSON` |
| Harness | `harness/run.sh --skill msm-record-archive --tier L0 --mode validate-only --target REPO` |

## Triggers

- "record archive 초기화", "runtime DB 초기화", "event archive"
- "instance DB 초기화", "instance insert", "instance query"
- "market_signal 등록", "ECA 실행", "export-snapshot"
- "msm-record-archive init"

## Dependencies

- Python 3.10+
- `duckdb>=0.9` (query, export-snapshot)
- `pyyaml>=6.0` (schema 로드)
- SQLite 3.35+ (built-in)

## Non-Goals

- entity/relation 생성 → `msm-ontology`
- msm-explain projection → `msm-explain`
- evidence 수집 → `msm-evidence`
- HITL gate → `msm-orchestration`
