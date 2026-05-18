# 온톨로지 설정

## canonical_root_hub.yaml — SSOT

v1.0.0의 단일 진실 소스. `msm init`이 자동 생성하며 `locked: true`로 설정됩니다. 직접 편집하지 않고 `msm-ontology`를 통해 갱신합니다.

```yaml
version: "1.0"
locked: true
domains:
  ai_agent:
    tbox: ontology/Tbox/ai_agent/
    abox: ontology/Abox/ai_agent/
    relations: ontology/Tbox/ai_agent/relations.jsonl
```

---

## Tbox / Abox 구조

```
ontology/
  Tbox/{cluster}/
    md/          ← Obsidian 그래프뷰용 노트 (시각화 SSOT)
    entities.jsonl   ← 클래스 구조화 저장 (스크립트 입출력)
    relations.jsonl  ← 관계 구조화 저장
  Abox/{cluster}/
    md/
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

## Graphify ETL 노드 → Tbox 매핑

Graphify `graph.json`의 concept 노드는 `graphify_to_msm.py`가 MSM entity 형식으로 변환합니다.

| Graphify 필드 | MSM 필드 | 변환 규칙 |
|---|---|---|
| `node.id` | `entity_id` | slug 그대로 |
| `node.label` | `label_en` | 직접 매핑 |
| `node.community_name` | `extra.leiden_community_name` | 보존 |
| degree > mean+2σ | `tags: ["hub_candidate"]` | god node → hub 후보 |

`hub_candidate` 태그 노드는 `*__hub.md` 생성 후보로 별도 검토를 권장합니다.

---

## workflow yaml 바인딩

`workflow/{category}/*.yaml`에서 `tool:` 필드로 스킬을 바인딩합니다.

```yaml
# workflow/evidence/graphify-etl.yaml
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
| `canonical_root_hub.yaml` | v1.0.0 SSOT — 도메인·Tbox/Abox 경로 선언 |
| `ontology/Tbox/*/entities.jsonl` | 클래스 정의 (스크립트 입출력) |
| `ontology/Tbox/*/relations.jsonl` | 관계 정의 |
| `ontology/Abox/*/instances.jsonl` | 인스턴스 |
| `workflow/*.yaml` | 워크플로우 외부 정의 |
