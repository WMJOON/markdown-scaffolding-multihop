# KB 유지보수 가이드 ― Heuristic Rewrite Loop

> 이 가이드는 `module.kb-rewrite-loop.md`의 사용법을 실제 시나리오 중심으로 설명한다.

---

## 언제 이 가이드가 필요한가

KB를 구축(Top-Down / Bottom-Up)한 이후에 다음 상황이 생기면 이 루프를 쓴다:

- 노트가 너무 길어져서 읽기 어려워졌다
- 같은 내용이 여러 노트에 흩어져 있다
- 새 논문을 추가했는데 기존 노드에 반영이 안 됐다
- ontology를 바꿨는데 article 노트는 예전 표현 그대로다
- 팀원이 "이 문서 이해하기 어렵다"고 했다
- 특정 프레이밍이 너무 고착돼서 다양한 관점이 사라졌다
- raw/ 에 쌓인 소스 문서를 wiki 노드로 컴파일해야 한다 *(→ Workflow D)*
- 연결되어야 할 합성 노드나 글이 링크 없이 고립되어 있다 *(→ H-X)*

---

## 시나리오 1: 새 논문 추가 후 기존 노드 업데이트

**heuristic**: H-E (Evidence Freshness)
**rewrite type**: evidence-integrating rewrite
**위험도**: Medium

```
1. evidence 수집
   → evidence/[topic]/sources/ 에 새 논문 노트 추가
   
2. Detect
   → 이 evidence와 연결된 ontology 노드 확인
   → 본문이 새 evidence를 반영하지 않음 → H-E 트리거

3. Draft
   → rationale: "PMC12913532 추가로 claim 강도 조정 필요"
   → 바꾼 것: "~로 알려져 있다" → "~임이 확인됐다 (PMC12913532)"
   → 유지한 것: 구조, 기존 citations

4. Review: Medium 위험도 → variant 파일 생성
   → output-assetization-v2.md 으로 저장 후 검토

5. Merge: 승인 시 in-place overwrite
```

---

## 시나리오 2: 팀 공유 전 가독성 점검

**heuristic**: H-F (Readability)
**rewrite type**: readability rewrite / format rewrite
**위험도**: Low

```
1. Detect
   → heading 5개 이상, bold 과다, 단락 없이 bullet만 나열 → H-F 트리거

2. Diagnose
   → readability rewrite + format rewrite (Low)

3. Draft
   → bullet → prose 전환, heading 축소, 서두 summary 추가
   → rationale 필요 없음 (Low-risk)

4. Review: 자동 반영 가능

5. Merge: in-place overwrite
```

---

## 시나리오 3: Semantic Bias 발견

**heuristic**: H-G (Semantic Bias)
**rewrite type**: framing rewrite
**위험도**: High

```
1. Detect
   → 한 가지 프레이밍만 대표 해석처럼 고착
   → uncertainty 표현이 삭제됨
   → alternative framing 부재 → H-G 트리거

2. Diagnose
   → framing rewrite (High)

3. Draft
   → alternative framing 섹션 추가
   → "~이다" → "~로 볼 수 있다 / ~라는 해석도 있다" 완화
   → rationale: "semantic bias 발견, framing 다양화"

4. Review: High → 반드시 human review
   → sidecar note 생성: [filename]-rewrite-rationale.md

5. Merge: human 승인 후 variant로 저장
```

---

## 시나리오 4: 연결 누락 노드 발견 (H-X Connection Candidate)

**heuristic**: H-X (Connection Candidate)
**rewrite type**: link-enriching rewrite
**위험도**: Low~Medium

H-X는 합성 노드(synthesis note) 또는 글(article)이 관련 ontology 노드와 연결되지 않아 그래프에서 고립된 경우를 탐지한다.

```
1. Detect
   → orphan 노드 스캔: wikilink 0개인 synthesis/article 노드 발견
   → 또는 BFS 서브그래프에서 도달 불가 노드 발견
   → H-X 트리거

2. Diagnose
   → 후보 링크 목록 생성:
     - 같은 concept을 참조하는 ontology 노드
     - 유사 키워드를 가진 evidence 노드
     - 상위/하위 concept 관계

3. Draft
   → 본문 내 자연스러운 위치에 wikilink 삽입
   → frontmatter의 related: 필드 추가 또는 갱신
   → rationale: "H-X: [[target-node]] 연결 누락 발견"

4. Review
   → Low-risk (새 링크 추가만): 자동 반영 가능
   → Medium-risk (기존 링크 변경 포함): variant 파일 생성 후 검토

5. Merge: 승인 시 in-place overwrite
```

**ollama_mcp 위임 예시 (H-X 자동 탐지):**
```
ollama_extract_concepts(note_content) → candidate_concepts 목록 추출
→ KB graph에서 candidate_concepts와 매칭되는 노드 검색
→ 연결 누락 쌍 발견 시 H-X 트리거
```

---

## 시나리오 5: Raw 문서 → Wiki 노드 컴파일 (Workflow D)

**workflow**: Workflow D (Raw→Wiki Compile)
**출처**: Karpathy LLM Knowledge Bases 포스트 인사이트 적용

raw/ 디렉토리에 쌓인 정제되지 않은 소스 문서(클리핑, 메모, 논문 초록 등)를 구조화된 wiki 노드로 컴파일할 때 사용한다.

```
1. raw/ 스캔
   → raw/[topic]/ 아래 처리되지 않은 문서 목록 수집
   → frontmatter에 status: raw 또는 processed 없음 확인

2. 분류 (Diagnose)
   → 각 raw 문서에 대해:
     a. concept 노드로 승격 가능한가? → ontology/[concept]/[instance].md
     b. evidence 노드인가? → evidence/[topic]/sources/
     c. synthesis 대상인가? → article/ 또는 ontology/ 합성 노드

3. 컴파일 (Draft)
   → 대상 경로와 frontmatter 스캐폴드 생성:
     - title, concept, status: draft, source, created
   → 본문: raw 내용 → 구조화된 prose/섹션으로 재작성
   → wikilink 연결: 관련 concept · evidence 노드 링크 삽입

4. ollama_mcp 위임 (저위험 초안)
   → ollama_draft_note(raw_content, target_schema) 호출
   → 결과 검토 후 ontology/ 또는 evidence/ 에 배치

5. Validation 승격
   → status: draft → experimental (1차 검토 후)
   → status: experimental → validated (cross-link 검증 후)

6. raw/ 아카이브
   → 처리 완료된 raw 문서: frontmatter에 status: processed 추가
   → 또는 context/migration/ 으로 이동
```

**디렉토리 예시:**
```
raw/
  llm-knowledge-bases/
    karpathy-post-notes.md      ← status: raw
    memory-architecture-clip.md ← status: raw

→ 컴파일 후:

ontology/
  knowledge-management/
    llm-knowledge-base.md       ← status: draft, source: karpathy-post
evidence/
  llm-knowledge-bases/
    sources/
      karpathy-2024.md
```

---

## 디렉토리 스캔 방법

특정 폴더 전체를 점검할 때:

```
Claude에게 요청: "10_Agent_KnowledgeBase/ontology/ 폴더 KB 품질 점검해줘"
→ H-A 우선 적용 (너무 긴 노드 탐지)
→ H-F 적용 (가독성 낮은 노드 탐지)
→ H-B 적용 (중복 노드 탐지, 유사 내용 비교)
→ H-C/H-D는 링크가 있는 노드에만 적용
→ H-E는 evidence/ 폴더에 최근 변경이 있을 경우 적용
→ H-G는 별도 요청 시에만 적용 (자동 스캔 비용 높음)
→ H-X는 orphan 노드 스캔 후 자동 적용 가능 (ollama_mcp 위임 권장)
```

---

## ollama_mcp 위임 결정 기준

| 작업 | 휴리스틱 | ollama 위임 여부 | 이유 |
|------|----------|-----------------|------|
| 유사 노드 비교 | H-B | ? `ollama_extract_concepts` | 반복적 텍스트 비교 |
| 가독성 초안 | H-F | ? `ollama_complete` | Low-risk 포맷 정리 |
| Raw 초안 생성 | Workflow D | ? `ollama_draft_note` | 저위험 구조화 작업 |
| 연결 후보 탐지 | H-X | ? `ollama_extract_concepts` | concept 추출 반복 작업 |
| Semantic Bias | H-G | ? Claude 직접 | 판단 정밀도 필요 |
| Evidence 통합 | H-E | ? Claude 직접 | claim 강도 판단 필요 |
| Framing rewrite | H-G | ? Claude 직접 | 고위험, 맥락 의존적 |

---

## Rewrite Log 예시

```yaml
# context/rewrite-log/2026-04-06-output-assetization.md
target_note: ontology/ax-org-mgmt/output-assetization.md
date: 2026-04-06
heuristic_trigger: H-E
rewrite_type: evidence-integrating rewrite
auto_or_reviewed: reviewed
accepted: true
rejection_reason: ~
notes: "PMC12913532 반영, claim 강도 조정"
```

---

## 관련 문서

- `modules/module.kb-rewrite-loop.md` ― 전체 루프 규칙 및 heuristic 표
- `guides/kb-build-flows.md` ― Top-Down / Bottom-Up 구축 흐름
- `planning/kb-heuristic-rewrite-loop.md` ― 설계 철학 및 원칙