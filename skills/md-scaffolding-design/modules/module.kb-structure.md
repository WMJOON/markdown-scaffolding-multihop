# module.kb-structure

## 목적

이 프레임워크를 적용한 KB의 **디렉토리 구조 원칙**을 정의한다.
Obsidian path 필터 정합성과 Neo4j 확장을 동시에 만족하는 ABox/TBox 분리 구조.

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
    concept/           ← 선택적: concept class 메타 정의
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

## 레이어 역할

| 레이어 | 성격 | Obsidian 필터 | Neo4j 역할 |
|--------|------|--------------|-----------|
| `ontology/` | ABox — instance 노드 | `path:ontology/` → concept 노드만 반환 | Node (label = 폴더명) |
| `schema/` | TBox — type 정의 | 제외 | Relationship type 스키마 소스 |
| `evidence/` | 근거·출처 | `path:evidence/` | 별도 Node 또는 Property |
| `context/` | 운영 문서 | 제외 | 제외 |
| `docs/` | 메타 문서 | 제외 | 제외 |

---

## ABox: ontology/

**instance 노드만** 포함한다. 폴더명 = Neo4j node label = Obsidian type tag.

`path:ontology/` 로 필터하면 concept 노드만 정확히 반환된다.
`schema/`, `context/`, `docs/` 가 섞이지 않는다.

### instance 최소 frontmatter

```yaml
---
type: technique                    # concept 폴더명 (= Neo4j node label)
status: draft                      # draft | experimental | validated | deprecated
sources:
  - evidence/[topic]/sources/[file].md
relations:
  - type: uses                     # schema/relation/uses.yaml의 label 참조
    target: "[[ontology/framework/RLAIF]]"
domain: [도메인 레이블]             # 인덱싱·필터링용 (docs/index/ 생성에 활용)
---
```

---

## TBox: schema/

**type 정의 전용.** `ontology/` 밖에 위치하므로 Obsidian path 필터에 걸리지 않는다.
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

---

## ETL 흐름

```
Evidence 수집       evidence/[topic]/sources|notes|claims/
       ↓
Ontology ETL        source-backed claim만 추출 → ontology/[concept]/[instance].md
       ↓
Node Link           frontmatter relations 설정 (schema/relation/* 참조)
       ↓
Validation          status: draft → experimental → validated
```

---

## 상태 모델

| 상태 | 의미 |
|------|------|
| `draft` | 구조화 초안, 근거 부족 또는 검증 전 |
| `experimental` | 일부 evidence 있으나 ontology placement 불안정 |
| `validated` | source-backed claim + relation 검증 완료 |
| `deprecated` | 더 나은 node/structure로 대체됨 |

**승격 최소 조건 (→ validated):**
- source note 1개 이상
- 핵심 claim의 evidence trace 확보
- relation 방향 확인
- `context/validation/` 에 validation pack 존재 권장

---

## graph-config.yaml 연동 규칙

```yaml
# graph-config.yaml 권장 설정 (kb-structure 프리셋)
entity_dirs:
  - ontology/technique/
  - ontology/framework/
  - ontology/pattern/
  # ... 각 concept 폴더를 명시

exclude_dirs:
  - schema/
  - context/
  - docs/

schema_dir: schema/relation/       # relation type 정의 소스
```

`exclude_dirs` 에 `schema/`, `context/`, `docs/` 를 포함해야
GraphRAG retrieval에서 메타 문서가 섞이지 않는다.
