# 워크플로우 가이드

어떤 상황에서 시작하느냐에 따라 4가지 워크플로우 중 하나를 선택합니다.

| 워크플로우 | 시작 상황 | 핵심 스킬 |
|-----------|----------|---------|
| A | KB를 처음 만든다 | `md-scaffolding-design`, `md-mece-validator` |
| B | Claude 인사이트를 KB 노드로 저장한다 | `md-scaffolding-design` (`save_insight.py`) |
| C | KB가 낡거나 지저분해졌다 | `md-kb-rewrite` |
| D | raw/ 소스를 wiki 노드로 컴파일한다 | `md-scaffolding-design`, `ollama_mcp` |

---

## Workflow A — 새 KB를 처음 만드는 상황

"도메인은 정해졌는데 Markdown 구조가 아직 없다. 어디서부터 시작하지?"

`md-scaffolding-design`을 실행합니다. 프로젝트 디렉토리나 GitHub repo를 분석해 `graph-ontology.yaml`을 자동 생성하고, `ontology/` · `schema/` · `evidence/` · `context/` · `docs/` 폴더 구조를 초기화합니다. 프리셋(personal-memory, obsidian-vault, git-repo 등)을 사용하면 즉시 시작할 수 있습니다.

```bash
python3 scaffold_project.py --local ./my-docs --output ./graph-ontology.yaml
python3 scaffold_project.py --template obsidian-vault --output ./graph-ontology.yaml

# MECE 온톨로지 검증 포함 (md-mece-validator 연계)
python3 scaffold_project.py --local ./my-docs --mece medium --domain "도메인 설명"
```

→ 상세: [KB 구축 흐름](kb-build-flows.md) · [온톨로지 설정](ontology-config.md)

---

## Workflow B — 추론 결과를 KB에 저장하는 상황

"Claude가 분석한 인사이트를 그냥 대화로 끝내지 않고, KB 노드로 남기고 싶다."

`md-scaffolding-design`의 `save_insight.py`를 씁니다. Claude의 추론 결과에 wikilink를 연결해 기존 그래프와 이어지는 노드로 저장합니다. 나중에 `md-graph-multihop`이 이 노드를 다시 추론 경로에 포함시킬 수 있습니다.

```bash
python3 save_insight.py --title "분석 제목" --content "..." --links "node-a,node-b" --config graph-ontology.yaml
```

---

## Workflow C — KB가 낡거나 지저분해진 상황

"노트가 너무 길어졌거나, 같은 내용이 여러 곳에 흩어졌거나, 새 논문을 추가했는데 기존 노드에 반영이 안 됐다."

`md-kb-rewrite`를 씁니다. H-A~H-X 휴리스틱으로 문제를 진단하고, 6단계 rewrite loop(Detect → Diagnose → Draft → Review → Merge → Observe)로 개선합니다. 위험도가 낮은 작업은 자동 반영, 높은 작업은 human review를 거칩니다.

v0.1.4부터 H-X가 **interesting connection / missing synthesis** 후보도 탐지합니다. 즉 이 워크플로우는 단순 cleanup뿐 아니라 "아직 쓰이지 않은 article이나 concept가 있는가?"까지 점검합니다.

→ 상세: [KB 유지보수 가이드](kb-maintenance.md)

---

## Workflow D — Raw 소스를 Wiki 노드로 컴파일하는 상황

"클리핑해둔 문서, 논문 초록, 메모들이 `raw/` 폴더에 쌓여 있다. 이걸 KB 구조로 정리하고 싶다."

Karpathy의 "LLM Knowledge Bases" 접근에서 착안한 흐름입니다. `md-scaffolding-design`이 `raw/[domain]/` 디렉토리를 스캔하고, 각 문서를 `ontology/` 또는 `evidence/`로 분류·컴파일합니다. 저위험 초안 작성이나 개념 목록 추출은 `ollama_mcp`(로컬 Gemma)에게 위임할 수 있습니다.

```
raw/[domain]/source.md (status: raw)
  → ontology/instance/[domain]/[instance].md (status: draft, type: [class])
  → evidence/[domain]/sources/[source].md
```

---

## ollama_mcp 연동

`ollama_mcp`는 필수 의존성이 아닌 **비용 절감·반복 작업 위임 보조 레이어**입니다. 모든 유지보수/합성 작업을 상위 모델에 맡기면 단순 반복 작업까지 고비용 reasoning 경로를 타게 됩니다.

**권장 모델:** `qwen3.5:4b` — concept extraction / lightweight semantic filtering / draft condensation / rewrite pre-pass 역할

**대표 사용 패턴:**

1. **H-X Connection Candidate 탐지** — `ollama_extract_concepts`로 여러 노드의 핵심 개념 목록 추출 → Claude가 교차 분석해 gap·synthesis·missing node 후보 도출
2. **Rewrite pre-pass** — 긴 note를 로컬 모델이 summary draft로 압축 → 상위 레이어가 semantic framing risk 재검토
3. **Evidence freshness triage** — 새 evidence note와 기존 summary note 간 키워드 차이 1차 비교

**fallback:** `ollama_mcp`가 없거나 오류 나면 상위 모델이 직접 노드 본문을 읽어 처리하고, 처리 대상 수를 줄여 토큰 낭비를 최소화합니다.
