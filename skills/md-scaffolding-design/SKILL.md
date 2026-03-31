---
name: md-scaffolding-design
description: >
  로컬 Markdown 디렉토리 또는 GitHub repo에 멀티홉 추론 구조를 설계하고 저장하는 스캐폴딩 워크플로우.
  md-graph-multihop의 companion 스킬로, "조회/추론"이 아니라 "구조 설계 + 저장"을 담당한다.
  KB 디렉토리 구조 원칙(ontology/ ABox + schema/ TBox + evidence/ + context/ + docs/)을 기반으로,
  Evidence → Ontology ETL → Node Link → Validation 흐름에 따라 지식 구조를 초기화·확장한다.
  (1) 프로젝트 디렉토리/GitHub repo를 분석해 graph-config.yaml을 자동 생성하거나,
  (2) personal-memory·github-docs·git-repo·obsidian-vault·kb-structure 등 프리셋으로 즉시 구조를 초기화하거나,
  (3) Claude의 멀티홉 추론 결과를 wikilink가 연결된 md 인사이트 노드로 저장할 때 사용한다.
  Obsidian path:ontology/ 필터 및 Neo4j 확장을 염두에 둔 ABox/TBox 분리 구조를 지원한다.
  트리거 예시: "이 레포에 GraphRAG 구조 만들어줘", "멀티홉용 config 생성해줘",
  "추론 결과를 노드로 저장해줘", "graph-config 자동 생성해줘", "git repo에 그래프 구조 세팅해줘",
  "온톨로지 설계해줘", "Entity 정의해줘", "top-down 분해해줘", "KB 구조 초기화해줘",
  "evidence 폴더 만들어줘", "schema 정의해줘".
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
[조회/추론]  md-graph-multihop
graph_builder.py / graph_rag.py / github_adapter.py
        ↓
[결과 저장]
save_insight.py → insights/날짜_제목.md (wikilink 포함)
        ↓
[다음 추론]  새 노드가 그래프에 포함 → 더 깊은 멀티홉 가능
```
