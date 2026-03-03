# CLI Quick Reference

출처: [Obsidian CLI 공식 문서](https://help.obsidian.md/cli)
버전: Obsidian 1.12+

## 설치 & 설정

```bash
# 설치: Obsidian 1.12+ → Settings → General → Command line interface → Enable → Register

# macOS PATH (자동 등록, ~/.zprofile)
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"

# macOS 수동 (bash)
echo 'export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"' >> ~/.bash_profile

# Fish
fish_add_path /Applications/Obsidian.app/Contents/MacOS

# Linux: /usr/local/bin/obsidian 심링크 자동 생성
```

## 문법

```
obsidian [vault=<name>] <command> [param=value ...] [flag ...]

파라미터: param=value  (공백 포함 시 "따옴표")
플래그:   flag 이름만 (boolean true)
줄바꿈:  \n  탭: \t
--copy:   모든 명령에 추가 → 클립보드로 출력
```

## 전체 명령 빠른 참조

### General
| 명령 | 설명 |
|------|------|
| `help [cmd]` | 도움말 |
| `version` | 버전 |
| `reload` | 앱 리로드 |
| `restart` | 앱 재시작 |

### Files & Folders
| 명령 | 주요 파라미터 | 플래그 |
|------|-------------|--------|
| `file` | `file` `path` | |
| `files` | `folder` `ext` | `total` |
| `folder` | `path`(required) `info=files\|folders\|size` | |
| `folders` | `folder` | `total` |
| `open` | `file` `path` | `newtab` |
| `create` | `name` `path` `content` `template` | `overwrite` `open` `newtab` |
| `read` | `file` `path` | `--copy` |
| `append` | `file` `path` `content`(req) | `inline` |
| `prepend` | `file` `path` `content`(req) | `inline` |
| `move` | `file` `path` `to`(req) | |
| `rename` | `file` `path` `name`(req) | |
| `delete` | `file` `path` | `permanent` |

### Daily Notes
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `daily` | `paneType=tab\|split\|window` | |
| `daily:path` | | |
| `daily:read` | | `--copy` |
| `daily:append` | `content`(req) `paneType` | `inline` `open` |
| `daily:prepend` | `content`(req) `paneType` | `inline` `open` |

### Search
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `search` | `query`(req) `path` `limit` `format=text\|json` | `total` `case` |
| `search:context` | `query`(req) `path` `limit` `format=text\|json` | `case` |
| `search:open` | `query` | |

### Tasks
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `tasks` | `file` `path` `status="<char>"` `format=json\|tsv\|csv` | `total` `done` `todo` `verbose` `active` `daily` |
| `task` | `ref=<path:line>` `file` `path` `line` `status="<char>"` | `toggle` `done` `todo` `daily` |

### Properties
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `aliases` | `file` `path` | `total` `verbose` `active` |
| `properties` | `file` `path` `name` `sort=count` `format=yaml\|json\|tsv` | `total` `counts` `active` |
| `property:set` | `name`(req) `value`(req) `type=text\|list\|number\|checkbox\|date\|datetime` `file` `path` | |
| `property:remove` | `name`(req) `file` `path` | |
| `property:read` | `name`(req) `file` `path` | |

### Tags
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `tags` | `file` `path` `sort=count` `format=json\|tsv\|csv` | `total` `counts` `active` |
| `tag` | `name`(req) | `total` `verbose` |

### Links
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `backlinks` | `file` `path` `format=json\|tsv\|csv` | `counts` `total` |
| `links` | `file` `path` | `total` |
| `unresolved` | `format=json\|tsv\|csv` | `total` `counts` `verbose` |
| `orphans` | | `total` |
| `deadends` | | `total` |

### Outline
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `outline` | `file` `path` `format=tree\|md\|json` | `total` |

### Plugins
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `plugins` | `filter=core\|community` `format=json\|tsv\|csv` | `versions` |
| `plugins:enabled` | `filter=core\|community` `format` | `versions` |
| `plugins:restrict` | `on\|off` | |
| `plugin` | `id`(req) | |
| `plugin:enable` | `id`(req) `filter` | |
| `plugin:disable` | `id`(req) `filter` | |
| `plugin:install` | `id`(req) | `enable` |
| `plugin:uninstall` | `id`(req) | |
| `plugin:reload` | `id`(req) | |

### Templates
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `templates` | | `total` |
| `template:read` | `name`(req) `title` | `resolve` |
| `template:insert` | `name`(req) | |

### Themes & Snippets
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `themes` | | `versions` |
| `theme` | `name` | |
| `theme:set` | `name`(req) | |
| `theme:install` | `name`(req) | `enable` |
| `theme:uninstall` | `name`(req) | |
| `snippets` / `snippets:enabled` | | |
| `snippet:enable` / `snippet:disable` | `name`(req) | |

### Bookmarks
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `bookmarks` | `format=json\|tsv\|csv` | `total` `verbose` |
| `bookmark` | `file` `folder` `search` `url` `subpath` `title` | |

### Command Palette
| 명령 | 파라미터 |
|------|---------|
| `commands` | `filter=<prefix>` |
| `command` | `id`(req) |
| `hotkeys` | `format=json\|tsv\|csv` / `total` `verbose` |
| `hotkey` | `id`(req) / `verbose` |

### File History
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `diff` | `file` `path` `from=<n>` `to=<n>` `filter=local\|sync` | |
| `history` | `file` `path` | |
| `history:list` | | |
| `history:read` | `file` `path` `version=<n>` | |
| `history:restore` | `file` `path` `version`(req) | |
| `history:open` | `file` `path` | |

### Sync
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `sync` | `on\|off` | |
| `sync:status` | | |
| `sync:history` | `file` `path` | `total` |
| `sync:read` | `file` `path` `version`(req) | |
| `sync:restore` | `file` `path` `version`(req) | |
| `sync:open` | `file` `path` | |
| `sync:deleted` | | `total` |

### Publish
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `publish:site` | | |
| `publish:list` | | `total` |
| `publish:status` | | `total` `new` `changed` `deleted` |
| `publish:add` | `file` `path` | `changed` |
| `publish:remove` | `file` `path` | |
| `publish:open` | `file` `path` | |

### Vault
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `vault` | `info=name\|path\|files\|folders\|size` | |
| `vaults` | | `total` `verbose` |
| `vault:open` | `name`(req) | (TUI 전용) |

### Workspace
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `workspace` | | `ids` |
| `workspaces` | | `total` |
| `workspace:save` | `name` | |
| `workspace:load` | `name`(req) | |
| `workspace:delete` | `name`(req) | |
| `tabs` | | `ids` |
| `tab:open` | `group` `file` `view` | |
| `recents` | | `total` |

### Miscellaneous
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `random` | `folder` | `newtab` |
| `random:read` | `folder` | |
| `unique` | `name` `content` `paneType` | `open` |
| `wordcount` | `file` `path` | `words` `characters` |
| `web` | `url`(req) | `newtab` |

### Bases
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `bases` | | |
| `base:views` | | |
| `base:create` | `file` `path` `view` `name` `content` | `open` `newtab` |
| `base:query` | `file` `path` `view` `format=json\|csv\|tsv\|md\|paths` | |

### Developer
| 명령 | 파라미터 | 플래그 |
|------|---------|--------|
| `devtools` | | |
| `dev:debug` | `on\|off` | |
| `dev:cdp` | `method`(req) `params=<json>` | |
| `dev:errors` | | `clear` |
| `dev:screenshot` | `path=<file>` | |
| `dev:console` | `limit=<n>` `level=log\|warn\|error\|info\|debug` | `clear` |
| `dev:css` | `selector`(req) `prop` | |
| `dev:dom` | `selector`(req) `attr` `css` | `total` `text` `inner` `all` |
| `dev:mobile` | `on\|off` | |
| `eval` | `code`(req) | |

## TUI 키보드 단축키

| 동작 | 단축키 |
|------|--------|
| 커서 이동 | ← → / Ctrl+B Ctrl+F |
| 단어 이동 | Alt+B / Alt+F |
| 줄 처음/끝 | Ctrl+A / Ctrl+E |
| 줄 삭제 | Ctrl+U (앞) / Ctrl+K (뒤) |
| 이전 명령 | ↑ / Ctrl+P |
| 다음 명령 | ↓ / Ctrl+N |
| 히스토리 검색 | Ctrl+R |
| 자동완성 | Tab |
| 실행 | Enter |
| 화면 지우기 | Ctrl+L |
| 종료 | Ctrl+C / Ctrl+D |
