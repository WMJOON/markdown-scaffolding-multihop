---
name: md-ralph-etl
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
- `curl`, `pandoc` (full 모드 크롤링 시)
- `01_ontology-data/graph-ontology.yaml` 존재

## 스크립트

```
01_ontology-data/tools/
├── ralph_cli.py                 # CLI 진입점
└── ralph/
    ├── coordinator.py           # 상태 머신 오케스트레이터
    ├── step_intake.py           # A. URL/파일 정규화, dedup, 배치
    ├── step_crawl.py            # B. curl+pandoc 크롤링
    ├── step_preprocess.py       # C. 헤딩 경계 청킹 엔진
    ├── step_parse.py            # D. 규칙+패턴 엔티티/관계 추출
    ├── step_placement.py        # E. 2단계 유사도 그래프 위치 판정
    ├── step_seal.py             # F. V1-V8 검증 + Seed 봉인
    ├── similarity.py            # Levenshtein + TF-IDF cosine
    ├── common.py                # 공유 dataclass/enum
    ├── yaml_io.py               # YAML/JSONL 입출력
    ├── idempotency.py           # SHA256 멱등성 키
    └── reporter.py              # cost/run 리포트 생성
```

## 운영 모드 (3종)

| 모드 | 설명 | 스킵 단계 | 사용 시나리오 |
|------|------|----------|-------------|
| `full` | URL → crawl → 전체 | 없음 | 새 URL에서 엔티티 수집 |
| `local` | 로컬 파일 → preprocess부터 | B_CRAWL | 이미 받은 논문/문서 처리 |
| `enrich` | parse → place → seal만 | B_CRAWL, C_PREPROCESS | 기존 엔티티 관계 보강 |

## 입력 포맷 (3종)

| 포맷 | 옵션 | 형식 |
|------|------|------|
| TSV | `--manifest data.tsv` | case_id, source_type, industry_mapping, title, url, start_marker |
| JSONL | `--manifest sources.jsonl` | `{"url":"...","title":"...","source_type":"...","tags":[...]}` |
| 디렉토리 | `--input-dir ./docs/` | 지정 폴더의 .md/.txt/.html 자동 스캔 |

## 워크플로우

### 시나리오 1 — URL에서 CaseStudy/Model 엔티티 수집

```bash
# dry-run (기본)
python3 tools/ralph_cli.py run \
  --manifest data/raw-data/case-study/case-study-source-manifest.tsv \
  --scope CaseStudy,Model

# 실제 반영
python3 tools/ralph_cli.py run \
  --manifest data/raw-data/case-study/case-study-source-manifest.tsv \
  --scope CaseStudy,Model \
  --apply
```

### 시나리오 2 — 로컬 논문 디렉토리에서 Model 추출

```bash
python3 tools/ralph_cli.py run \
  --input-dir ./papers/ \
  --mode local \
  --scope Model \
  --batch-size 10
```

### 시나리오 3 — JSONL manifest로 혼합 소스 처리

```bash
# sources.jsonl 예시:
# {"url":"https://arxiv.org/abs/2401.01234","title":"New Architecture","source_type":"paper"}
# {"path":"/local/report.md","title":"Internal Report","source_type":"report"}

python3 tools/ralph_cli.py run \
  --manifest sources.jsonl \
  --scope Model,Work,Dataset
```

### 시나리오 4 — 기존 엔티티 관계 보강

```bash
python3 tools/ralph_cli.py run \
  --manifest data.tsv \
  --mode enrich
```

### 시나리오 5 — 이전 run 재개 / 상태 확인

```bash
# 재개
python3 tools/ralph_cli.py run --resume R-20260303-0001

# 상태 확인
python3 tools/ralph_cli.py status --run-id R-20260303-0001

# 리포트 생성
python3 tools/ralph_cli.py report --run-id R-20260303-0001
```

### 시나리오 6 — 특정 단계만 실행

```bash
python3 tools/ralph_cli.py parse --run-id R-20260303-0001 --apply
python3 tools/ralph_cli.py place --run-id R-20260303-0001
python3 tools/ralph_cli.py seal  --run-id R-20260303-0001 --apply
```

## 주요 CLI 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--manifest PATH` | TSV 또는 JSONL manifest 파일 | |
| `--input-dir PATH` | 로컬 디렉토리 (--manifest 대체) | |
| `--mode {full,local,enrich}` | 운영 모드 | full |
| `--format {tsv,jsonl,auto}` | 입력 포맷 (자동 감지) | auto |
| `--scope TYPE,TYPE,...` | 추출 대상 entity type | 전체 |
| `--apply` | 실제 파일 쓰기 (없으면 dry-run) | false |
| `--batch-size N` | 배치당 최대 URL/파일 수 | 20 |
| `--resume RUN_ID` | 이전 run 재개 | |
| `--extensions .md,.txt` | local 모드 스캔 확장자 | .md,.txt,.html |

## 핵심 도구 상세

### Similarity Engine (토큰 최적화 핵심)

LLM 호출 없이 2단계 유사도로 그래프 위치 판정:

1. **Lexical** (alias_sim): Normalized Levenshtein — entity_id, label, aliases 간 비교
2. **Semantic** (embed_sim): TF-IDF cosine (char 3-gram + word unigram) — summary/definition 비교

임계치 (calibration 예정):
- `alias_sim >= 0.92` → merge_candidate
- `alias_sim >= 0.80` → extend
- `embed_sim >= 0.75` → relation-only
- evidence = 0 → reject
- ambiguity > threshold → hold

### Chunking Engine (증거 단위 생성)

- 전략: H1-H3 헤딩 경계 우선 분할
- 크기: max 400 words, overlap 50 words, min 40 words
- 메타데이터: `[doc_type | section_path]` 접두사 자동 부착

### Entity Parsing (규칙 우선)

패턴 레지스트리 방식 — entity type별 regex + 기존 사전 매칭:
- Model: `uses|based on|trained with` + 대문자 시작 이름
- Work: `for|applied to|performs` + task 명사
- Dataset: `dataset|benchmark|evaluated on` + 이름
- Metric: 수치 + 단위 자동 추출

### Seal Validation Suite (V1-V8)

seed 발행 전 필수 검증:
- V1 evidence coverage, V2 entity_id 유일성, V3 relation type 유효성
- V4 hold 잔여, V5 orphan, V6 layer 일관성, V7 merge 확정, V8 source_ref 포맷

## 산출물 경로

```
archive/history/ralph-runs/{run_id}/
├── run_state.yaml           # 상태 머신 (중단/재개 가능)
├── intake_manifest.yaml     # A단계: 정규화된 입력 목록
├── evidence_corpus/
│   ├── raw/                 # B단계: 원문 보존
│   ├── index/               # B단계: 최소 인덱스
│   └── chunks/              # C단계: 증거 단위
├── entity_candidates.jsonl  # D단계: 엔티티 후보
├── relation_candidates.jsonl# D단계: 관계 후보
├── placement_report.jsonl   # E단계: 위치 판정
├── hold_registry.yaml       # E단계: hold 관리
├── seed_candidate.yaml      # F단계: 불변 Seed
├── validation_results.jsonl # F단계: V1-V8 결과
├── audit_trail.jsonl        # F단계: 추적 로그
├── cost_report.yaml         # 비용 리포트
└── run_report.yaml          # 실행 리포트
```

## HITL 게이트

- **H1** (비용/리스크): LLM 호출 > 5%, hold > 20%, retry >= 70%
- **H2** (토폴로지): 새 node/relation type, 대규모 merge(10%+)

## 관련 Workflow 엔티티

이 스킬은 다음 Workflow 엔티티에 의해 오케스트레이션된다:
- `[[Workflow/workflow__ralph_etl_evidence_pipeline]]` — 6단계 전체 파이프라인

## 관련 스킬

- `md-graph-multihop` — 멀티홉 그래프 추론 (placement 판정의 기반)
- `md-scaffolding-design` — graph-config/ontology 구조 설계
- `md-frontmatter-rollup` — frontmatter 집계 (seal 후 rollup 연계)

## 스펙 문서

- `02_planning/20260303-ontological_ralph_etl/Ontological-Ralph-ETL-Instruction-v0.0.3.md`
