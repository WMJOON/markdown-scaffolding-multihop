# Module: Parse (Step D)

규칙 + 사전 + 패턴 기반 엔티티/관계 후보 추출. LLM은 타입 판정 보조로만 허용.

## 추출 패턴 레지스트리

| Entity Type | Pattern | Predicate |
|-------------|---------|-----------|
| Model | `uses\|based on\|trained with` + 대문자 이름 | `targets_model` |
| Work | `for\|applied to\|performs` + task 명사 | `targets_work` |
| Dataset | `dataset\|benchmark\|evaluated on` + 이름 | `uses_dataset` |
| ModelFamily | `family of\|class of` + architecture | `belongs_to_family` |
| Metric | accuracy/F1/BLEU 등 + 수치 | `reports_metric` |

## 추출 순서

1. **Wikilink 감지** — `[[EntityType/entity_id]]` 패턴으로 기존 엔티티 참조 발견
2. **패턴 매칭** — scope_targets에 해당하는 entity type의 regex 적용
3. **기존 사전 매칭** — entity_id, label_en/ko, aliases와 대조
4. **신규 후보 생성** — 매칭 안 되면 `generate_entity_id()` 로 새 ID 생성

## Entity ID 규칙

```
entity_id = {entity_type_lower}__{slug}
slug = lowercase(title).replace(' ','_').replace('-','_')[:80]
collision → __{n} 접미사
```

## 산출물

- `entity_candidates.jsonl`
- `relation_candidates.jsonl`
