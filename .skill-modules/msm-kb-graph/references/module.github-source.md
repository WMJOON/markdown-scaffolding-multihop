# module.github-source

## 목적

GitHub API로 repo의 md 파일을 가져와 그래프를 구성한다. 로컬 클론 불필요.

## 인증 순서

1. `GITHUB_TOKEN` 환경변수
2. `gh auth token` (gh CLI)
3. 미인증 (rate limit: 60 req/hr)

## 파일 목록 조회

`GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1`
→ blob 항목 중 `.md` 확장자만 필터

## 파일 내용 조회

`GET /repos/{owner}/{repo}/contents/{path}`
→ base64 디코딩

## 링크 파싱 (GitHub md)

| 형식 | 추출 방식 |
|------|----------|
| `[[wikilink]]` | wikilink 패턴 |
| `[text](path.md)` | markdown link, `.md` 확장자만 |
| `[text](./path.md)` | 상대경로 정규화 후 node_id 변환 |

## node_id 변환

`docs/guides/setup.md` → `docs__guides__setup`
(슬래시 → `__`, 확장자 제거, NFC 정규화)

## graph-config.yaml 연동

`--config` 옵션으로 graph-config.yaml을 지정하면
`entity_dirs`를 경로 prefix 기반 entity type 분류에 활용한다.
