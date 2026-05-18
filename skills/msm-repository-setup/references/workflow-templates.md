# Workflow Templates

`templates/workflow/`에 4종이 있다. 모두 SPEC §4.2의 최소 스키마를 만족한다.

| 파일 | category | kind | mode | tool |
|------|----------|------|------|------|
| `evidence/evidence-collection.yaml` | evidence | single | dry-run | msm-evidence |
| `ontology/ontology-construction.yaml` | ontology | single | dry-run | msm-ontology |
| `maintain/validation.yaml` | maintain | single | validate-only | msm-maintain |
| `explorer/search-reason.yaml` | explorer | pipeline | dry-run | (pipeline steps) |

`workflow/index.yaml`은 위 4개를 registry로 모은다. SPEC §6.2.

## 검증 키

`validate_workflows.py`가 강제하는 필수 키:

- top-level: `version`, `id`, `category`, `kind`, `mode`, `inputs`, `outputs`, `runtime`, `governance`
- governance: `hitl_required`, `max_retry`
- mode: `dry-run` / `apply` / `validate-only`
- kind: `single` (→ `tool` 필수) / `pipeline` (→ `pipeline:` 블록 필수)
