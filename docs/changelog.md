# Changelog

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
- ollama_mcp 전용 섹션 README에 추가 — role, model(`gemma4:e4b`), fallback, use patterns 명시

### Changed
- README 포지셔닝: GraphRAG/ETL 중심 → **structural layer + maintenance/governance layer** 구조 명시
- `md-kb-rewrite` 설명: rewrite loop 중심 → wrapper skill + semantic framing + synthesis detection로 확대
- `gemma4:e4b`를 경량 보조 기본 모델로 문서화

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