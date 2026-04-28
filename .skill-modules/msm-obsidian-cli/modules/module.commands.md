# module.commands — Obsidian CLI 명령 레퍼런스

출처: [Obsidian CLI 공식 문서](https://help.obsidian.md/cli)
버전: Obsidian 1.12+

---

## General

| 명령 | 설명 |
|------|------|
| `help [<command>]` | 전체 명령 목록 / 특정 명령 도움말 |
| `version` | Obsidian 버전 출력 |
| `reload` | 앱 창 리로드 |
| `restart` | 앱 재시작 |

---

## Files and Folders

### `file`
파일 정보 조회 (기본: 활성 파일)
```
file=<name>   path=<path>
```

### `files`
vault 파일 목록
```
folder=<path>   ext=<extension>   total
```

### `folder` / `folders`
```
path=<path>  info=files|folders|size    # folder
folder=<path>  total                    # folders
```

### `open`
파일 열기
```
file=<name>   path=<path>   newtab
```

### `create`
파일 생성/덮어쓰기
```
name=<name>   path=<path>   content=<text>   template=<name>
overwrite   open   newtab
```

### `read`
파일 내용 읽기 (기본: 활성 파일)
```
file=<name>   path=<path>
```

### `append`
파일 끝에 내용 추가 (기본: 활성 파일)
```
file=<name>   path=<path>   content=<text> (required)   inline
```

### `prepend`
frontmatter 다음에 내용 삽입 (기본: 활성 파일)
```
file=<name>   path=<path>   content=<text> (required)   inline
```

### `move`
파일 이동 (링크 자동 업데이트)
```
file=<name>   path=<path>   to=<path> (required)
```

### `rename`
파일 이름 변경 (확장자 자동 보존, 링크 업데이트)
```
file=<name>   path=<path>   name=<name> (required)
```

### `delete`
파일 삭제 (기본: 휴지통)
```
file=<name>   path=<path>   permanent
```

---

## Daily Notes

| 명령 | 설명 |
|------|------|
| `daily` | 오늘 일간 노트 열기 |
| `daily:path` | 일간 노트 경로 반환 (미생성 시에도 반환) |
| `daily:read` | 일간 노트 내용 읽기 |
| `daily:append content=<text>` | 내용 추가 (`inline`, `open` 플래그) |
| `daily:prepend content=<text>` | 내용 앞에 삽입 (`inline`, `open` 플래그) |

```bash
obsidian daily
obsidian daily:append content="- [ ] Buy groceries"
obsidian daily:read --copy
```

---

## Search

### `search`
파일 경로 목록 반환
```
query=<text> (required)   path=<folder>   limit=<n>
format=text|json   total   case
```

### `search:context`
grep 스타일 `path:line: text` 출력
```
query=<text> (required)   path=<folder>   limit=<n>   format=text|json   case
```

### `search:open`
검색 패널 열기
```
query=<text>
```

---

## Tasks

### `tasks`
태스크 목록 (기본: 전체 vault)
```
file=<name>   path=<path>   status="<char>"
total   done   todo   verbose   format=json|tsv|csv
active   daily
```

예시:
```bash
obsidian tasks todo                    # 미완료 태스크
obsidian tasks daily                   # 오늘 일간 노트 태스크
obsidian tasks file=Recipe done        # 특정 파일 완료 태스크
obsidian tasks verbose                 # 파일 경로·줄 번호 포함
obsidian tasks 'status=?'             # 커스텀 상태 필터
```

### `task`
태스크 조회/업데이트
```
ref=<path:line>   file=<name>   path=<path>   line=<n>
status="<char>"   toggle   done   todo   daily
```

예시:
```bash
obsidian task file=Recipe line=8 toggle
obsidian task ref="Recipe.md:8" done
obsidian task daily line=3 status=-
```

---

## Properties

| 명령 | 설명 |
|------|------|
| `aliases` | 별칭 목록 (`file`, `path`, `active`, `total`, `verbose`) |
| `properties` | 속성 목록 (`format=yaml|json|tsv`, `counts`, `active`) |
| `property:set name=<n> value=<v> [type=...]` | 속성 설정 |
| `property:remove name=<n>` | 속성 제거 |
| `property:read name=<n>` | 속성 값 읽기 |

```bash
obsidian property:set name=status value=active type=text file=Note
obsidian property:read name=tags file=Note
obsidian properties file=Note format=json
```

---

## Tags

| 명령 | 설명 |
|------|------|
| `tags` | 태그 목록 (`counts`, `sort=count`, `format=json|tsv|csv`, `active`) |
| `tag name=<tag>` | 특정 태그 정보 (`total`, `verbose`) |

---

## Bookmarks

| 명령 | 설명 |
|------|------|
| `bookmarks` | 북마크 목록 (`total`, `verbose`, `format=json|tsv|csv`) |
| `bookmark` | 북마크 추가 (`file`, `folder`, `search`, `url`, `title`, `subpath`) |

---

## Command Palette

| 명령 | 설명 |
|------|------|
| `commands [filter=<prefix>]` | 명령 ID 목록 |
| `command id=<id>` | Obsidian 명령 실행 |
| `hotkeys` | 단축키 목록 (`total`, `verbose`, `format`) |
| `hotkey id=<id>` | 특정 명령 단축키 |

---

## Templates

| 명령 | 설명 |
|------|------|
| `templates` | 템플릿 목록 |
| `template:read name=<template>` | 템플릿 내용 읽기 (`resolve`, `title=<title>`) |
| `template:insert name=<template>` | 활성 파일에 템플릿 삽입 |

---

## Links

| 명령 | 설명 |
|------|------|
| `backlinks` | 역링크 목록 (`counts`, `total`, `format`) |
| `links` | 아웃고잉 링크 (`total`) |
| `unresolved` | 미해결 링크 (`total`, `counts`, `verbose`, `format`) |
| `orphans` | 링크 없는 파일 (`total`) |
| `deadends` | 아웃고잉 링크 없는 파일 (`total`) |

---

## Outline

```
outline [file=<name>] [path=<path>] [format=tree|md|json] [total]
```

---

## File History

| 명령 | 설명 |
|------|------|
| `diff` | 버전 비교 (`file`, `path`, `from=<n>`, `to=<n>`, `filter=local|sync`) |
| `history` | 로컬 버전 목록 (`file`, `path`) |
| `history:list` | 히스토리 있는 파일 목록 |
| `history:read` | 특정 버전 읽기 (`version=<n>`) |
| `history:restore` | 버전 복원 (`version=<n>` required) |
| `history:open` | 파일 복구 열기 |

---

## Plugins

| 명령 | 설명 |
|------|------|
| `plugins` | 설치된 플러그인 목록 (`filter=core|community`, `versions`, `format`) |
| `plugins:enabled` | 활성 플러그인 목록 |
| `plugins:restrict [on|off]` | 제한 모드 토글 |
| `plugin id=<id>` | 플러그인 정보 |
| `plugin:enable id=<id>` | 활성화 |
| `plugin:disable id=<id>` | 비활성화 |
| `plugin:install id=<id>` | 설치 (`enable` 플래그) |
| `plugin:uninstall id=<id>` | 제거 |
| `plugin:reload id=<id>` | 리로드 (개발자용) |

---

## Themes & Snippets

| 명령 | 설명 |
|------|------|
| `themes` | 설치된 테마 목록 |
| `theme [name=<n>]` | 현재/특정 테마 정보 |
| `theme:set name=<n>` | 테마 적용 |
| `theme:install name=<n>` | 테마 설치 (`enable` 플래그) |
| `theme:uninstall name=<n>` | 테마 제거 |
| `snippets` | CSS 스니펫 목록 |
| `snippets:enabled` | 활성 스니펫 목록 |
| `snippet:enable name=<n>` | 스니펫 활성화 |
| `snippet:disable name=<n>` | 스니펫 비활성화 |

---

## Vault

| 명령 | 설명 |
|------|------|
| `vault [info=name|path|files|folders|size]` | vault 정보 |
| `vaults` | 알려진 vault 목록 (`total`, `verbose`) |
| `vault:open name=<n>` | 다른 vault로 전환 (TUI 전용) |

---

## Sync & Publish

### Sync
| 명령 | 설명 |
|------|------|
| `sync [on|off]` | Sync 일시중지/재개 |
| `sync:status` | 동기화 상태 |
| `sync:history` | 버전 히스토리 |
| `sync:read version=<n>` | 특정 버전 읽기 |
| `sync:restore version=<n>` | 버전 복원 |
| `sync:deleted` | 삭제된 파일 목록 |

### Publish
| 명령 | 설명 |
|------|------|
| `publish:site` | 사이트 정보 |
| `publish:list` | 발행된 파일 목록 |
| `publish:status` | 변경 사항 목록 (`new`, `changed`, `deleted`) |
| `publish:add` | 파일 발행 (`changed` 플래그로 전체 변경분) |
| `publish:remove` | 파일 발행 취소 |
| `publish:open` | 발행된 사이트에서 열기 |

---

## Workspace

| 명령 | 설명 |
|------|------|
| `workspace [ids]` | 현재 워크스페이스 트리 |
| `workspaces` | 저장된 워크스페이스 목록 |
| `workspace:save [name=<n>]` | 레이아웃 저장 |
| `workspace:load name=<n>` | 저장된 레이아웃 로드 |
| `workspace:delete name=<n>` | 삭제 |
| `tabs [ids]` | 열린 탭 목록 |
| `tab:open` | 새 탭 열기 (`group`, `file`, `view`) |
| `recents` | 최근 파일 목록 |

---

## Miscellaneous

| 명령 | 설명 |
|------|------|
| `random [folder=<path>] [newtab]` | 랜덤 노트 열기 |
| `random:read [folder=<path>]` | 랜덤 노트 읽기 |
| `unique [name] [content] [paneType] [open]` | Unique note 생성 |
| `wordcount [file] [path] [words|characters]` | 단어/문자 수 |
| `outline [file] [path] [format] [total]` | 헤딩 트리 |
| `web url=<url> [newtab]` | 웹 뷰어에서 URL 열기 |

---

## Bases

| 명령 | 설명 |
|------|------|
| `bases` | `.base` 파일 목록 |
| `base:views` | 현재 base의 뷰 목록 |
| `base:create` | base에 항목 생성 (`file`, `view`, `name`, `content`, `open`, `newtab`) |
| `base:query` | base 쿼리 (`file`, `view`, `format=json|csv|tsv|md|paths`) |

---

## Developer Commands

| 명령 | 설명 |
|------|------|
| `devtools` | Electron DevTools 토글 |
| `dev:debug [on|off]` | Chrome DevTools Protocol 디버거 연결/해제 |
| `dev:cdp method=<CDP.method> [params=<json>]` | CDP 명령 실행 |
| `dev:errors [clear]` | JS 오류 목록 |
| `dev:screenshot [path=<file>]` | 스크린샷 (base64 PNG) |
| `dev:console [limit=<n>] [level=...] [clear]` | 콘솔 메시지 |
| `dev:css selector=<css> [prop=<name>]` | CSS 소스 위치 조회 |
| `dev:dom selector=<css> [attr|css|total|text|inner|all]` | DOM 쿼리 |
| `dev:mobile [on|off]` | 모바일 에뮬레이션 |
| `eval code=<javascript>` | JS 실행 후 결과 반환 |
