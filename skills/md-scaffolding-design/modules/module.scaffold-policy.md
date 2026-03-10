# module.scaffold-policy

## 목적

프로젝트 디렉토리 또는 GitHub repo를 분석해 graph-config.yaml을 자동 생성한다.

## 분석 방법

### 로컬 디렉토리 (`--local`)
- `os.walk`로 `.md` 파일이 있는 폴더 탐색 (최대 depth 3)
- 무시 디렉토리: `.git`, `.github`, `node_modules`, `__pycache__`, `.obsidian`, `dist`, `build` 등
- md 파일 수 기준으로 폴더 중요도 판단

### GitHub repo (`--repo`)
- `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1`
- blob 항목 중 `.md` 파일 경로에서 부모 디렉토리 추출

## 프리셋 정책

| 프리셋 | 대상 |
|--------|------|
| `personal-memory` | 제텔카스텐 / 개인 지식 베이스 / 일간노트 |
| `github-docs` | GitHub 프로젝트 docs/ 기반 |
| `git-repo` | 일반 Git 레포 (README, docs, wiki 포함) |
| `obsidian-vault` | Obsidian vault (entity 노드 + wikilink) |
| `any-markdown` | 임의 Markdown 디렉토리 (최소 설정) |

프리셋 + 분석 결과 병합 시: 프리셋 entity_dirs가 기본값, 분석 결과로 미발견 디렉토리 보완.

## entity 타입 추론

디렉토리명을 entity 타입으로 변환:
- 소문자화, `-` `공백` → `_`
- 단순 복수형 정규화 (notes → note, guides → guide)

## 온톨로지 분해 연계

`scaffold_project.py`로 자동 생성된 `entity_dirs`는 **온톨로지 분해의 출발점**이다.
생성된 config를 그대로 사용하기 전에 `module.ontology-decomposition.md`의 3단계 프로세스를 따라 Entity와 관계를 정제하는 것을 권장한다:

1. **Step 1** — 자동 추출된 entity 목록에서 주요 Entity를 확정 (불필요 항목 제거, 누락 항목 추가)
2. **Step 2** — Top-down으로 Concept 계층 검증 + Bottom-up으로 실제 파일 패턴과 대조
3. **Step 3** — Entity 확정 후 `relation_map` 정의 (관계는 Entity 확정 전에 정의하지 않는다)
