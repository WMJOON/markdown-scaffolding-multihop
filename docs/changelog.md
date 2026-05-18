# Changelog

## v1.0.0 (2026-05-18)

> 5-Layer 아키텍처로 전면 재편. `.skill-modules/` 정책 폐지, v1.0.0 스킬 6개 승격, Graphify ETL 어댑터 추가.

### Breaking — 스킬 구조 재편

- `.skill-modules/` 디렉토리 정책 폐지 → 모든 스킬을 `skills/`로 통합
- v0.x 스킬 7개 (`msm-data-analysis`, `msm-kb-graph`, `msm-kb-rewrite`, `msm-mece-validator`, `msm-obsidian-cli`, `msm-ralph-etl`, `msm-rdf-owl-bridge`) 제거
- v1.0.0 스킬 6개 승격 (`msm-evidence`, `msm-harness`, `msm-maintain`, `msm-ontology`, `msm-orchestration`, `msm-repository-setup`)

### Added — 5-Layer 아키텍처

- `msm-repository-setup`: `msm init` — 5-Layer KB 디렉토리 골격 부트스트랩 (L0 score 1.0 검증 완료)
- `msm-harness`: memory 2-tier · L0~L3 런타임 · 5-Axis 계측 (비결정성·궤적·오라클·비용·HITL)
- `msm-orchestration` v1.0.0: 자연어 인텐트 라우팅 · CC 계약 · HITL 2층 정책 · workflow yaml 바인딩
- `msm-evidence`: URL/MD 수집 · 청킹 · dedup · seed 등록
- `msm-ontology`: entity·relation 생성 · MECE 검증 · Tbox/Abox 승격
- `msm-maintain`: scan · rewrite · data-analysis
- `workflow/evidence/graphify-etl.yaml`: Graphify ETL 워크플로우 정의

### Added — Graphify ETL 어댑터

- `skills/msm-evidence/scripts/graphify_to_msm.py`
  - Graphify `graph.json` → MSM entity/relation JSONL 변환 (Semantic Lifting Layer Option A)
  - `file_type == "concept"` 노드만 통과, `code` 타입 제거
  - god node (degree > mean + 2σ) → `tags: ["hub_candidate"]` 자동 태깅
  - Leiden `community_name` → `extra.leiden_community_name` 보존
  - LLM 재호출 없음 (Graphify Step 2 concept 노드 재활용)

---

## v0.2.0 (2026-04-28)

> 스킬 10개 → 7개 통합 재편 (md-* → msm-*). 각 스킬의 워크플로우 완결성을 높이고 구성을 간소화. mece-validator 완전 자동화, 보안 강화.

### Changed — 스킬 구조 재편
- `md-*` 10개 → `msm-*` 7개로 통합·리네임
  - `msm-kb-graph` (신규 통합): `md-graph-multihop` + `md-vector-search` + `md-scaffolding-design` 병합
    - 그래프 초기화·BFS 멀티홉·zvec 벡터 검색·인사이트 저장을 단일 진입점으로
  - `msm-ralph-etl`: `md-ralph-etl` + `md-frontmatter-rollup` 흡수 (ETL + 집계 통합)
  - `msm-mece-validator`, `msm-kb-rewrite`, `msm-rdf-owl-bridge`, `msm-obsidian-cli`, `msm-data-analysis`: 리네임
- README 스킬 구성 mermaid·역할 요약·의존관계 테이블 전면 갱신
- `graph_builder.py` `entities.*.dir` 레거시 포맷 호환 추가

### Added — mece-validator 자동화
- `msm-mece-validator/scripts/mece_interview.py`
  - `--auto` 플래그 — LLM이 인터뷰 답변 자동 생성, 무인 MECE 검증 루프
  - `--ollama` 플래그 — Ollama 확인 프롬프트 자동 수락, 로컬 모델 단독 실행
  - 질문 중복 조기 종료 — 반복 질문 감지 시 루프 자동 종료

### Security
- `skills/md-ralph-etl/data/ontology-entities/` (ETL 추출 엔티티 78개 파일) git 이력 전체 정화 (git filter-repo)
- `.gitignore`에 Ralph ETL 런타임 산출물 경로 추가 — archive/, data/ontology-entities/, data/ontology-relations/, evidence_corpus/

---

## v0.1.6 (2026-04-27)

> md-mece-validator 신규 스킬 추가. graph-ontology.yaml 온톨로지 설계·검증을 위한 Calibrated Validation 루프 구현.

### Added
- `md-mece-validator` 스킬 신규
  - `scripts/mece_interview.py` — MECE Calibrated Validation 루프 (light/medium/deep)
  - `references/depth-guide.md` — 채점 공식, 차원별 가중치, 출력 구조 상세
  - light: LLM 0회, heuristic 구조 체크 (클래스·관계 존재 여부, domain/range 선언)
  - medium: LLM 4-6회, ME/CE two-bucket 채점, 게이트 ≥0.75, crystallize
  - deep: LLM 15-24회, 6차원 채점 + Contrarian 체크, 게이트 ≥0.85 + open_questions 소진, `context/validation/mece-pack-{날짜}.yaml` 출력

### Changed
- `md-scaffolding-design/scripts/scaffold_project.py` `--mece [light|medium|deep]` 플래그 추가 — 분석 후 MECE 인터뷰 자동 연계
- `md-scaffolding-design/SKILL.md` 스크립트 목록에 `mece_interview.py` 추가, `md-mece-validator` 참조 링크 추가
- `requirements.txt` `anthropic>=0.40` 추가 (medium/deep 모드용)
- `docs/guides/ontology-config.md` MECE 검증 섹션 추가
- `docs/guides/kb-build-flows.md` Light 검증 기준에 `md-mece-validator` 참조 추가

---

## v0.1.5 (2026-04-25)

> md-obsidian-cli 스킬 구조 재설계, Obsidian 그래프 계층 패턴 명문화, md-ralph-etl PDF 처리 지원 추가, 스크립트 구문 오류 수정.

### Added
- `md-obsidian-cli/references/graph-hierarchy-patterns.md` 신규
  - Obsidian 그래프 계층 구조 설계 패턴 (L0/L1/L2 허브-리프 구조)
  - 폴더 레벨 가시성 규칙, 양방향 wikilink 패턴, frontmatter 계층 스키마
  - md-graph-multihop 연동 섹션 — `graph-config.yaml` `entity_dirs`·`relation_map` 설정 가이드
- `md-ralph-etl/scripts/step_pdf.py` 신규
  - arxiv 등 PDF URL 직접 처리 (opendataloader-pdf 우선, pymupdf4llm fallback)
  - 원본 `.pdf` + 변환본 `.md` 동시 저장
- `md-ralph-etl/scripts/ollama_http.py`, `publish_evidence.py` 신규

### Changed
- `md-obsidian-cli/SKILL.md` 네비게이션 허브로 재구조화 (~190줄 → ~45줄)
  - 중복 커맨드 레퍼런스 제거 (module.commands.md, cli-reference.md와 분리)
  - frontmatter description에 계층 구조 패턴 트리거 추가
- `md-obsidian-cli/references/graph-hierarchy-patterns.md` frontmatter 스키마 수정
  - `relations: [{type: parent_node}]` → `parent: "[[...]]"` 단일 필드로 통일
  - `md-scaffolding-design`의 `relation_map: {parent: child_of}` 와 직접 호환
- `md-ralph-etl/scripts/step_crawl.py` PDF URL 분기 추가
- `md-ralph-etl/scripts/ralph_cli.py` PDF 시나리오 지원 확장
- `md-scaffolding-design/SKILL.md` description 간소화

### Fixed
- `md-data-analysis/scripts/correlation_analysis.py` f-string 내 백슬래시 이스케이프 구문 오류 수정 (Python 3.11 이하 호환)

---

## v0.1.4 (2026-04-17)

> md-kb-rewrite의 wrapper layer 성격을 명확히 하고, semantic framing guardrail / H-X / ollama_mcp 운영 패턴을 README 차원에서 공식화한 릴리스.

### Added
- `md-kb-rewrite` 스킬에 semantic framing guardrail 추가
- H-X: interesting connection / missing synthesis 후보 탐지까지 범위 확대
- ollama_mcp 전용 섹션 README에 추가 — role, model(`qwen3.5:4b`), fallback, use patterns 명시

### Changed
- README 포지셔닝: GraphRAG/ETL 중심 → **structural layer + maintenance/governance layer** 구조 명시
- `md-kb-rewrite` 설명: rewrite loop 중심 → wrapper skill + semantic framing + synthesis detection로 확대
- `qwen3.5:4b`를 경량 보조 기본 모델로 문서화

---

## v0.1.3 (2026-04-07)

### Added
- `md-kb-rewrite` ��ų �ű� �߰� �� KB ��������/�Ź��ͽ� ����
  - 6�ܰ� rewrite loop (Detect �� Diagnose �� Draft �� Review �� Merge �� Observe)
  - H-A ~ H-G 7���� �޸���ƽ + H-X Connection Candidate
  - ollama_mcp �������� �ݺ� �۾�(H-B, H-F) Gemma ���� ����
- Workflow D (Raw��Wiki Compile) �� md-scaffolding-design�� �߰�
  - raw/ �ҽ� ������ ����ȭ�� wiki ���� ������
  - Karpathy LLM Knowledge Bases �λ���Ʈ ����
- H-X Connection Candidate �޸���ƽ �� ���� ���� �ռ� ��� �߰�

### Changed
- `md-scaffolding-design` �� KB �������� ������ md-kb-rewrite�� �и�
  - Workflow C ������ md-kb-rewrite ���𷺼����� ��ü
  - Workflow D ���� �߰�

### Integration
- ollama_mcp (���� Gemma4:e4b) ���� ���� �����ӿ�ũ �� ��ų ����

---

## v0.1.2
> KB ���� �帧(Top-Down / Bottom-Up)�� ����ȭ ��긯�� ������ ������.

| ���� ���� | ���� | v0.1.2 |
|-----------|------|--------|
| ���� ���� | �帧 ������ | **Top-Down / Bottom-Up** ���� ���� ���� + ���� ����ȭ |
| ��ū ����ȭ | ���� | **Light/Medium/Deep ���� ����** ��긯 + ���� ���� ���� |
| ���� �°� ���� | `�� validated` ���� ���� | `draft �� experimental �� validated` �ܰ躰 ���� �и� |
| ���� | `docs/guides/` 2�� | **`kb-build-flows.md` �߰�** �� �帧����긯������ Ż�� ���� |

��: [SPEC v0.1.2](../../planning/markdown-scaffolding-multihop_v0.1.2-SPEC.md)

---

## v0.1.1
> KB ���� ����(SPEC)�� �����ϰ�, Obsidian ��� ���� KB�� ���� ������ ������.

| ���� ���� | ���� | v0.1.1 |
|-----------|------|--------|
| KB ���� | `ontology/` �ȿ� domain ���� ȥ�� | **ABox/TBox �и�** �� `ontology/`(instance), `schema/`(type ����) |
| Obsidian ���� | `path:ontology/` �� relation ���� ȥ�� | `schema/` �и��� `path:ontology/` ���� ���ռ� Ȯ�� |
| Neo4j Ȯ�� | ���� ���� �۾� �ʿ� | `schema/relation/*.yaml` �� relationship type ���� ���� |
| docs ���� | ���� | `docs/index/ �� guides/ �� templates/` �ż� |
| ������ | `obsidian-vault` �� 5�� | **`kb-structure` ������ �߰�** �� ABox/TBox ��� �ڵ� ���� |

��: [SPEC v0.1.1](../../planning/markdown-scaffolding-multihop_v0.1.1-SPEC.md)