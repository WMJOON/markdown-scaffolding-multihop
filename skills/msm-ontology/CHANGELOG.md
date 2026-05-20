# msm-ontology Changelog

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
