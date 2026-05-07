---
name: msm-orchestration
description: |-
  MSM(Markdown Scaffolding Multihop) 스킬 팩 오케스트레이터. 상시 로드 스킬.
  Markdown KB 구조화·온톨로지·그래프 작업 관련 모든 요청의 진입점.
  트리거: "멀티홉 추론", "GraphRAG", "그래프 분석", "Knowledge Graph",
  "KB 분석", "인사이트 추출", "데이터 분석",
  "노트 재작성", "KB 정리", "구조 유지보수",
  "MECE 검증", "온톨로지 점검", "온톨로지 확장",
  "Ralph", "ETL", "논문 수집", "URL 크롤링",
  "RDF", "OWL", "온톨로지 브릿지",
  "MSM", "msm", "markdown scaffolding".
---

# msm-orchestration

팩 정의: [references/pack_config.json](references/pack_config.json)

---

## 오케스트레이터 역할

라우터 + 3-Phase 제어기다. 서브스킬 내부 로직(3-Phase 세부, 종료 판정)은 복제하지 않고 서브스킬에 위임한다.  
**전역 원칙**: dry-run 먼저, 사용자 확인 후 apply. 모든 KB 변경 작업에 적용.

---

## 1. 요청 분석 — 인텐트 → 스킬 매핑

| 인텐트 | 신호 키워드 | 담당 스킬 |
|--------|-----------|---------|
| Evidence 수집·온톨로지 확장 | "Ralph", "ETL", "논문 수집", "URL 크롤링", "온톨로지 확장" | [A] ralph-etl 시작 |
| 그래프 설계·멀티홉 추론 | "멀티홉", "GraphRAG", "그래프 분석", "Knowledge Graph" | [B] kb-graph |
| KB 데이터 분석·인사이트 | "KB 분석", "인사이트", "데이터 분석" | [C] data-analysis |
| KB 재작성·구조 유지보수 | "노트 재작성", "KB 정리", "구조 유지보수" | [D] mece-validator → kb-rewrite |
| MECE 검증·온톨로지 점검 | "MECE 검증", "온톨로지 점검", "구조 검증" | mece-validator |
| Obsidian 파일 조작 | "파일 생성", "폴더 이동", "Obsidian CLI" | obsidian-cli |
| RDF/OWL 변환 | "RDF", "OWL", "온톨로지 브릿지", "Turtle" | rdf-owl-bridge |

특정 서브스킬이 직접 언급된 경우: 해당 스킬만 로드하여 위임.

---

## 2. 서브스킬 로드 절차

```
1. 인텐트 → 스킬 결정
2. Read: ~/.skill-modules/msm-skills/{SKILL_NAME}/SKILL.md
3. 3-Phase 프로토콜 확인
4. Phase 0(DESIGN): scope · mode · 종료 기준 사용자와 합의
5. Phase 1(EXECUTE): dry-run → 확인 → apply
6. Phase 2(EVALUATE): 종료 판정 결과 보고
```

---

## 3. 캐노니컬 파이프라인

### [A] 온톨로지 확장 (Ralph ETL)

```
msm-ralph-etl       →  Evidence Seed (.jsonl)
msm-kb-graph        →  그래프 확장 결과
msm-mece-validator  →  구조 검증 리포트
```

Step 1 시작 전 사용자와 scope(URL/파일 목록, similarity threshold) 합의 필수.

### [B] 그래프 설계·멀티홉 추론

```
msm-kb-graph  →  멀티홉 인사이트 / 그래프 구조
```

### [C] KB 분석 → 인사이트

```
msm-data-analysis  →  인사이트 리포트
msm-kb-graph       →  멀티홉 연결 인사이트 (선택)
```

### [D] KB 재구조화

```
msm-mece-validator  →  구조 점검 결과
msm-kb-rewrite      →  재작성 노트
```

---

## 4. 실행 종료 조건

| 파이프라인 | 종료 조건 |
|-----------|---------|
| [A] ETL | Evidence Seed 봉인 완료 + mece-validator 통과 |
| [B] 그래프 | 인사이트 노드 vault 저장 완료 |
| [C] 분석 | 리포트 생성 완료 |
| [D] 재구조화 | 재작성 노트 갱신 + 검증 통과 |

모든 apply 직전 사용자 확인 게이트 통과 필수.

---

## 설치

```bash
git clone https://github.com/WMJOON/markdown-scaffolding-multihop.git
cd markdown-scaffolding-multihop
./install.sh
```

## 거버넌스 검증

```bash
python3 ~/.claude/skills/mso-skill-governance/scripts/validate_gov.py \
  --pack-root ~/.claude --pack msm --json
```
