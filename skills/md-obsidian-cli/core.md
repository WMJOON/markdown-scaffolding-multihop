# md-obsidian-cli — Core

## 역할

`obsidian://` URI 스킴을 빌드하고 플랫폼 기본 명령(`open` / `xdg-open` / `start`)으로
실행 중인 Obsidian 앱에 전달한다.
외부 플러그인·API 없이 동작하며, AI CLI 에이전트(antigravity · codex · claude-code 등) 어디서든 Obsidian vault를 직접 제어할 수 있다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **URI 스킴** | `obsidian://action?param=value` 형태. Obsidian이 등록한 커스텀 URL 핸들러 |
| **액션** | `open` · `new` · `search` · `daily` · `choose-vault` · `hook-get-address` |
| **볼트 식별** | `vault` 파라미터 = 볼트 이름 or ID. 생략 시 마지막 열린 볼트 |
| **파일 경로** | `file` (볼트 내 상대경로) 또는 `path` (절대경로) |
| **URI 인코딩** | 모든 값은 퍼센트 인코딩 필수. 슬래시→`%2F`, 공백→`%20` |

## 모듈 구성

- `module.uri-actions.md` — 각 URI 액션의 파라미터·동작·예시 정의
- `module.shell-integration.md` — 쉘·Python에서 URI 호출 패턴 (배치, 파이프, 조건부)

## 스크립트 의존성

```
obsidian_cli.py   → Python 표준 라이브러리만 (urllib.parse, subprocess, argparse)
```

## 플랫폼별 실행 명령

| 플랫폼 | 명령 |
|--------|------|
| macOS  | `open "obsidian://..."` |
| Linux  | `xdg-open "obsidian://..."` |
| Windows | `start "" "obsidian://..."` |

`obsidian_cli.py`가 플랫폼을 자동 감지해 적절한 명령을 선택한다.

## 설계 원칙

- **단방향 IPC**: URI를 전송할 뿐, 응답값을 받지 않는다 (x-callback-url 제외)
- **인코딩 위임**: 모든 인코딩은 스크립트가 처리 — 호출자는 원문 문자열만 전달
- **dry-run 우선**: `--dry-run`으로 URI를 먼저 확인한 후 실행
