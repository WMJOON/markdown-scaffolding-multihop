---
name: msm-instance
version: "0.12.0"
description: |
  MSM v1.2.0 — DuckDB 기반 property graph instance layer 관리.
  evidence → DuckDB insert, contract validate, ECA rule_runner 실행.
triggers:
  - "msm-instance init"
  - "instance DB 초기화"
  - "instance insert"
  - "instance query"
  - "instance migrate"
  - "export-snapshot"
  - "ECA 실행"
  - "market_signal 등록"
  - "SQLite runtime"
  - "DuckDB analytics"
---

# msm-instance (v1.2.0)

## What

MSM의 Instance Layer(ABox)를 SQLite + DuckDB 하이브리드로 운용하는 Fat Skill.

**원칙: SQLite로 살아가고, DuckDB로 생각한다.**

| 저장소 | 용도 | 경로 |
|--------|------|------|
| `instance/runtime.db` | OLTP 상태 기억 (WAL 모드) | `<target>/instance/runtime.db` |
| `instance/snapshots/*.parquet` | OLAP analytics bridge | `<target>/instance/snapshots/` |

책임:
1. **init**: schema DDL 생성 + runtime.db 초기화
2. **insert**: evidence → instance row 삽입 (contract validate 선행)
3. **query**: DuckDB로 parquet snapshot 분석
4. **migrate**: schema 버전 마이그레이션
5. **export-snapshot**: runtime.db → parquet 스냅샷 내보내기
6. **eca-run**: ECA(Event-Condition-Action) 규칙 실행

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — init | `scripts/msm-instance init --target REPO [--apply]` |
| CLI — insert | `scripts/msm-instance insert --target REPO --table TABLE --data JSON [--apply]` |
| CLI — query | `scripts/msm-instance query --target REPO --sql SQL` |
| CLI — migrate | `scripts/msm-instance migrate --target REPO --to VERSION [--apply]` |
| CLI — export-snapshot | `scripts/msm-instance export-snapshot --target REPO [--apply]` |
| CLI — eca-run | `scripts/msm-instance eca-run --target REPO --table TABLE --row JSON` |
| Harness | `harness/run.sh --skill msm-instance --tier L0 --mode validate-only --target REPO` |

## Triggers

- "instance DB 초기화", "instance insert", "instance query"
- "market_signal 등록", "ECA 실행", "export-snapshot"
- "msm-instance init"

## Dependencies

- Python 3.10+
- `duckdb>=0.9` (query, export-snapshot)
- `pyyaml>=6.0` (schema 로드)
- SQLite 3.35+ (built-in)

## Non-Goals

- entity/relation 생성 → `msm-ontology`
- Obsidian projection → `msm-obsidian-projection`
- evidence 수집 → `msm-evidence`
- HITL gate → `msm-orchestration`
