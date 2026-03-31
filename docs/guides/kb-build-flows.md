# KB 구축 흐름 가이드

Top-Down / Bottom-Up 두 가지 KB 구축 전략과 최적화 루브릭.

> 상세 명세: [`planning/markdown-scaffolding-multihop_v0.1.2-SPEC.md`](../../../planning/markdown-scaffolding-multihop_v0.1.2-SPEC.md)

---

## 전략 선택 기준

| 조건 | 전략 | 이유 |
|------|------|------|
| 도메인 구조 선명 + evidence 미수집 | **Top-Down** | 구조를 먼저 잡고 evidence를 목적에 맞게 수집 |
| 도메인 구조 불명확 + evidence 이미 존재 | **Bottom-Up** | evidence에서 구조를 귀납하는 게 더 빠름 |
| 구조 선명하지만 일부 영역 불명확 | **Top-Down + 부분 Bottom-Up** | 선명한 영역은 Top-Down, 불명확한 영역만 Bottom-Up |

---

## Top-Down Flow (structure-first)

구조가 먼저 선명할 때 사용한다. ontology를 scaffolding한 뒤 evidence를 수집·검증하는 흐름이다.

### 적합한 상황

- 도메인 구조가 이미 어느 정도 선명할 때
- 기술 지도, 온톨로지 설계, 사업계획서처럼 상위 구조가 중요한 경우

### 절차

```
scaffolding (ontology + schema)
  → evidence 수집
    → 데이터 검증 (ontology ↔ evidence)
      → ontology 업데이트
        → 출처 검증 (evidence source validity)
          → evidence 업데이트
            → [반복 or 종료]
```

1. **scaffolding** — `ontology/[concept]/` 구조와 `schema/relation/` type을 먼저 설계
2. **evidence 수집** — 각 instance를 지지할 evidence를 `evidence/[topic]/sources/`에 모음
3. **데이터 검증** — ontology 구조와 evidence 내용의 정합성 확인
4. **ontology 업데이트** — 검증 결과를 반영해 instance frontmatter 보정
5. **출처 검증** — `evidence/[topic]/claims/`에 claim-to-source 매핑 확인
6. **evidence 업데이트** — 출처 검증 결과로 evidence 보정
7. **반복 또는 종료** — 종료 조건 충족 시 `status` 승격

### 루프 탈출

```
데이터 검증 pass
  → 출처 검증 pass
    → 목표 status 달성 → 종료
    → 미달 → 검증 깊이 한 단계 올리고 재시도 (최대 1회)
```

---

## Bottom-Up Flow (evidence-first)

구조가 불명확할 때 사용한다. evidence를 먼저 수집하고 ontology 구조를 점진적으로 추출하는 흐름이다.

### 적합한 상황

- 도메인 구조가 아직 불명확할 때
- 문헌조사, 사례수집, source-heavy domain exploration
- 먼저 사실·근거를 충분히 모아야 할 때

### 절차

```
evidence 수집
  → 출처 검증 (evidence source validity)
    → evidence 업데이트
      → scaffolding (ontology + schema 추출)
        → 데이터 검증 (ontology ↔ evidence)
          → ontology 업데이트
            → [반복 or 종료]
```

1. **evidence 수집** — source note, 문헌, 공식 문서를 `evidence/[topic]/sources/`에 모음
2. **출처 검증** — source validity를 먼저 확인, `claims/`에 기록
3. **evidence 업데이트** — 검증된 근거 기준으로 정리
4. **scaffolding** — 반복 등장하는 concept를 `ontology/[concept]/`로 추출, relation type을 `schema/relation/`에 정의
5. **데이터 검증** — 구조화 결과가 evidence와 맞는지 확인
6. **ontology 업데이트** — instance frontmatter 보정/확장
7. **반복 또는 종료** — 종료 조건 충족 시 `status` 승격

### 루프 탈출

```
출처 검증 pass   ← 항상 선행
  → 데이터 검증 pass
    → 목표 status 달성 → 종료
    → 미달 → evidence 보강 후 재시도 (최대 1회)
```

---

## 핵심 규칙

**Rule 1. ontology ≠ evidence**
- `ontology/` = 구조화 결과 (normalization)
- `evidence/` = 정당화 근거 (justification)
- 둘은 분리되지만 반복적으로 교차 검증된다

**Rule 2. 검증은 두 종류다**
- **데이터 검증**: ontology 구조가 evidence 내용과 맞는가?
- **출처 검증**: evidence source 자체가 유효한가?

**Rule 3. ontology 업데이트는 loop다**
검증 결과에 따라 반복 갱신된다. 단 종료 조건(status 승격 기준)을 명시하지 않으면 무한 루프가 된다.

**Rule 4. 전략 선택 기준**
- 구조가 선명하면 → Top-Down 우선
- 구조가 불명확하면 → Bottom-Up 우선
- 두 흐름은 상호 배타적이 아니다. 같은 KB 안에서 topic별로 다르게 적용할 수 있다.

---

## 최적화 루브릭

> **고정 제약:** evidence의 출처 검증은 깊이에 관계없이 항상 수행한다.
> 출처 없는 evidence는 ontology ETL 대상에서 제외한다.

### 검증 깊이 기준

노드 유형에 따라 검증 수준을 다르게 적용한다.

| 노드 유형 | 예시 | 데이터 검증 | 출처 검증 | 목표 status |
|-----------|------|-----------|-----------|------------|
| **정착된 개념** | RLHF, Transformer, BFS | Light — 구조 배치 확인만 | 1차 출처 1개 확인 | `validated` |
| **도메인 특화 claim** | 특정 벤더 기능, 사내 정책 | Medium — evidence 2개 대조 | 기관·날짜·내용 일치 확인 | `experimental → validated` |
| **신규 synthesis / 해석** | 저자의 주장, 비교 분석 결과 | Deep — 전체 validation pack | 교차 출처 2개 이상, 반박 evidence 탐색 | `draft → experimental` 까지 |

**Light / Medium / Deep 기준:**

| 수준 | 데이터 검증 | 출처 검증 | 권장 중단 기준 |
|------|-----------|-----------|--------------|
| Light | ontology 배치가 MECE에 맞는지만 확인 | URL + 기관명 확인 | 1회 pass면 종료 |
| Medium | evidence 2개 이상에서 claim 교차 확인 | 날짜·버전·저자 확인 | 2회 이내 pass면 종료 |
| Deep | 반박 가능성·예외·한계 탐색 포함 | 독립 출처 2개 이상 + 인용 맥락 확인 | validation pack 완성 시 종료 |

### 공통 강제 종료 조건

- 재시도 1회 후에도 미달이면 status를 한 단계 낮춰 기록하고 종료
  - 예: `validated` 목표 미달 → `experimental`로 기록 후 종료
- 루프를 계속 돌리는 것보다 낮은 status로 기록하는 것이 토큰 효율이 높다
