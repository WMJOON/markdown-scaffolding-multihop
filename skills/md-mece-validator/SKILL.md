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

## 관련 스킬

- `md-scaffolding-design` — graph-config.yaml + 프로젝트 초기화 (scaffold_project.py 포함)
- `kb-ontology-maintenance` — 기존 온톨로지에 노드·관계 추가 (delta check 시 light 모드 활용)
