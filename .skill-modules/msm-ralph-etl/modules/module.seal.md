# Module: Seal & Optimize (Step F)

V1-V8 Validation Suite 통과 후 불변 Seed 발행. LLM 자동 병합 확정 금지.

## Validation Suite

| # | Check | Pass Criteria | Failure |
|---|-------|---------------|---------|
| V1 | Evidence coverage | 100% 노드/관계에 evidence span | SEAL_BLOCKED |
| V2 | Entity ID 유일성 | 기존과 중복 없음 | SEAL_BLOCKED |
| V3 | Relation type 유효성 | ontology 정의에 존재 | SEAL_BLOCKED |
| V4 | Hold 잔여 | 현재 배치 hold = 0 | SEAL_BLOCKED |
| V5 | Orphan check | relation 0개 노드 없음 | Warning |
| V6 | Layer 일관성 | purpose↔structure 경로 존재 | Warning |
| V7 | Merge 확정 | merge_candidate = 0 | SEAL_BLOCKED |
| V8 | Source ref format | `[[source__*]]` 포맷 | SEAL_BLOCKED |

## Entity Markdown 생성

`--apply` 시 `data/ontology-entities/{EntityType}/{entity_id}.md`에 기존 포맷 호환 파일 생성:
- YAML frontmatter (entity_id, entity_type, ontology_layer, label_ko/en, relations, tags 등)
- Body (Summary, Definition, Evidence 섹션)

## 산출물

- `seed_candidate.yaml` — 불변 스냅샷 + provenance
- `optimization_patch.yaml`
- `audit_trail.jsonl` — candidate → placement → entity 추적
- `validation_results.jsonl`
