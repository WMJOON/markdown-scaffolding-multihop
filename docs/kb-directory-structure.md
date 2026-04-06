# KB 디렉토리 구조

이 프레임워크를 적용한 Knowledge Base의 권장 디렉토리 구조입니다.

각 폴더는 명확한 역할을 가집니다. 폴더를 역할별로 분리하는 이유는 단순한 정리 습관이 아니라, **그래프 탐색 범위를 정확하게 제어하기 위해서입니다.** `ontology/`만 그래프 노드로 읽히고, 나머지 폴더는 탐색에서 제외됩니다. 이 분리가 없으면 KB 품질이 섞이고, 검색 결과가 오염됩니다.

---

## 전체 구조

```text
[kb-name]/
  ontology/            ← ABox: instance 노드만 (Obsidian path:ontology/ 필터 대상)
    [concept]/
      [instance].md
  schema/              ← TBox: type 정의 (graph traversal 제외)
    relation/
      [relation-type].yaml
    concept/           ← 선택적
      [concept].yaml
  evidence/            ← 근거·출처
    [topic]/
      sources/
      notes/
      claims/
  context/             ← 운영·정책·계획 (graph traversal 제외)
    planning/
    policies/
    validation/
    migration/
    comparison/
  docs/                ← 탐색·인덱스 (graph traversal 제외)
    index/
    guides/
```

---

## 각 폴더의 역할

### `ontology/` — 지식의 본체

**여기에 들어오는 것:** 구조화된 개념 노드(instance). 도메인 지식의 핵심 단위들이 여기 삽니다.

이 폴더가 그래프 탐색의 대상입니다. `md-graph-multihop`이 읽는 파일들이 여기 있습니다. Obsidian에서 `path:ontology/`로 필터하면 concept 노드만 반환됩니다. 폴더명이 Neo4j node label과 직접 매핑됩니다.

**여기에 넣지 않을 것:** evidence(근거 문서), 운영 노트, 템플릿. 섞이면 그래프 탐색이 오염됩니다.

### `schema/` — 관계의 정의서

**여기에 들어오는 것:** 노드 간 관계 유형(relation type)의 YAML 정의. "어떤 노드가 어떤 노드와 어떤 관계를 맺을 수 있는가"를 선언합니다.

`ontology/` 밖에 있으므로 Obsidian path 필터에 걸리지 않습니다. Neo4j로 내보낼 때 relationship type 스키마 소스로 직접 사용됩니다.

### `evidence/` — 주장의 근거

**여기에 들어오는 것:** 논문, 기사, 공식 문서, 인터뷰 등 ontology 노드의 주장을 뒷받침하는 원천 자료.

`evidence/`에 있는 내용이 검증된 뒤에야 `ontology/` 노드의 `status`가 승격됩니다. "왜 이 주장이 맞는가?"에 대한 답이 여기 있습니다.

### `context/` — 운영 문서

**여기에 들어오는 것:** KB를 만들고 유지하는 과정에서 생긴 운영 문서. 계획, 정책, 검증 기록, 마이그레이션 로그, 비교 분석 등.

그래프 탐색에서 제외됩니다. KB의 지식 자체가 아니라, KB를 운영하는 맥락을 담습니다.

### `docs/` — 메타 문서

**여기에 들어오는 것:** KB 전체를 탐색하거나 이해하는 데 도움이 되는 가이드, 인덱스, 템플릿.

그래프 탐색에서 제외됩니다. 사람이 KB를 이해하기 위해 읽는 문서들입니다.

---

## 레이어별 역할 요약

| 레이어 | 성격 | Obsidian 필터 | Neo4j 역할 |
|--------|------|--------------|-----------|
| `ontology/` | ABox — instance 노드 | `path:ontology/` | Node (label = 폴더명) |
| `schema/` | TBox — type 정의 | 제외 | Relationship type 스키마 소스 |
| `evidence/` | 근거·출처 | `path:evidence/` | 별도 Node 또는 Property |
| `context/` | 운영 문서 | 제외 | 제외 |
| `docs/` | 메타 문서 | 제외 | 제외 |

---

## ontology/ 노드의 최소 frontmatter

```yaml
---
type: technique                    # concept 폴더명
status: draft                      # draft | experimental | validated | deprecated
sources:
  - evidence/[topic]/sources/[file].md
relations:
  - type: uses                     # schema/relation/uses.yaml 참조
    target: "[[ontology/framework/RLAIF]]"
domain: [도메인 레이블]
---
```

`status` 필드가 중요합니다. `draft`는 아직 검증 전, `experimental`은 1차 검토 통과, `validated`는 cross-link까지 검증 완료를 의미합니다.

---

## schema/relation/ 파일 최소 스키마

```yaml
# schema/relation/uses.yaml
label: USES
source_types: [technique, framework]
target_types: [technique, framework, pattern]
properties:
  context: string
neo4j_direction: outgoing
```

---

## ETL 흐름

새 지식이 KB에 들어오는 전체 경로입니다. Evidence가 없으면 ontology로 승격되지 않습니다.

```
Evidence 수집
  → Ontology ETL (source-backed claim만 추출)
    → Node Link (frontmatter relations 설정)
      → Validation (status: draft → validated 승격)
```

---

## 관련 문서

- KB 구축 흐름 가이드: [`docs/guides/kb-build-flows.md`](guides/kb-build-flows.md)
- 구조 명세 v0.1.1: [`planning/markdown-scaffolding-multihop_v0.1.1-SPEC.md`](../../planning/markdown-scaffolding-multihop_v0.1.1-SPEC.md)
- Top-Down/Bottom-Up + 루브릭 명세 v0.1.2: [`planning/markdown-scaffolding-multihop_v0.1.2-SPEC.md`](../../planning/markdown-scaffolding-multihop_v0.1.2-SPEC.md)
