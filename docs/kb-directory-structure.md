# KB 디렉토리 구조 (v1.0.0)

`msm init`이 생성하는 5-Layer 표준 구조입니다. 각 레이어는 명확한 역할을 가지며, `ontology/Tbox/` · `ontology/Abox/`만 그래프 탐색 대상입니다.

---

## 전체 구조

```text
{kb-root}/
  canonical_root_hub.yaml         ← locked SSOT — 도메인·경로 선언
  ontology/                       ← L1.A: 온톨로지 본체
    Tbox/                         ← 클래스·관계 정의
      {cluster}/
        md/                       ← Obsidian 그래프뷰용 노트 (시각화 SSOT)
        entities.jsonl            ← 클래스 구조화 (스크립트 SSOT)
        relations.jsonl
    Abox/                         ← 인스턴스
      {cluster}/
        md/
        instances.jsonl
  evidence/                       ← L1.B: 원본·seed
    seeds.jsonl
    md/
    graphify/                     ← Graphify ETL 출력
      entity_candidates.jsonl
      relation_candidates.jsonl
  planning/                       ← L1.C: 장기 태스크 계획
    research/
    ontology/
  report/                         ← L1.D: 설명 문서·논문
    paper/
    maintenance/
    explorer/
  docs/                           ← L1.E: 인덱스·가이드
    index.md
    guideline/
  workflow/                       ← L1.F: yaml 정의 워크플로우
    evidence/
      evidence-collection.yaml
      graphify-etl.yaml
    ontology/
      ontology-construction.yaml
    maintain/
      validation.yaml
    explorer/
      search-reason.yaml
    index.yaml
  memory/                         ← L1.G: 2-tier 메모리
    task-context/
      work-log/
      decision-history/
      troubleshooting/
      release-note/
    ontology-index/
  harness/                        ← L1.H: 하네스·런타임
    run.sh
    tiers/
    trajectory/
  .claude/                        ← 스킬·훅
    skills/
    hooks/
```

---

## 레이어별 역할

### `ontology/` — 지식 본체

**Tbox** (`ontology/Tbox/{cluster}/`): 클래스와 관계 정의. `canonical_root_hub.yaml`의 도메인 단위로 분할. Obsidian에서 `path:ontology/Tbox/`로 필터하면 개념 노드만 반환.

**Abox** (`ontology/Abox/{cluster}/`): 인스턴스. 동일 cluster 구조로 Tbox와 대칭.

**md + jsonl 이중 트랙:**
- `md/` = Obsidian 그래프뷰 시각화 SSOT
- `jsonl/` = 스크립트 입출력 구조화 SSOT
- `msm-ontology`가 두 트랙을 동기화

### `evidence/` — 근거·출처

`seeds.jsonl`에 청킹된 evidence chunk가 쌓입니다. `evidence/graphify/`는 Graphify ETL의 출력 전용 폴더입니다. Evidence가 검증된 후에야 `ontology/`로 승격됩니다.

### `workflow/` — 외부화된 워크플로우

모든 워크플로우는 yaml로 정의됩니다. 스킬이 yaml을 소비하는 방식으로, 워크플로우를 스킬에서 분리합니다.

### `memory/` — 2-tier 메모리

| Tier | 위치 | 수명 |
|------|------|------|
| task-context | `memory/task-context/` | 단기 (세션·태스크) |
| ontology-index | `memory/ontology-index/` | 영구 (구조 인덱스) |

user-memory(사용자 프로파일·선호)는 MSO 영역이므로 MSM이 관리하지 않습니다.

### `harness/` — 런타임

`run.sh`가 L0~L3 티어를 라우팅하고, `trajectory/`에 5-Axis 계측값을 기록합니다.

---

## 최소 frontmatter

### Tbox entity (`ontology/Tbox/{cluster}/md/{slug}.md`)

```yaml
---
entity_id: concept__reinforcement_learning
entity_type: Concept
label_en: Reinforcement Learning
label_ko: 강화학습
status: draft         # draft | experimental | validated | deprecated
cluster: ai_agent
tags: []
---
```

### Abox instance (`ontology/Abox/{cluster}/md/{slug}.md`)

```yaml
---
entity_id: instance__gpt4
entity_type: Model
label_en: GPT-4
status: experimental
cluster: ai_agent
source_doc_id: evidence__openai_gpt4
---
```

---

## ETL 흐름

```
Evidence 수집
  (msm-evidence: URL/MD → seeds.jsonl)
  (graphify_to_msm.py: graph.json → entity_candidates.jsonl)
      ↓
Ontology 승격
  (msm-ontology: MECE 검증 → Tbox/Abox md + jsonl)
      ↓
Status 승격
  draft → experimental → validated
```

---

## canonical_root_hub.yaml 스키마

```yaml
version: "1.0"
locked: true            # msm-orchestration PreToolUse hook이 직접 편집 차단
domains:
  ai_agent:
    tbox: ontology/Tbox/ai_agent/
    abox: ontology/Abox/ai_agent/
    relations: ontology/Tbox/ai_agent/relations.jsonl
```

`locked: true`인 경우 `msm-ontology`를 통해서만 갱신 가능합니다.

---

## 관련 문서

- [빠른 시작](guides/quickstart.md)
- [온톨로지 설정](guides/ontology-config.md)
- [KB 구축 흐름](guides/kb-build-flows.md)
- [PRD v1.0.0](../../planning/msm_v1.0.0/msm_v1.0.0-PRD.md)
