# msm-ontology — Core Reference

## 1. 파일 레이아웃

```
{target}/
  ontology/
    Tbox/
      {cluster}/
        entities.jsonl
        relations.jsonl
        md/
          {snake_label}.md
    Abox/
      {cluster}/
        instances.jsonl
        md/
          {snake_label}.md
```

## 2. ID 규칙

| 종류 | 패턴 | 예시 |
|------|------|------|
| entity | `entity:<snake_case_label>` | `entity:ai_agent` |
| instance | `instance:<snake_case_label>` | `instance:codex` |
| relation | `rel:<src_local>:<predicate>:<tgt_local>` | `rel:ai_agent:uses:tool` |

- 충돌 시 `_2`, `_3` 접미
- `accepted` 이상으로 승격된 id는 변경 금지

## 3. source_refs 강제

모든 add 호출에 `--evidence evidence:seed:...` 1개 이상 필수.
없으면 exit 1 + `source_refs_missing` 메시지.

## 4. MECE 검증

| 탐지 | 기준 |
|------|------|
| label_duplicate | 동일 cluster 내 normalized label 동일 |
| jaccard_overlap | label+synonyms Jaccard >= 0.7 |
| cluster_boundary | Tbox relation source/target이 다른 cluster |
| orphan_entity | source_refs 비어 있음 |
| missing_md | md_path 없거나 파일 없음 |

violation ≥ 1 → exit 1.

## 5. MD Projection

- `<!-- msm:generated:file ... -->` 첫 줄 마커
- frontmatter: id, label, cluster, kind/type, status, source_refs
- `<!-- msm:generated:start -->` ~ `<!-- msm:generated:end -->` 블록 갱신
- Notes 영역 (블록 아래) 보존

## 6. Oracle — `ontology_mece_readiness`

score = (entity≥1 ? 0.25 : 0)
      + (all_source_refs ? 0.25 : 0)
      + (mece_violations==0 ? 0.25 : 0)
      + (md_projection_complete ? 0.25 : 0)
