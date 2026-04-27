---
name: md-mece-validator
description: >
  graph-ontology.yaml 온톨로지 설계·검증 전용 스킬. Calibrated Validation 루프(light/medium/deep)로
  클래스·관계 구조의 MECE(상호배제·전체포괄) 품질을 보장한다. Bounded Rationality 원칙에 따라
  depth 파라미터 하나로 LLM 호출 수·라운드·게이트·출력물을 동시에 제어한다.
  트리거: "온톨로지 MECE 검증해줘", "graph-ontology 설계", "MECE 인터뷰", "온톨로지 구조 점검",
  "온톨로지 품질 확인", "classes가 겹치는 것 같아", "KB 구조 MECE로 만들어줘".
  md-scaffolding-design의 companion 스킬.
---

# md-mece-validator

`graph-ontology.yaml` 설계·검증 스킬. depth 파라미터 하나로 리소스 투입량을 조절한다.

## 스크립트

```
scripts/
└── mece_interview.py   # MECE Calibrated Validation 루프
```

상세 채점 공식·depth 비교: `references/depth-guide.md`

---

## 빠른 참조

| depth  | 언제 쓰나                             | 명령 |
|--------|--------------------------------------|------|
| light  | 아는 도메인, 빠른 구조 확인           | `python3 mece_interview.py --draft ./graph-ontology.yaml --depth light` |
| medium | 일반 KB 설계, 중간 복잡도             | `python3 mece_interview.py --domain "시장 분석 KB" --depth medium --output ./graph-ontology.yaml` |
| deep   | 신규·복잡 도메인, 중요 의사결정 KB    | `python3 mece_interview.py --draft ./graph-ontology.yaml --depth deep --output ./graph-ontology.yaml` |

### 비대화형 자동 모드 (CI / 대규모 KB)

```bash
# Ollama 확인 프롬프트 자동 수락 + 인터뷰 질문 LLM 자동 답변
python3 mece_interview.py --draft ./graph-ontology.yaml --depth medium --auto --ollama --output ./graph-ontology.yaml
```

| 플래그 | 효과 |
|--------|------|
| `--ollama` | Ollama 사용 확인 프롬프트 자동 수락 |
| `--auto`   | LLM이 "senior ontology reviewer" 역할로 인터뷰 질문에 자동 답변 (`--ollama` 포함) |

**조기 종료 조건 (자동 내장):** 다음 중 하나를 만족하면 해당 라운드에서 중단한다.
- 문자 3-gram Jaccard ≥ 0.15 — 새 질문이 이전 질문과 어휘를 재사용
- 같은 weakest 차원(ME/CE)이 2라운드 연속 — 소형 LLM이 동일 갭에 갇힌 경우

---

## 워크플로우

### 새 온톨로지 설계 (Medium)

```bash
python3 mece_interview.py --domain "도메인 설명" --depth medium --output ./graph-ontology.yaml
```

인터뷰 루프:
1. LLM이 weakest 차원(ME·CE)을 공략하는 질문 생성
2. 사람이 답변 입력
3. MECE 점수 채점 → 게이트(≥0.75) 충족 시 종료
4. 인터뷰 내용을 반영해 draft 결정화(crystallize)
5. `mece_assessment` 블록을 포함한 yaml 저장

### 기존 초안 검증 (Light — LLM 없음)

```bash
python3 mece_interview.py --draft ./graph-ontology.yaml --depth light
```

체크 항목:
- 클래스 최소 2개, object_property 최소 1개
- 모든 클래스에 `entity_dir` 정의
- 모든 관계에 `domain` / `range` 선언 + 실제 클래스 존재

### 기존 초안 개선 (Deep)

```bash
python3 mece_interview.py --draft ./graph-ontology.yaml --depth deep --output ./graph-ontology.yaml
```

추가 출력: `context/validation/mece-pack-{날짜}.yaml`

---

## scaffold_project.py 연계

```bash
# 프로젝트 분석 → MECE 인터뷰 한 번에
python3 scaffold_project.py --local ./my-docs --mece medium --domain "시장 분석 KB"
python3 scaffold_project.py --template obsidian-vault --mece light
```

---

## mece_assessment 출력 예시

```yaml
mece_assessment:
  depth: medium
  score: 0.79
  me_score: 0.83
  ce_score: 0.75
  gate_threshold: 0.75
  rounds_used: 2
  status: seed_ready    # draft | reviewing | seed_ready
  open_questions: []    # deep에서만 추적
  assessed_at: "2026-04-27"
```

---

## 소형 LLM false positive 방지

Ollama 소형 모델(≤7B)은 이름이 비슷한 클러스터를 ME 위반으로 잘못 판정하는 경향이 있다.
**처방: 클러스터 description 첫머리에 `[계층 레이블]`을 명시한다.**

```yaml
# 나쁜 예 — 모델이 세 클러스터를 동의어로 혼동
agent-governance:
  description: "에이전트 감사 인프라"
ai-governance:
  description: "AI 거버넌스 평가"
ax-org-mgmt:
  description: "조직 에이전트 관리"

# 좋은 예 — 계층 레이블로 즉시 구분
agent-governance:
  description: "[에이전트 거버넌스] 에이전트 결정 감사·규제 엔지니어링"
ai-governance:
  description: "[AI-시스템 거버넌스] AI 행동 평가 실행 체계"
ax-org-mgmt:
  description: "[조직 관리] 에이전트 도입 시 조직 프로세스·자산화"
```

효과: description 레이블만 추가해도 ME 점수가 0.30 → 0.70으로 개선된 사례 확인.

### 대형 온톨로지 처리 (오브젝트 200+)

파일이 너무 커서 LLM 컨텍스트에 직접 넣기 어려울 때: 클러스터별로 요약한 condensed YAML을 먼저 생성하고 검증에 사용한다.

```bash
# 1. condense 스크립트로 클러스터 요약 생성
python3 condense_kb_ontology.py --source graph-ontology.yaml --output graph-ontology-condensed.yaml

# 2. condensed로 MECE 검증
python3 mece_interview.py --draft graph-ontology-condensed.yaml --depth medium --auto --output graph-ontology-condensed.yaml
```

---

## 관련 스킬

- `md-scaffolding-design` — graph-config.yaml + 프로젝트 초기화 (scaffold_project.py 포함)
- `kb-ontology-maintenance` — 기존 온톨로지에 노드·관계 추가 (delta check 시 light 모드 활용)
