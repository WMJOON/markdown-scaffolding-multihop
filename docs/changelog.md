# Changelog

## v0.1.3 (2026-04-07)

### Added
- `md-kb-rewrite` 스킬 신규 추가 ― KB 유지보수/거버넌스 전담
  - 6단계 rewrite loop (Detect → Diagnose → Draft → Review → Merge → Observe)
  - H-A ~ H-G 7가지 휴리스틱 + H-X Connection Candidate
  - ollama_mcp 연동으로 반복 작업(H-B, H-F) Gemma 위임 가능
- Workflow D (Raw→Wiki Compile) ― md-scaffolding-design에 추가
  - raw/ 소스 문서를 구조화된 wiki 노드로 컴파일
  - Karpathy LLM Knowledge Bases 인사이트 적용
- H-X Connection Candidate 휴리스틱 ― 연결 누락 합성 노드 발견

### Changed
- `md-scaffolding-design` ― KB 유지보수 로직을 md-kb-rewrite로 분리
  - Workflow C 섹션을 md-kb-rewrite 리디렉션으로 대체
  - Workflow D 섹션 추가

### Integration
- ollama_mcp (로컬 Gemma4:e4b) 위임 결정 프레임워크 전 스킬 적용

---

## v0.1.2
> KB 구축 흐름(Top-Down / Bottom-Up)과 최적화 루브릭을 도입한 릴리스.

| 개선 영역 | 이전 | v0.1.2 |
|-----------|------|--------|
| 구축 전략 | 흐름 미정의 | **Top-Down / Bottom-Up** 전략 선택 기준 + 절차 문서화 |
| 토큰 최적화 | 없음 | **Light/Medium/Deep 검증 깊이** 루브릭 + 강제 종료 조건 |
| 상태 승격 조건 | `→ validated` 단일 기준 | `draft → experimental → validated` 단계별 조건 분리 |
| 문서 | `docs/guides/` 2종 | **`kb-build-flows.md` 추가** ― 흐름·루브릭·루프 탈출 통합 |

상세: [SPEC v0.1.2](../../planning/markdown-scaffolding-multihop_v0.1.2-SPEC.md)

---

## v0.1.1
> KB 구조 명세(SPEC)를 도입하고, Obsidian 기반 실제 KB에 검증 적용한 릴리스.

| 개선 영역 | 이전 | v0.1.1 |
|-----------|------|--------|
| KB 구조 | `ontology/` 안에 domain 폴더 혼재 | **ABox/TBox 분리** ― `ontology/`(instance), `schema/`(type 정의) |
| Obsidian 필터 | `path:ontology/` 에 relation 파일 혼재 | `schema/` 분리로 `path:ontology/` 필터 정합성 확보 |
| Neo4j 확장 | 별도 매핑 작업 필요 | `schema/relation/*.yaml` → relationship type 직접 매핑 |
| docs 구조 | 없음 | `docs/index/ · guides/ · templates/` 신설 |
| 프리셋 | `obsidian-vault` 등 5종 | **`kb-structure` 프리셋 추가** ― ABox/TBox 골격 자동 생성 |

상세: [SPEC v0.1.1](../../planning/markdown-scaffolding-multihop_v0.1.1-SPEC.md)