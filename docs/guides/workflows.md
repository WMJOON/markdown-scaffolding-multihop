# 워크플로우 가이드

v1.0.0의 모든 워크플로우는 `workflow/{category}/*.yaml`로 외부 정의되고, 스킬이 yaml을 소비합니다.

---

## 워크플로우 카테고리

| 카테고리 | yaml 위치 | 담당 스킬 |
|---------|----------|---------|
| evidence | `workflow/evidence/` | `msm-evidence` |
| ontology | `workflow/ontology/` | `msm-ontology` |
| maintain | `workflow/maintain/` | `msm-maintain` |
| explorer | `workflow/explorer/` | `msm-graph-reasoning` (v1.x 예정) |

---

## Workflow A — 새 KB 부트스트랩

```bash
skills/msm-repository-setup/scripts/msm init \
  --target my-kb --domain ai_agent --apply --yes

# canonical_root_hub.yaml + 5-Layer 골격 생성
# msm-orchestration이 workflow/index.yaml 자동 등록
```

→ [quickstart.md](quickstart.md)

---

## Workflow B — Evidence 수집

```bash
# workflow/evidence/evidence-collection.yaml 소비
skills/msm-orchestration/msm-orchestrate run \
  --workflow workflow/evidence/evidence-collection.yaml \
  --target my-kb --tier L1 --mode dry-run
```

또는 직접 호출:

```bash
skills/msm-evidence/scripts/msm-evidence collect \
  --target my-kb --source https://arxiv.org/abs/2310.01848 --apply
```

---

## Workflow C — Graphify ETL

코드베이스를 KB evidence로 수집합니다.

```bash
# workflow/evidence/graphify-etl.yaml 소비
skills/msm-orchestration/msm-orchestrate run \
  --workflow workflow/evidence/graphify-etl.yaml \
  --target my-kb \
  --inputs '{"graph_json": "graphify-out/graph.json"}' \
  --tier L1 --mode dry-run
```

또는 직접 호출:

```bash
graphify .
python skills/msm-evidence/scripts/graphify_to_msm.py \
  graphify-out/graph.json --output-dir my-kb/evidence/graphify/
```

---

## Workflow D — Ontology 구축

```bash
# workflow/ontology/ontology-construction.yaml 소비
skills/msm-orchestration/msm-orchestrate run \
  --workflow workflow/ontology/ontology-construction.yaml \
  --target my-kb --tier L1 --mode dry-run
```

또는 직접 호출:

```bash
skills/msm-ontology/scripts/msm-ontology add \
  --target my-kb --cluster ai_agent \
  --type Concept --label "RLHF" --apply

skills/msm-ontology/scripts/msm-ontology mece \
  --target my-kb --cluster ai_agent --depth medium
```

---

## Workflow E — KB 유지보수

```bash
# workflow/maintain/validation.yaml 소비
skills/msm-orchestration/msm-orchestrate run \
  --workflow workflow/maintain/validation.yaml \
  --target my-kb --tier L1 --mode dry-run
```

또는 직접 호출:

```bash
skills/msm-maintain/scripts/msm-maintain scan --target my-kb
skills/msm-maintain/scripts/msm-maintain report --target my-kb
```

---

## 자연어 라우팅

`msm-orchestration`이 자연어 인텐트를 workflow yaml로 자동 매핑합니다.

```bash
skills/msm-orchestration/msm-orchestrate run \
  --intent "graphify로 이 레포 분석해서 KB에 넣어줘" \
  --target my-kb --tier L0 --mode dry-run
```

라우팅 규칙: [skills/msm-orchestration/references/router-trigger-map.yaml](../../skills/msm-orchestration/references/router-trigger-map.yaml)

---

## ollama_mcp 연동

반복적·저비용 작업을 로컬 모델에 위임해 Claude 토큰을 절약합니다.

| 작업 | 위임 여부 |
|------|---------|
| evidence 청킹·요약 | ✓ ollama |
| concept 추출 초안 | ✓ ollama |
| MECE 판단·semantic bias 검출 | ✗ Claude 직접 |
