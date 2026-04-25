---
name: md-scaffolding-design
description: Markdown 디렉토리/GitHub repo에 멀티홉 추론 구조를 설계·저장하는 스캐폴딩 워크플로우. md-graph-multihop의 companion 스킬로 KB 초기화, 구조 설계, 추론 결과 저장을 담당한다.
---

# md-scaffolding-design

`md-graph-multihop`의 companion 스킬. 멀티홉 추론 구조를 **만들고 저장**한다.

## 스크립트

```
scripts/
├── scaffold_project.py   # 프로젝트 분석 → graph-config.yaml 자동 생성
└── save_insight.py       # 추론 결과 → wikilink 연결 md 노드로 저장
```

레퍼런스: `references/api_reference.md` — graph-config.yaml 필드 설명 + 프리셋 상세

---

## 워크플로우 A — 새 프로젝트에 그래프 구조 초기화

### 1. 프로젝트 분석 + graph-config.yaml 생성

```bash
# 로컬 디렉토리 분석
python3 scaffold_project.py --local ./my-docs --output ./graph-config.yaml

# GitHub repo 분석
python3 scaffold_project.py --repo owner/repo --output ./graph-config.yaml

# 프리셋만 사용 (분석 없이 즉시 생성)
python3 scaffold_project.py --template personal-memory --output ./graph-config.yaml
python3 scaffold_project.py --template github-docs     --output ./graph-config.yaml
python3 scaffold_project.py --template git-repo        --output ./graph-config.yaml
python3 scaffold_project.py --template obsidian-vault  --output ./graph-config.yaml
python3 scaffold_project.py --template any-markdown    --output ./graph-config.yaml

# 분석 + 프리셋 병합 (프리셋 기반에 실제 구조 반영)
python3 scaffold_project.py --repo owner/repo --template git-repo --output ./graph-config.yaml

# 사용 가능한 프리셋 목록
python3 scaffold_project.py --list-templates
```

**프리셋 종류:** `personal-memory` | `github-docs` | `git-repo` | `obsidian-vault` | `any-markdown`

### 2. 생성된 graph-config.yaml 검토 및 수정

`references/api_reference.md` 참조.

### 3. md-graph-multihop으로 바로 사용

```bash
python3 graph_builder.py --config graph-config.yaml      # 그래프 구축 확인
python3 graph_rag.py     --config graph-config.yaml --query "..."
python3 github_adapter.py --repo owner/repo --config graph-config.yaml --query "..."
```

---

## 워크플로우 B — 추론 결과를 md 노드로 저장

Claude가 멀티홉 추론으로 뽑은 인사이트를 그래프에 다시 연결되는 노드로 저장한다.

```bash
# 기본 사용
python3 save_insight.py \
  --title "분석 제목" \
  --content "분석 내용..." \
  --links "node-a,node-b" \
  --tags "태그1,태그2" \
  --output ./insights/

# graph-config.yaml의 insight_dir로 자동 경로 설정
python3 save_insight.py \
  --title "분석 제목" \
  --content "내용" \
  --config graph-config.yaml

# stdin 파이프 (Claude 출력을 바로 저장)
echo "추론 결과 텍스트" | python3 save_insight.py \
  --title "제목" \
  --links "node-a,node-b" \
  --config graph-config.yaml
```

저장 후 `graph_builder.py`를 재실행하면 인사이트 노드가 그래프에 포함된다.

---

## 전체 흐름

```
[새 프로젝트]
scaffold_project.py → graph-config.yaml 생성
        ↓
[KB 구축 전략 선택]
  Top-Down: ontology scaffolding → evidence 수집 → 검증
  Bottom-Up: evidence 수집 → ontology 귀납 추출 → 검증
  (전략·검증 깊이·루프 탈출 → docs/guides/kb-build-flows.md 참조)
        ↓
[조회/추론]  md-graph-multihop
graph_builder.py / graph_rag.py / github_adapter.py
        ↓
[결과 저장]
save_insight.py → insights/날짜_제목.md (wikilink 포함)
        ↓
[다음 추론]  새 노드가 그래프에 포함 → 더 깊은 멀티홉 가능
```

---

## 워크플로우 C — KB 유지보수 (Heuristic Rewrite Loop)

KB가 만들어진 이후 entropy가 누적될 때 사용한다.

> 상세 실행 규칙: `modules/module.kb-rewrite-loop.md`

### 언제 트리거하나

- "이 노트 점검해줘" / "KB 품질 확인해줘" / "낡은 노트 찾아줘"
- 새 evidence 추가 후 기존 노드 업데이트 필요 시
- 팀 공유 전 가독성 개선 필요 시
- ontology 변경 후 연관 노드 일관성 확인 시

### 실행 흐름

```
[대상 노드 또는 디렉토리 지정]
        ↓
[Detect] — H-A~H-G heuristic 스캔
        ↓
[Diagnose] — rewrite type 분류 (위험도 Low/Medium/High)
        ↓
[Draft] — rationale 포함한 controlled rewrite
        ↓
[Review] — Low: 자동 반영 / High: human review 요청
        ↓
[Merge] — in-place / variant / sidecar note 선택
        ↓
[Observe] — context/rewrite-log/ 기록 (선택)
```

### 모듈 참조

- `modules/module.kb-rewrite-loop.md` — heuristic 표, rewrite type 분류, merge 정책, log 포맷

---

> **⚠️ 스킬 분리 안내 (2026-04-07)**
> 워크플로우 C (KB 유지보수 / Heuristic Rewrite Loop)는 **`md-kb-rewrite` 스킬**로 분리됐습니다.
> "KB 품질 점검해줘", "노트 개선이 필요해", "rewrite해줘" 등의 요청은 `md-kb-rewrite`를 사용하세요.
> 위의 워크플로우 C 섹션은 참고용으로 남겨두되, 실제 실행 규칙은 `skills/md-kb-rewrite/SKILL.md`를 따릅니다.

---

## 워크플로우 D — Raw → Wiki 컴파일 (Karpathy ingest flow)

> Karpathy: "I index source documents into a raw/ directory, then use an LLM to incrementally compile a wiki."

raw/ 디렉토리에 소스 문서(논문, 기사, 클리핑, 이미지 등)가 쌓였을 때,
LLM이 이를 구조화된 wiki 노드로 컴파일하는 흐름이다.
기존 Bottom-Up flow의 **자동화 버전**이다.

### 언제 트리거하나

- "raw 폴더를 wiki로 변환해줘"
- "소스 문서들을 KB로 컴파일해줘"
- "클리핑한 문서들 정리해줘"
- "새로 수집한 자료들 KB에 넣어줘"
- "ingest해줘"

### 실행 흐름

```
raw/ 디렉토리 스캔
  → 각 소스 문서 읽기 (md, pdf, html 클리핑 등)
  → 문서별로:
      1. 핵심 개념 추출 (ollama_extract_concepts 활용 가능)
      2. 요약 생성 (ollama_summarize 활용 가능)
      3. 기존 ontology 노드와 매핑 — 새 concept이면 stub 생성
      4. evidence/ 에 source note 저장
      5. wikilink로 ontology 노드와 연결
  → index 파일 업데이트
  → 새로 생성된 노드 목록 보고
```

### 출력 규칙

- 기존 노드가 있으면: evidence 추가 + H-E 트리거 (md-kb-rewrite로 위임)
- 신규 개념이면: `ontology/[concept]/` 에 stub 노드 생성 (status: draft)
- 모호하면: 후보 목록만 제시하고 human 결정 대기

### ollama 활용

| 작업 | 도구 |
|------|------|
| 소스 문서 요약 | `ollama_summarize` |
| 개념 추출 | `ollama_extract_concepts` |
| 노드 초안 | `ollama_draft_note` |
| Claude 전담 | 기존 ontology와의 매핑, 새 concept 판단, wikilink 설계 |

### ollama 사용 불가 시 fallback

ollama_mcp 연결이 없거나 tool 호출이 실패하면 Claude가 직접 처리한다.

| 작업 | ollama 사용 시 | fallback (Claude 직접) |
|------|--------------|----------------------|
| 소스 문서 요약 | `ollama_summarize` | Claude가 문서 직접 읽고 요약 |
| 개념 추출 | `ollama_extract_concepts` | Claude가 텍스트 분석 후 개념 목록 추출 |
| 노드 초안 | `ollama_draft_note` | Claude가 frontmatter + 본문 직접 작성 |

**감지 기준:** ollama_mcp 도구 호출 시 오류 반환 또는 MCP 서버 미연결 상태.
**제한사항:** 대량 문서(10개 이상) 배치 처리 시 토큰 비용 증가. 처리 파일 수를 줄이거나 요약 깊이를 낮춰서 진행한다.


### 관련 스킬

- `md-kb-rewrite` H-E: 기존 노드에 evidence가 추가된 경우 freshness 체크
- `md-kb-rewrite` H-X: 컴파일 후 connection candidate 탐색
