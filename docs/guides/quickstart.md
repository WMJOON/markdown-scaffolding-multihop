# 빠른 시작

## 설치

```bash
pip install -r requirements.txt
```

## 지원 소스

| 소스 | 설명 |
|------|------|
| **로컬 디렉토리** | 모든 Markdown 파일 (Obsidian vault 포함) |
| **GitHub 레포** | GitHub API 경유, 로컬 클론 불필요 |
| **Git 레포 (로컬)** | git clone 후 로컬 파일로 처리 |

## 기본 사용

```bash
# 1. KB 구조 초기화
python3 skills/md-scaffolding-design/scripts/scaffold_project.py \
  --local ./my-kb --template kb-structure --output graph-config.yaml

# 2. 그래프 구축 확인
python3 skills/md-graph-multihop/scripts/graph_builder.py

# 3-a. 키워드 검색 + 멀티홉 추론
python3 skills/md-graph-multihop/scripts/graph_rag.py \
  --query "X와 Y의 관계는?" --hops 2 --context-only

# 3-b. 벡터 인덱싱 → 시맨틱 검색
python3 skills/md-vector-search/scripts/zvec_graph_index.py index
python3 skills/md-vector-search/scripts/zvec_graph_index.py search "시장 진입 전략"

# 4. 롤업 (값 집계)
python3 skills/md-frontmatter-rollup/scripts/rollup_engine.py --dry-run
```

## GitHub repo 대상

```bash
python3 skills/md-graph-multihop/scripts/github_adapter.py \
  --repo owner/repo --config graph-config.yaml --query "..."
```
