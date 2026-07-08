# Semantic Relations

이 문서는 MSM v0.14.0의 relation 후보와 axiom 후보를 사람이 검토할 때 쓰는 predicate 설명서다.

`msm-semantic-search link-relations`는 zvec으로 의미상 가까운 chunk를 찾고, chunk 안의 source/target mention 주변 문맥을 읽어 relation 후보를 만든다. 이 단계의 산출물은 정본이 아니라 `evidence/semantic-link/relation_candidates.jsonl` review queue다. `relations.jsonl` 승격은 source validation 이후 `msm-ontology`가 수행한다.

---

## 후보 레코드 원칙

relation 후보는 최소한 다음 정보를 가져야 한다.

| 필드 | 의미 |
|------|------|
| `source`, `target` | 관계 양끝의 entity id |
| `predicate` | 제안된 관계 유형 |
| `confidence` | semantic score, mention match, direction cue를 합성한 후보 신뢰도 |
| `semantic_score` | zvec 검색 점수 |
| `matched_terms` | target entity로 인정한 표면어 |
| `direction_evidence` | 방향을 판단한 cue, 문장/창 단위 근거 |
| `evidence.source_path` | 후보를 만든 원문 또는 chunk 파일 |
| `source_refs` | 검증된 evidence seed. 비어 있으면 정본 승격 금지 |
| `requires_source_validation` | 원문/seed 검증 필요 여부 |

승격 전 필수 조건:

- `source_refs`가 비어 있으면 `relations.jsonl`에 쓰지 않는다.
- `related_to`는 약한 관계이므로 자동 승격보다 큐레이션/재탐색 신호로 사용한다.
- directed predicate는 방향이 의미를 바꾸므로 source/target을 뒤집을 수 있는지 반드시 확인한다.
- L2 이상 axiom 후보는 relation 후보와 별도 큐인 `evidence/semantic-link/axiom_candidates.jsonl`로 보낸다.

---

## L0 Observed Relations

L0는 문서에서 관측 가능한 약한 사실이다. graph-wide inference를 거의 만들지 않으므로 자동 후보 생성은 가능하지만, 정본 적용은 저장소 정책에 따른다.

| Predicate | 방향 | 의미 | 좋은 근거 | 오염 리스크 |
|-----------|------|------|-----------|-------------|
| `mentions` | source → target | source 문서나 chunk가 target을 언급한다 | 같은 chunk 안 명시적 명명 | 낮음 |
| `cites` | source → target | source가 target 문서·논문·URL을 인용한다 | citation, URL, reference marker | 낮음 |
| `co_occurs_with` | 무방향 | 두 entity가 같은 chunk/window에서 반복적으로 함께 나타난다 | 여러 chunk의 공출현 | 낮음~중간 |
| `has_source` | entity → evidence | entity 정의나 claim이 특정 evidence에 의해 뒷받침된다 | `source_refs`, 원문 라인 | 낮음 |
| `describes` | source → target | source 문서가 target의 속성·정의·절차를 설명한다 | 정의문, “is/means/refers to” 문맥 | 낮음~중간 |

운영 기준:

- `mentions`, `co_occurs_with`는 탐색 보조 신호다. ontology 의미 관계로 과해석하지 않는다.
- `has_source`는 다른 모든 승격의 기반이다.

---

## L1 Directed Fact Relations

L1은 chunk 내용을 읽어 방향을 제안할 수 있는 사실 관계다. 후보 생성은 가능하지만 자동 적용은 금지한다.

| Predicate | 방향 의미 | 사용 기준 | 반대 방향 후보 |
|-----------|-----------|-----------|----------------|
| `depends_on` | source가 target에 의존한다 | “requires”, “based on”, “built on”, “의존”, “기반” | `supports`, `enables`일 수 있음 |
| `implements` | source가 target을 구현한다 | 코드/절차/컴포넌트가 개념·인터페이스·정책을 실현 | `implemented_by` |
| `enables` | source가 target을 가능하게 한다 | 기술·정책·구조가 결과나 능력을 열어줌 | `enabled_by`, `depends_on` |
| `uses` | source가 target을 사용한다 | 도구, 데이터, API, 방법론을 수단으로 씀 | `used_by` |
| `contains` | source가 target을 포함한다 | 문서·모듈·클러스터가 구성요소를 포함 | `part_of` |
| `part_of` | source가 target의 일부다 | 하위 개념/구성요소/섹션이 상위 구조에 속함 | `contains` |
| `extends` | source가 target을 확장한다 | 기존 개념/기능/스키마에 기능을 추가 | `extended_by` |
| `optimizes` | source가 target을 최적화한다 | 비용, 품질, 속도, 검색성 같은 목표를 개선 | `optimized_by` |
| `causes` | source가 target을 유발한다 | 명시적 인과 표현, 실험/사례 기반 결과 | `caused_by` |
| `maps_to` | source가 target에 매핑된다 | 필드·개념·스키마 간 대응 | `mapped_from` |
| `contrasts_with` | 무방향에 가까움 | 두 개념의 차이·대립·trade-off를 설명 | 보통 동일 predicate |
| `related_to` | 약한 연결 | 방향 cue가 약하거나 cross-sentence fallback | 승격 전 재분류 필요 |

운영 기준:

- `depends_on`과 `enables`는 자주 뒤집힌다. “A needs B”는 `A depends_on B`, “A makes B possible”은 `A enables B`다.
- `contains`/`part_of`는 구조 관계다. 개념적 유사성만으로 쓰지 않는다.
- `causes`는 가장 오염 위험이 큰 L1 관계다. 단순 시간순/공출현을 인과로 승격하지 않는다.
- `maps_to`는 양쪽 스키마/필드/분류 체계가 명확할 때 쓴다.
- `related_to`는 최종 relation이라기보다 “더 읽어야 할 연결”에 가깝다.

---

## L2 RBox Lightweight Axioms

L2부터는 relation이 아니라 relation schema에 대한 공리다. 후보만 만들고 자동 적용하지 않는다.

| Axiom | 의미 | 필요 검증 | 리스크 |
|-------|------|-----------|--------|
| `inverse_of` | 두 predicate가 서로 역관계다 | 모든 대표 사례에서 방향 반전이 성립하는지 | 중간 |
| `subPropertyOf` | 한 predicate가 더 일반 predicate의 하위다 | 하위 관계가 항상 상위 관계를 함의하는지 | 중간 |
| `domain` | predicate의 source class 제한 | 기존 ABox source들이 위반하지 않는지 | 중간~높음 |
| `range` | predicate의 target class 제한 | 기존 ABox target들이 위반하지 않는지 | 중간~높음 |

예시:

- `implemented_by inverse_of implements`
- `uses subPropertyOf depends_on`은 항상 맞지 않을 수 있다. “사용하지만 의존하지 않는” 사례가 있으면 보류한다.

---

## L3 RBox Propagation Axioms

L3는 추론 결과를 넓게 전파한다. HITL과 graph diff preview가 필수다.

| Axiom | 의미 | 오염 가능성 |
|-------|------|-------------|
| `TransitiveProperty` | A→B, B→C이면 A→C를 추론 | 긴 체인에서 과잉 연결 생성 |
| `SymmetricProperty` | A→B이면 B→A를 추론 | 방향 의미가 있는 predicate에 적용하면 오염 |
| `AsymmetricProperty` | A→B이면 B→A 불가 | 예외 사례가 있으면 충돌 |
| `propertyChain` | predicate 조합으로 새 predicate 추론 | 한 번 승인하면 다수 inferred edge 생성 |

운영 기준:

- `part_of`는 transitive 후보가 될 수 있지만, “멤버십”, “문서 섹션”, “개념 하위분류”가 섞이면 오염된다.
- `propertyChain`은 반드시 예상 inferred edge 수와 충돌 edge를 preview한다.

---

## L4 TBox Class Axioms

L4는 class 구조를 바꾼다. ontology 탐색 경로, 분류 결과, future extraction 기준에 영향을 준다.

| Axiom | 의미 | 필요 검증 |
|-------|------|-----------|
| `subClassOf` | 한 class가 다른 class의 하위다 | 단일 부모/MECE 정책과 충돌하지 않는지 |
| `classification_rule` | instance를 class로 분류하는 조건 | false positive/negative 사례 |
| `someValuesFrom` | 특정 relation이 최소 하나의 target class를 가져야 함 | 실제 데이터 누락인지 구조 규칙인지 |
| `cardinality` | relation 개수 제한 | 예외 instance와 시간 변화 |
| `intersectionOf` | 여러 class 조건을 동시에 만족하는 class | 조건 조합이 과도하게 좁지 않은지 |

운영 기준:

- `subClassOf`는 디렉토리 이동이 아니라 class 의미 결정이다.
- `classification_rule`은 자동 분류기를 만든다. 잘못 승인하면 이후 후보 생성이 계속 오염된다.

---

## L5 Negative / Disjoint Axioms

L5는 “동시에 참이면 안 된다”는 부정 제약이다. 별도 승인과 충돌 검사가 필수다.

| Axiom | 의미 | 반드시 물어야 할 질문 |
|-------|------|----------------------|
| `disjointWith` | 두 class는 겹칠 수 없다 | 실제 instance가 양쪽에 속할 수 있는가? |
| `AllDisjointClasses` | 여러 class가 상호 배타적이다 | 분류 체계가 완전하고 안정적인가? |
| `propertyDisjointWith` | 두 predicate가 동시에 성립할 수 없다 | 한 쌍의 entity에 양쪽 관계가 모두 가능한가? |
| `complementOf` | 한 class가 다른 class의 보집합이다 | universe boundary가 명확한가? |
| `FunctionalProperty` | source당 target이 최대 하나다 | 시간 변화/버전/복수 소속 예외가 없는가? |
| `InverseFunctionalProperty` | target당 source가 최대 하나다 | shared target이나 alias가 없는가? |

운영 기준:

- “서로 달라 보인다”는 `disjointWith` 근거가 아니다.
- L5 승격 전에는 기존 ABox 충돌, 새 inferred 충돌, future ingestion에 미칠 영향을 모두 본다.

---

## ELT에서의 위치

v0.14.0 이후 KB 구축은 ETL보다 ELT에 가깝다.

```text
Extract   원문, URL, Markdown, graph.json, 기존 ontology registry를 수집
Load      evidence/, zvec index, relation_candidates.jsonl, axiom_candidates.jsonl에 보존
Transform source validation, MECE, HITL, inference preview 이후 ontology 정본으로 승격
```

이 모델에서는 `evidence/`와 candidate queue가 먼저 쌓이고, ontology 정본은 검증된 subset만 받아들인다. 따라서 semantic relation과 axiom inference는 정본 작성기가 아니라 검토 가능한 변환 후보 생성기로 다룬다.
