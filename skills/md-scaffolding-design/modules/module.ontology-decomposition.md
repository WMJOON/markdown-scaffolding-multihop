# module.ontology-decomposition

## 목적

그래프 구조 설계 전에 **주요 Entity를 체계적으로 정의**하는 온톨로지 분해 방법론.
Top-down MECE 분해와 Bottom-up Instance 귀납을 결합하여 Entity를 확정한 후 관계를 매핑한다.

---

## 3단계 프로세스

### Step 1: 주요 Entity 규정

도메인에서 **독립적으로 존재할 수 있는 핵심 개념**을 식별한다.

**기준:**
- 단독으로 파일(노드)이 될 수 있는가?
- 다른 Entity와 관계를 맺는 주체인가?
- 재사용되는 참조 단위인가?

**출력:** Entity 후보 목록 (이름, 설명, 예시 인스턴스)

---

### Step 2-A: Top-down — Concept MECE 분해

도메인 전체를 **상호 배타적이고 전체 포괄적(MECE)**으로 분해하여 Concept 계층을 설계한다.

```
도메인
├── Concept A           ← 최상위 분류
│   ├── Sub-concept A1  ← 중간 분류
│   │   ├── Leaf A1-1   ← Entity (파일화 단위)
│   │   └── Leaf A1-2
│   └── Sub-concept A2
│       └── Leaf A2-1
└── Concept B
    └── ...
```

**MECE 검증:**
- **상호 배타(ME)**: 같은 Instance가 두 Concept에 동시에 속하지 않는가?
- **전체 포괄(CE)**: 도메인의 모든 Instance가 하나의 Concept에 속하는가?

**도구:** 마인드맵 또는 계층 목록으로 먼저 작성, 검증 후 graph-ontology.yaml의 `classes`로 옮긴다.

---

### Step 2-B: Bottom-up — Instance → Concept Entity화

이미 수집된 Instance(파일, 데이터, 메모)에서 **공통 속성을 귀납하여 Concept를 추출**한다.

**절차:**
1. 대표 Instance 10~30개 수집
2. 각 Instance의 공통 속성(frontmatter 키, 제목 패턴, 내용 구조) 추출
3. 공통 속성 묶음 → Concept 이름 부여
4. Top-down Concept와 대조하여 중복·누락 확인

**예시:**

| Instance | 공통 속성 | 귀납된 Concept |
|----------|-----------|----------------|
| `meeting-2024-01.md`, `meeting-2024-02.md` | `date`, `attendees`, `action_items` | `Meeting` |
| `project-alpha.md`, `project-beta.md` | `owner`, `status`, `deadline` | `Project` |
| `person-alice.md`, `person-bob.md` | `role`, `team`, `skills` | `Person` |

**병합 정책:**
- Top-down에 없는 새 Concept → 추가 또는 기존 Concept의 Sub-concept으로 편입
- Top-down Concept 중 Instance 없는 것 → 삭제하거나 비활성 표시

---

### Step 3: 관계 매핑 (Entity 확정 후)

**Entity 정의가 완료된 다음에** 관계를 매핑한다. 관계는 Entity를 먼저 확정하지 않으면 일관성이 무너진다.

**관계 유형:**

| 유형 | 예시 | graph-ontology 표현 |
|------|------|---------------------|
| 계층 (is-a) | `Engineer` is-a `Person` | `subClassOf` |
| 부분-전체 (part-of) | `Task` part-of `Project` | `object_properties.part_of` |
| 연관 (related-to) | `Meeting` mentions `Person` | `object_properties.mentions` |
| 참조 (depends-on) | `Document` depends-on `Concept` | `object_properties.depends_on` |
| 순서 (follows) | `Task` follows `Task` | `object_properties.follows` |

**관계 매핑 순서:**
1. 계층 관계(is-a, part-of) 먼저 — 구조가 명확해짐
2. 강한 연관(depends-on, implements) 다음 — 기능적 의존성
3. 약한 연관(related-to, mentions, see-also) 마지막 — 참조/연결

---

## graph-ontology.yaml 연결

분해 결과를 `graph-ontology.yaml`에 직접 반영한다:

```yaml
classes:
  # Step 1 + 2 결과
  - name: Project
    entity_dir: projects
    description: "독립 실행 단위 작업 묶음"
    scalar_attrs: [title, status, owner, deadline, tags]

  - name: Task
    entity_dir: tasks
    description: "Project의 하위 실행 항목"
    scalar_attrs: [title, status, owner, due_date, tags]

object_properties:
  # Step 3 결과
  - name: part_of
    domain: Task
    range: Project
    wikilink_key: project

  - name: assigned_to
    domain: Task
    range: Person
    wikilink_key: owner
```

---

## Top-down / Bottom-up 선택 가이드

| 상황 | 권장 방법 |
|------|-----------|
| 새 프로젝트, Instance 없음 | Top-down 먼저 |
| 기존 파일 정리 / 레거시 vault 구조화 | Bottom-up 먼저 |
| 표준 도메인 (소프트웨어, 연구, 비즈니스) | Top-down 스케치 → Bottom-up 검증 |
| 도메인 불분명, 탐색적 | Bottom-up으로 패턴 발견 → Top-down 정리 |

**일반 원칙**: 두 방향을 한 번씩 순회하면 서로 누락을 보완한다.
