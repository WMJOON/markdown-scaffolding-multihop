# markdown-scaffolding-multihop

Markdown 기반 지식 베이스를 위한 **GraphRAG 스킬셋**.
로컬 파일 시스템(Obsidian 포함)과 Git 레포지토리 모두에서 동작한다.
그래프 구축 → 멀티홉 추론 → 구조 설계 → 값 집계를 통합 제공한다.

## 스킬 구성

| 스킬 | 역할 |
|------|------|
| `md-graph-multihop` | 그래프 구축 + 멀티홉 추론 (조회) |
| `md-scaffolding-design` | 구조 설계 + 추론 결과 저장 |
| `md-frontmatter-rollup` | 엣지 기반 frontmatter 값 집계 |

## 지원 소스

| 소스 | 설명 |
|------|------|
| **로컬 디렉토리** | 모든 Markdown 파일 (Obsidian vault 포함) |
| **GitHub 레포** | GitHub API 경유, 로컬 클론 불필요 |
| **Git 레포 (로컬)** | git clone 후 로컬 파일로 처리 |

## 설정 방식

### A. OWL 온톨로지 (권장)

`graph-ontology.yaml` 파일 하나로 그래프 구조와 집계 규칙을 선언한다.
graph-config.yaml + rollup-config.yaml을 자동 도출한다.

```bash
cp graph-ontology.example.yaml graph-ontology.yaml
# 편집 후:
python3 skills/md-frontmatter-rollup/scripts/rollup_engine.py --ontology graph-ontology.yaml
```

### B. 분리 설정 (레거시 호환)

`graph-config.yaml` + `rollup-config.yaml` 조합. 기존 방식 그대로 사용 가능.

## 빠른 시작

```bash
pip install -r requirements.txt

# 1. 프로젝트 초기화 (로컬)
python3 skills/md-scaffolding-design/scripts/scaffold_project.py \
  --local ./my-docs --template github-docs --output graph-config.yaml

# 1-b. GitHub 레포에서 초기화
python3 skills/md-scaffolding-design/scripts/scaffold_project.py \
  --repo owner/repo --template git-repo --output graph-config.yaml

# 2. 그래프 확인
python3 skills/md-graph-multihop/scripts/graph_builder.py

# 3. 멀티홉 질의 (로컬)
python3 skills/md-graph-multihop/scripts/graph_rag.py \
  --query "X와 Y의 관계는?" --context-only

# 3-b. GitHub 레포 직접 질의
python3 skills/md-graph-multihop/scripts/github_adapter.py \
  --repo owner/repo --query "X와 Y의 관계는?"

# 4. 롤업 실행
python3 skills/md-frontmatter-rollup/scripts/rollup_engine.py --dry-run
```

## 설정 파일

| 파일 | 용도 |
|------|------|
| `graph-ontology.yaml` | OWL 스타일 단일 진실 소스 (권장) |
| `graph-config.yaml` | entity_dirs / relation_map / scalar_node_attrs |
| `rollup-config.yaml` | rollup_rules (집계 규칙, 레거시 호환) |

## 디렉토리 구조

```
repository/
├── README.md
├── requirements.txt
├── graph-ontology.example.yaml     # OWL 설정 예시
├── skills/
│   ├── md-graph-multihop/          # 그래프 구축 + 멀티홉 추론
│   ├── md-scaffolding-design/      # 구조 설계 + 결과 저장
│   └── md-frontmatter-rollup/      # frontmatter 값 집계
└── tests/
```
