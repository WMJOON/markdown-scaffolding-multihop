# KB 디렉토리 구조

이 프레임워크를 적용한 Knowledge Base의 권장 디렉토리 구조입니다.

각 폴더는 명확한 역할을 가집니다. 폴더를 역할별로 분리하는 이유는 단순한 정리 습관이 아니라, **그래프 탐색 범위를 정확하게 제어하기 위해서입니다.** `ontology/`만 그래프 노드로 읽히고, 나머지 폴더는 탐색에서 제외됩니다. 이 분리가 없으면 KB 품질이 섞이고, 검색 결과가 오염됩니다.

---

## 전체 구조

```text
[kb-name]/
  ontology/            ← 그래프 탐색 대상 (Obsidian path:ontology/ 필터)
    concept/           ← 개념 정의 노드 (TBox-lite) — 도메인별 폴더, 클래스별 1개 파일
      [domain]/
        [Concept].md     예) market/Industry.md, market/Segment.md
    instance/          ← 인스턴스 노드 (ABox) — 도메인별 폴더
      [domain]/
        [instance].md    예) market/samsung.md  (class는 frontmatter type 필드)
  schema/              ← 관계 유형 정의 (graph traversal 제외)
    relation/
      [relation-type].yaml
  evidence/            ← 근거·출처
    [domain]/
      sources/
      notes/
      claims/
  raw/                 ← 미처리 소스 (Workflow D 입력, graph traversal 제외)
    [domain]/
  context/             ← 운영·정책·계획 (graph traversal 제외)
    planning/
    policies/
    validation/          ← MECE validation pack (mece-pack-{날짜}.yaml)
    migration/           ← 디렉토리·파일 이동 로그
    comparison/
    ontology-history/    ← 온톨로지 객체 변경 이력 (삭제·병합·분리·rename)
      YYYY-MM-DD_[action]-[object].yaml
  docs/                ← 탐색·인덱스 (graph traversal 제외)
    index/
    guides/
```

---

## 각 폴더의 역할

### `ontology/` — 지식의 본체

이 폴더가 그래프 탐색의 대상입니다. `md-graph-multihop`이 읽는 파일들이 여기 있습니다. Obsidian에서 `path:ontology/`로 필터하면 개념·인스턴스 노드만 반환됩니다.

#### `ontology/concept/` — 개념 정의 (TBox-lite)

**여기에 들어오는 것:** 도메인별 폴더 아래 클래스당 1개 파일. "Industry란 무엇인가", "Segment란 무엇인가"처럼 개념 자체를 정의하는 노드입니다. `graph-ontology.yaml`의 클래스 선언과 1:1 대응합니다.

도메인 폴더명(`market/`)은 탐색 범위를 나타내며, 파일명이 Neo4j node label(`Industry`)과 대응됩니다. 같은 도메인 안에 여러 클래스 정의가 공존할 수 있습니다.

#### `ontology/instance/` — 인스턴스 노드 (ABox)

**여기에 들어오는 것:** 도메인별 폴더 아래 실제 엔티티 파일. `ontology/instance/market/samsung.md`처럼 같은 도메인의 엔티티들이 도메인 폴더 아래 모입니다.

도메인 폴더 안에 여러 클래스의 인스턴스가 공존할 수 있습니다. Neo4j label은 폴더명이 아닌 각 파일의 **`type` frontmatter 필드**로 결정됩니다 (예: `type: industry`).

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

#### `context/ontology-history/` — 온톨로지 스키마 변경 이력

`ontology/`의 클래스·관계 **객체가 삭제·병합·분리·rename된 경우**만 기록합니다. 추가(add)는 `graph-ontology.yaml` 자체가 소스이므로 기록 불필요.

파일명 규칙: `YYYY-MM-DD_[action]-[target].yaml`

```yaml
# context/ontology-history/2026-04-27_merge-Segment-into-Industry.yaml
date: 2026-04-27
type: merge                  # delete | merge | split | rename
objects_before:
  - Segment
  - Industry
object_after: Industry       # 남은 클래스 (삭제면 null)
reason: "Segment는 Industry의 하위 속성으로 충분히 표현 가능 — Bottom-Up ETL 후 MECE 검증(score 0.71→0.83)으로 판단"
trigger: mece-validator      # mece-validator | bottom-up-etl | top-down | manual
affected_nodes:              # wikilink 수정이 필요했던 노드 목록
  - ontology/instance/market/samsung.md
  - evidence/market/segment-analysis.md
mece_score_before: 0.71
mece_score_after: 0.83
```

**`context/migration/`과의 구분:** `migration/`은 파일·디렉토리의 물리적 이동(경로 변경, vault 재구성)을 기록하고, `ontology-history/`는 스키마 수준의 개념 생명주기(클래스의 탄생·소멸·합성)를 기록합니다.

### `docs/` — 메타 문서

**여기에 들어오는 것:** KB 전체를 탐색하거나 이해하는 데 도움이 되는 가이드, 인덱스, 템플릿.

그래프 탐색에서 제외됩니다. 사람이 KB를 이해하기 위해 읽는 문서들입니다.

---

## 레이어별 역할 요약

| 레이어 | 성격 | Obsidian 필터 | Neo4j 역할 |
|--------|------|--------------|-----------|
| `ontology/concept/[domain]/` | TBox-lite — 개념 정의 노드 | `path:ontology/concept/` | Node label = 파일명 |
| `ontology/instance/[domain]/` | ABox — instance 노드 | `path:ontology/instance/` | Node label = `type` frontmatter |
| `schema/` | TBox — type 정의 | 제외 | Relationship type 스키마 소스 |
| `evidence/` | 근거·출처 | `path:evidence/` | 별도 Node 또는 Property |
| `raw/` | 미처리 소스 — Workflow D 입력 | 제외 | 제외 |
| `context/` | 운영 문서 | 제외 | 제외 |
| `context/ontology-history/` | 온톨로지 객체 변경 이력 | 제외 | 제외 |
| `context/validation/` | MECE 검증 pack | 제외 | 제외 |
| `context/migration/` | 파일·디렉토리 이동 로그 | 제외 | 제외 |
| `docs/` | 메타 문서 | 제외 | 제외 |

---

## ontology/ 노드의 최소 frontmatter

### instance 노드 (`ontology/instance/[domain]/[instance].md`)

```yaml
---
type: industry                     # Neo4j label — class 식별자 (필수)
status: draft                      # draft | experimental | validated | deprecated
domain: market                     # 이 파일이 속한 도메인 폴더명과 일치
sources:
  - evidence/market/sources/[file].md
relations:
  - type: uses                     # schema/relation/uses.yaml 참조
    target: "[[ontology/instance/tech/RLAIF]]"
---
```

### concept 노드 (`ontology/concept/[domain]/[Concept].md`)

```yaml
---
type: concept
label: Industry                    # 이 파일이 정의하는 클래스명 (파일명과 동일)
domain: market
status: validated
description: "..."
properties:                        # 이 클래스의 인스턴스가 가지는 속성 목록
  - name
  - market_share
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
