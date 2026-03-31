# KB 디렉토리 구조

이 프레임워크를 적용한 Knowledge Base의 권장 디렉토리 구조.

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

## 레이어 역할

| 레이어 | 성격 | Obsidian 필터 | Neo4j 역할 |
|--------|------|--------------|-----------|
| `ontology/` | ABox — instance 노드 | `path:ontology/` | Node (label = 폴더명) |
| `schema/` | TBox — type 정의 | 제외 | Relationship type 스키마 소스 |
| `evidence/` | 근거·출처 | `path:evidence/` | 별도 Node 또는 Property |
| `context/` | 운영 문서 | 제외 | 제외 |
| `docs/` | 메타 문서 | 제외 | 제외 |

## ontology/

**instance 노드만** 포함한다. 폴더명 = Neo4j node label = Obsidian type tag.

`path:ontology/` 로 필터하면 concept 노드만 반환된다. schema/context/docs가 섞이지 않는다.

### instance 최소 frontmatter

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

## schema/

**TBox 전용.** `ontology/` 밖에 위치하므로 Obsidian path 필터에 걸리지 않는다.
Neo4j export 시 relationship type 스키마 소스로 직접 사용된다.

### relation type yaml 최소 스키마

```yaml
# schema/relation/uses.yaml
label: USES
source_types: [technique, framework]
target_types: [technique, framework, pattern]
properties:
  context: string
neo4j_direction: outgoing
```

## ETL 흐름

```
Evidence 수집
  → Ontology ETL (source-backed claim만 추출)
    → Node Link (frontmatter relations 설정)
      → Validation (status: draft → validated 승격)
```

## 관련 문서

- 상세 명세: [`planning/markdown-scaffolding-multihop_v0.1.1-SPEC.md`](../../planning/markdown-scaffolding-multihop_v0.1.1-SPEC.md)
