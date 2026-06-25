# 온톨로지 설정

## canonical_root_hub.yaml — SSOT

MSM의 단일 진실 소스. `msm init`이 자동 생성하며 `locked: true`로 설정됩니다. 직접 편집하지 않고 `msm-ontology`를 통해 갱신합니다.

```yaml
version: "1.0"
locked: true
domains:
  - name: ai_agent
    root_hub: ontology/explain/concept/ai_agent/ai_agent__class.md
    description: "AI Agent 도메인"
system:
  semantic: ontology/system/semantic/**/*.ttl
  kinetic: ontology/system/kinetic/**/*.ttl
  dynamic: ontology/system/dynamic/**/*.ttl
record_archive:
  runtime: record-archive/runtime/runtime.db
  snapshots: record-archive/snapshots/**/*.parquet
```

---

## explain/concept (TBox) / explain/instance (ABox) 구조

```
ontology/
  system/
    semantic/{domain}.ttl
    kinetic/{domain}.ttl
    dynamic/{domain}.ttl
  explain/concept/{cluster}/
    {cluster}__class.md
    entities.jsonl   ← 클래스 구조화 저장 (스크립트 입출력)
    relations.jsonl  ← 관계 구조화 저장
  explain/instance/{cluster}/
    instances.jsonl
```

**md + jsonl 이중 트랙 규칙:**
- `md/` = Obsidian 그래프뷰의 시각화 SSOT
- `jsonl/` = 스크립트 입출력의 구조화 SSOT
- 두 트랙은 `msm-ontology`가 동기화

---

## entity JSONL 최소 스키마

```jsonl
{"entity_id": "concept__reinforcement_learning", "entity_type": "Concept", "label_en": "Reinforcement Learning", "status": "draft", "cluster": "ai_agent", "tags": [], "extra": {}}
```

## relation JSONL 최소 스키마

```jsonl
{"source_entity_id": "concept__rlhf", "predicate": "extends", "target_entity_id": "concept__reinforcement_learning", "confidence": 0.9}
```

---

## Graphify ETL 노드 → explain/concept (TBox) 매핑

Graphify `graph.json`의 concept 노드는 `graphify_to_msm.py`가 MSM entity 형식으로 변환합니다.

| Graphify 필드 | MSM 필드 | 변환 규칙 |
|---|---|---|
| `node.id` | `entity_id` | slug 그대로 |
| `node.label` | `label_en` | 직접 매핑 |
| `node.community_name` | `extra.leiden_community_name` | 보존 |
| degree > mean+2σ | `tags: ["hub_candidate"]` | god node → hub 후보 |

`hub_candidate` 태그 노드는 `*__class.md` 생성 후보로 별도 검토를 권장합니다.

---

## workflow TTL 바인딩

`agent-context/workflow/{category}/*.abox.ttl`이 실행 정본입니다. YAML은 편집·마이그레이션 레이어로 유지합니다.

```yaml
# agent-context/workflow/evidence/graphify-etl.yaml
tool: msm-evidence
steps:
  - id: graphify_to_msm
    script: skills/msm-evidence/scripts/graphify_to_msm.py
    args: ["{inputs.graph_json}", "--output-dir", "{inputs.output_dir}"]
```

---

## 설정 파일 요약

| 파일 | 역할 |
|------|------|
| `canonical_root_hub.yaml` | SSOT — 도메인·explain/system/record archive 경로 선언 |
| `ontology/explain/concept/*/entities.jsonl` | 클래스 정의 (스크립트 입출력) |
| `ontology/explain/concept/*/relations.jsonl` | 관계 정의 |
| `ontology/explain/instance/*/instances.jsonl` | 인스턴스 |
| `ontology/system/**/*.ttl` | formal graph |
| `agent-context/workflow/**/*.abox.ttl` | 워크플로우 실행 정본 |
