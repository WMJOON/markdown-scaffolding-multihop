# MECE Validator — Depth Guide

## 목차
1. [Depth별 비용과 게이트](#depth별-비용과-게이트)
2. [MECE 점수 계산 공식](#mece-점수-계산-공식)
3. [차원별 가중치](#차원별-가중치)
4. [Perspective 질문 전략](#perspective-질문-전략)
5. [Deep 전용: Contrarian 체크](#deep-전용-contrarian-체크)
6. [출력 파일 구조](#출력-파일-구조)

---

## Depth별 비용과 게이트

| depth  | LLM 호출 | 라운드  | 게이트                        | 출력물                                 |
|--------|---------|---------|------------------------------|----------------------------------------|
| light  | 0       | 0       | heuristic                    | graph-ontology.yaml + mece_assessment  |
| medium | 4-6     | 2-3     | MECE ≥ 0.75                  | + mece_assessment 블록                 |
| deep   | 15-24   | 5-8     | ≥ 0.85 + open_questions 소진 | + validation_pack.yaml                 |

### Light 체크리스트 (heuristic)

- 클래스 최소 2개
- object_property 최소 1개
- 모든 클래스: `entity_dir` 정의 여부
- 모든 관계: `domain` / `range` 선언 여부
- `domain` / `range` 값이 실제 클래스명과 일치 여부

### Medium 루프 조건

```
while round < 3:
    weakest = score_two_bucket()["weakest"]  # "me" 또는 "ce"
    question = ask_question(weakest)
    answer = input()
    score = score_two_bucket()
    if score >= 0.75: break
→ crystallize(history) → write yaml
```

### Deep 루프 조건

```
while round < 8:
    weakest = score_six_dim()["weakest"]     # 6차원 중 최저
    question = ask_question(weakest)
    answer = input()
    score = score_six_dim()
    contrarian = check_contrarian()
    open_questions += contrarian["open_question"]
    if score >= 0.85 and not open_questions: break
→ crystallize(history) → write yaml + validation_pack
```

---

## MECE 점수 계산 공식

```
MECE score = (ME score + CE score) / 2

ME score = class_boundary_clarity × 0.40
         + property_uniqueness    × 0.35
         + constraint_consistency × 0.25

CE score = entity_coverage    × 0.40
         + relation_coverage  × 0.35
         + attribute_coverage × 0.25
```

### Medium: Two-bucket 채점

LLM이 ME 전체, CE 전체를 각각 하나의 점수로 평가.

```json
{
  "me_score": 0.0~1.0,
  "ce_score": 0.0~1.0,
  "weakest": "me" | "ce",
  "reasoning": "핵심 문제 한 줄"
}
```

### Deep: 6차원 채점

LLM이 6개 차원을 개별 점수로 평가 → 가중합으로 ME/CE 산출.

```json
{
  "class_boundary_clarity": 0.0~1.0,
  "property_uniqueness":    0.0~1.0,
  "constraint_consistency": 0.0~1.0,
  "entity_coverage":        0.0~1.0,
  "relation_coverage":      0.0~1.0,
  "attribute_coverage":     0.0~1.0,
  "weakest": "가장 낮은 차원 이름",
  "reasoning": "핵심 문제 한 줄"
}
```

---

## 차원별 가중치

### ME (Mutually Exclusive — 상호배제)

| 차원                    | 가중치 | 의미                                        |
|------------------------|--------|---------------------------------------------|
| class_boundary_clarity | 0.40   | 두 클래스가 동시에 적용될 수 있는 경우 없음  |
| property_uniqueness    | 0.35   | 같은 의미를 가진 중복 관계 없음             |
| constraint_consistency | 0.25   | domain/range 제약이 실제 인스턴스와 충돌 없음 |

### CE (Collectively Exhaustive — 전체포괄)

| 차원                | 가중치 | 의미                                       |
|--------------------|--------|---------------------------------------------|
| entity_coverage    | 0.40   | 모든 도메인 실체가 최소 하나의 클래스에 속함 |
| relation_coverage  | 0.35   | 의미 있는 관계가 모두 정의됨                |
| attribute_coverage | 0.25   | 중요한 속성이 모두 datatype_property로 정의됨 |

---

## Perspective 질문 전략

weakest 차원에 따라 특정 관점의 인터뷰어가 질문을 생성한다.

| weakest 차원                | 인터뷰어 관점                                                            |
|----------------------------|-------------------------------------------------------------------------|
| me / class_boundary_clarity | BOUNDARY_TESTER: 두 클래스 경계가 겹치는 반례를 찾아라                  |
| property_uniqueness         | REDUNDANCY_HUNTER: 같은 의미를 가진 중복 관계를 찾아라                  |
| constraint_consistency      | CONSTRAINT_CHECKER: domain/range 제약이 실제 인스턴스와 충돌하는 케이스 |
| ce / entity_coverage        | EXHAUSTIVENESS_PROBER: 어떤 클래스에도 안 들어가는 도메인 실체를 찾아라 |
| relation_coverage           | RELATION_MAPPER: 아직 정의되지 않은 의미 있는 관계를 찾아라              |
| attribute_coverage          | ATTRIBUTE_AUDITOR: 중요한데 datatype_property로 정의 안 된 속성을 찾아라 |

---

## Deep 전용: Contrarian 체크

매 라운드 채점 후 비판적 관점에서 MECE 위반을 탐색한다.

```json
{
  "finding": "가장 심각한 MECE 위반 한 줄 (없으면 빈 문자열)",
  "open_question": "반드시 명확히 해야 할 미결 질문 (없으면 빈 문자열)"
}
```

- `finding`: 즉시 콘솔에 출력
- `open_question`: `open_questions` 목록에 추적 → 게이트 조건 (`open_questions == []`)

---

## 출력 파일 구조

### graph-ontology.yaml (light/medium/deep)

```yaml
namespace: "http://example.org/kb#"
classes:
  ClassName:
    label: "..."
    entity_dir: "data/classname"
    description: "..."
object_properties:
  propName:
    label: "..."
    domain: ClassName
    range: ClassName
    relation_name: snake_case
    rollup: []
datatype_properties:
  propName:
    label: "..."
    domain: [ClassName]
    range: xsd:string
mece_assessment:
  depth: medium
  score: 0.79
  me_score: 0.83
  ce_score: 0.75
  gate_threshold: 0.75
  rounds_used: 2
  status: seed_ready    # draft | reviewing | seed_ready
  breakdown: {}         # deep에서만 6차원 breakdown 포함
  open_questions: []    # deep에서만 추적
  assessed_at: "2026-04-27"
```

### context/validation/mece-pack-{날짜}.yaml (deep only)

```yaml
ontology_summary:
  classes: [ClassName1, ClassName2, ...]
  object_properties: [propName1, ...]
  datatype_properties: [propName1, ...]
mece_assessment:
  # 위와 동일
interview_log:
  - round: 1
    perspective: "BOUNDARY_TESTER: ..."
    Q: "질문 내용"
    A: "답변 내용"
```
