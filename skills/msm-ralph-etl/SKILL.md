---
name: msm-ralph-etl
description: >
  Evidence 기반 온톨로지 확장을 위한 토큰 최적화 ETL 도구 모음.
  URL/로컬 파일을 크롤링하고, 헤딩 경계 기반 청킹으로 증거 단위를 생성하며,
  Levenshtein + TF-IDF 2단계 유사도로 그래프 위치 판정(new/extend/merge/hold)을 수행한다.
  LLM 호출을 최소화하고 규칙+패턴 기반 엔티티 추출을 우선하는 비용 최적화 파이프라인.
  트리거 예시: "Ralph로 URL 수집해줘", "Evidence ETL 실행해줘", "논문에서 엔티티 추출해줘",
  "온톨로지 확장해줘", "로컬 문서에서 Model 엔티티 뽑아줘", "관계 보강해줘".
---

# md-ralph-etl

Evidence 수집 → 온톨로지 확장 → 불변 Seed 발행을 위한 이벤트 기반 ETL 도구.
`graph-ontology.yaml` 기반 vault에서 동작하며, Python stdlib만 사용 (외부 패키지 불필요).

## 필수 프로토콜: 설계 → 실행 → 종료

Ralph형 업무를 수행할 때 **반드시 3-Phase 프로토콜**을 따른다.

1. **Phase 0 — DESIGN**: 실행 전에 scope, mode, similarity, 종료 기준을 사용자와 합의. 합의 없이 CLI 실행 금지.
2. **Phase 1 — EXECUTE**: dry-run 먼저 → 사용자 확인 → `--apply`. 매 step 후 gate 평가.
3. **Phase 2 — EVALUATE**: 종료 판정. 성공/경고/차단/수확체감 중 하나로 분류 후 구조적 보고.

상세 규칙: [module.workflow-design.md](modules/module.workflow-design.md)

## 전제 조건

- Python 3.10+
- `curl`, `pandoc` (full 모드 HTML 크롤링 시)
- `01_ontology-data/graph-ontology.yaml` 존재
- PDF 처리 (선택):
  - `opendataloader-pdf` + Java 11+: `pip install opendataloader-pdf` (품질 최상)
  - `pymupdf4llm`: `pip install pymupdf4llm` (순수 Python fallback)

## Graphify ETL 어댑터 (v1.0.0 — Semantic Lifting Layer)

코드베이스를 Graphify로 분석한 결과를 MSM SSOT로 변환하는 어댑터.
`file_type==concept` 노드만 통과시키고 god node를 `hub_candidate`로 태깅한다.

```bash
# 실행
graphify .
python scripts/graphify_to_msm.py graphify-out/graph.json --output-dir evidence/graphify/

# 출력
# evidence/graphify/entity_candidates.jsonl
# evidence/graphify/relation_candidates.jsonl
```

워크플로우: `workflow/evidence/graphify-etl.yaml`
v1.0.0에서 `msm-evidence` 스킬로 이관 예정.

