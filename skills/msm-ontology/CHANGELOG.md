# msm-ontology Changelog

## [0.13.0] — 2026-05-26

### Added
- **LinkML OWL reasoning layer** — YAML 작성 → OWL/Turtle 컴파일 → owlready2 추론 → JSONL 역주입
- **`compile.py`** — LinkML YAML(`ontology/definition/*.yaml`) → OWL/Turtle(`ontology/owl/*.ttl`)
  - `--domain NAME` 으로 특정 도메인만 컴파일 가능
- **`reason.py`** — Turtle → owlready2 OWL2 DL reasoning
  - Pellet → HermiT 순으로 자동 fallback
  - 추론 결과(`inferred_types`, `inferred_properties`) → `ontology/Abox/_inferred/inferred.jsonl`
- **`materialize.py`** — compile + reason 연속 실행 (단계 실패 시 중단)
- **`explain.py`** — instance ID로 원본 레코드 + 추론 결과 + 근거 ontology 출력
- **디스패처 확장** — `compile / reason / materialize / explain` 추가
  - v0.12.0 stub(`definition / contract-validate / eca-run / eca-schedule / gen-ddl`)도 디스패처에 연결

### Dependencies
- 신규: `linkml` (compile), `owlready2` + Java (reason)
- 기존 CLI는 stdlib만으로 동작 유지

### Design Decision
- **OWL 거부 → 채택 전환**: v1.2.0 PRD §1.2에서 OWL을 거부했으나,
  관계 추적/관리 및 복잡한 class inference 필요성으로 재채택.
  Obsidian 호환은 inferred.jsonl → 기존 projection 경로로 유지.
- 상세: `planning/msm-ontology_v0.13.0/msm-ontology_v0.13.0-PRD.md`

## [1.1.0] — 2026-05-20

### Added
- **Real-time progress logging** to stderr with consistent prefixes:
  - `[*]` — info (progress)
  - `[+]` — success
  - `[!]` — warning/skipped
  - `[x]` — error
- **Batch operation counters** showing `(i/N)` for multi-entity registrations
- **Summary report** at end of `add_entities()` showing added/skipped/failed counts
- **Error handling** with exception catching in atomic operations
- **Logging helper function** `_log()` using `flush=True` for real-time output

### Changed
- **Behavior change**: fail-fast → continue-on-error in `add_entities()`
  - Previously: duplicate label would stop processing remaining entities
  - Now: skips duplicate and continues with next entity, returns non-zero rc
- **Error messages** consolidated to use `_log(..., "err")` instead of inline `print()`
- **stdout/stderr separation**: logs go to stderr, JSON events stay on stdout

### Fixed
- Batch processing now shows all results instead of aborting on first error

## [1.0.0] — Initial release

- Entity / relation / instance registration to JSONL
- MECE violation detection
- Markdown projection generation
- Atomic append for consistency
