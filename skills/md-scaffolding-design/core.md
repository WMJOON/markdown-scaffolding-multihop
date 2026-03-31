# md-scaffolding-design — Core

## 역할

멀티홉 추론 구조를 **설계하고 저장**하는 스캐폴딩 워크플로우.
md-graph-multihop의 companion: "조회/추론"이 아닌 "구조 초기화 + 결과 저장"을 담당.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **scaffold** | 프로젝트 구조 분석 → graph-config.yaml 자동 생성 |
| **preset** | 미리 정의된 entity/relation 구조 템플릿 |
| **insight node** | Claude 추론 결과를 wikilink 연결로 저장한 md 파일 |
| **ontology decomposition** | Top-down MECE 분해 + Bottom-up Instance 귀납으로 Entity를 확정하고 관계를 매핑하는 설계 방법론 |
| **ABox** | `ontology/[concept]/[instance].md` — instance 노드 저장소. Obsidian `path:ontology/` 필터 대상 |
| **TBox** | `schema/relation/*.yaml` + `schema/concept/*.yaml` — type 정의. graph traversal 제외 |
| **Evidence layer** | `evidence/[topic]/sources|notes|claims/` — 근거·출처 저장소. Ontology ETL 전에 먼저 수집 |
| **ETL flow** | Evidence 수집 → Ontology ETL → Node Link → Validation 승격 순서 |
| **node status** | `draft` → `experimental` → `validated` (또는 `deprecated`) — instance 승격 상태 모델 |

## KB 디렉토리 구조

```text
[kb-name]/
  ontology/     ← ABox: instance 노드 (Obsidian path:ontology/ 필터)
    [concept]/
      [instance].md
  schema/       ← TBox: type 정의 (Neo4j schema 소스, traversal 제외)
    relation/
      [relation-type].yaml
    concept/    ← 선택적
      [concept].yaml
  evidence/     ← 근거·출처
    [topic]/
      sources/
      notes/
      claims/
  context/      ← 운영·정책·계획 (traversal 제외)
    planning/
    policies/
    validation/
    migration/
    comparison/
  docs/         ← 탐색·인덱스 (traversal 제외)
    index/
    guides/
```

## ETL 흐름

```
Evidence 수집
  → Ontology ETL (source-backed claim만 추출)
    → Node Link (frontmatter relations 설정)
      → Validation (status: draft → validated 승격)
```

## 모듈 구성

- `module.kb-structure.md` — KB 디렉토리 구조 원칙 (ABox/TBox 분리, ETL 규칙, 상태 모델)
- `module.ontology-decomposition.md` — 온톨로지 분해 방법론 (Top-down / Bottom-up / 관계 매핑)
- `module.scaffold-policy.md` — 프로젝트 분석 및 config 생성 정책
- `module.insight-save.md` — 추론 결과 → md 노드 저장 정책

## 스크립트

```
scaffold_project.py  → 구조 분석 + graph-config.yaml 생성 (KB 구조 프리셋 포함)
save_insight.py      → 추론 결과 → wikilink md 노드 저장
```

## 프리셋 종류

`personal-memory` | `github-docs` | `git-repo` | `obsidian-vault` | `any-markdown` | `kb-structure`
