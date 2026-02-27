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
