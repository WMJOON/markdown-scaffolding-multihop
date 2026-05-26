---
name: msm-evidence
version: "0.12.0"
description: |
  MSM v1.0.0 Fat Skill — 외부 URL/로컬 MD를 수집·청킹·dedup하여
  evidence/seeds.jsonl 및 evidence/md/ 노트를 생성한다.
  entity/relation 생성은 하지 않는다. seed는 msm-ontology의 입력.
spec: planning/msm_v1.0.0/msm-evidence-SPEC.md
prd: planning/msm_v1.0.0/msm_v1.0.0-PRD.md
---

# msm-evidence (v1.0.0)

## What

외부 원본(URL, 로컬 MD)을 받아 검증 가능한 evidence seed를 생산하는 Fat Skill.

책임:
1. **수집**: URL / 로컬 MD 파일을 fetch
2. **청킹**: 큰 문서를 검색·인용 가능한 단위로 분할
3. **dedup**: content-hash(sha256) 기반 중복 제거
4. **seed 등록**: `evidence/seeds.jsonl`에 append, `evidence/md/`에 노트 저장

자세한 동작은 [core.md](core.md) 참조.

## Entry Points

| 진입점 | 명령 |
|--------|------|
| CLI — collect | `scripts/msm-evidence collect --target REPO --source URI [...] [--apply]` |
| CLI — verify | `scripts/msm-evidence verify --target REPO` |
| CLI — list | `scripts/msm-evidence list --target REPO` |
| CLI — graphify ETL | `scripts/graphify_to_msm.py graph.json [--output-dir OUT] [--sigma 2.0]` |
| Harness | `harness/run.sh --skill msm-evidence --tier L0 --mode validate-only --target REPO` |
| Workflow | `workflow/evidence/graphify-etl.yaml` |

## Triggers

- "evidence 수집", "seed 수집", "URL 크롤링"
- "Ralph", "ETL", "논문 수집"
- "msm-evidence collect"

## Dependencies

- Python 3.10+
- 외부 패키지 없음 (stdlib만: urllib.request, html.parser, hashlib)
- Bash (CLI wrapper, harness)

## Source Types

| 소스 타입 | 스크립트 | 출력 |
|---------|---------|------|
| URL / 로컬 MD | `scripts/msm-evidence collect` | `evidence/seeds.jsonl`, `evidence/md/` |
| Graphify `graph.json` | `scripts/graphify_to_msm.py` | `evidence/graphify/entity_candidates.jsonl`, `evidence/graphify/relation_candidates.jsonl` |

Graphify ETL은 `file_type==concept` 노드만 통과시키는 Semantic Lifting Layer(Option A).
`code` 타입 노드는 버리고, god node(degree 2σ 초과)는 `hub_candidate` 태그 부여.

## Non-Goals

- entity/relation/instance 생성 → `msm-ontology`
- LLM 기반 claim 추출 → v1.1
- JS-rendered 페이지 → v1.2
- PDF 처리 → v1.1
