---
name: md-obsidian-cli
description: >
  obsidian:// URI 스킴으로 AI CLI 에이전트(antigravity · codex · claude-code 등)에서
  Obsidian vault를 직접 조작하는 CLI 통합 워크플로우.
  노트 열기·생성·검색·일간 노트·볼트 전환을 쉘 한 줄 또는 Python 스크립트로 실행.
  외부 API 없이 macOS open 명령만으로 동작하며, 스크립트로 배치 자동화도 지원한다.
  트리거 예시: "Obsidian에서 노트 열어줘", "vault에 새 노트 만들어줘",
  "Obsidian에서 검색해줘", "obsidian URI 생성해줘", "일간 노트 열어줘".
---

# md-obsidian-cli

`obsidian://` URI 스킴을 통해 실행 중인 Obsidian 앱을 AI CLI 에이전트에서 직접 조작한다.
antigravity · codex · claude-code 등 어느 환경에서도 동일하게 동작한다.

## 전제 조건

- Obsidian 앱 설치 및 실행 중
- macOS: `open` 명령 사용 (기본 내장)
- Linux: `xdg-open` 명령 사용
- Windows: `start` 명령 사용

의존 패키지 없음 — Python 표준 라이브러리만 사용.

## 스크립트

```
scripts/
└── obsidian_cli.py   # URI 빌더 + 플랫폼별 실행기
```

## 워크플로우

### 노트 열기

```bash
# 볼트만 열기
python3 scripts/obsidian_cli.py open --vault "my vault"

# 특정 노트 열기
python3 scripts/obsidian_cli.py open --vault "my vault" --file "Projects/2026-Q1"

# 새 탭에서 열기
python3 scripts/obsidian_cli.py open --vault "my vault" --file "note" --pane tab

# URI만 출력 (실행 안 함)
python3 scripts/obsidian_cli.py --dry-run open --vault "my vault" --file "note"
```

### 새 노트 생성

```bash
# 기본 생성 (에디터에서 바로 열림)
python3 scripts/obsidian_cli.py new --vault "my vault" --name "새 노트"

# 내용 포함 생성
python3 scripts/obsidian_cli.py new \
  --vault "my vault" \
  --file "Daily/2026-03-02" \
  --content "오늘의 할 일:\n- [ ] 항목1"

# 백그라운드 생성 (UI 없이)
python3 scripts/obsidian_cli.py new --vault "my vault" --name "auto-note" --silent

# 기존 파일에 내용 추가
python3 scripts/obsidian_cli.py new --vault "my vault" --name "log" --content "새 항목" --append
```

### 검색

```bash
# 검색 패널 열기
python3 scripts/obsidian_cli.py search --vault "my vault"

# 쿼리 포함 검색
python3 scripts/obsidian_cli.py search --vault "my vault" --query "GraphRAG"
```

### 일간 노트

```bash
# 오늘 일간 노트 열기 (Daily notes 플러그인 필요)
python3 scripts/obsidian_cli.py daily --vault "my vault"
```

### URI 직접 실행

```bash
# obsidian:// URI를 직접 실행
python3 scripts/obsidian_cli.py exec "obsidian://open?vault=my%20vault&file=note"
```

## 주요 CLI 옵션

| 옵션 | 설명 |
|------|------|
| `--dry-run` | URI만 출력, Obsidian 실행 안 함 |
| `--vault NAME` | 볼트 이름 또는 ID |
| `--file PATH` | 파일 상대 경로 (확장자 생략 가능) |
| `--path ABSPATH` | 절대 파일 경로 |
| `--pane tab\|split\|window` | 열기 위치 |
| `--content TEXT` | 노트 내용 (new 액션) |
| `--silent` | UI 열지 않고 생성만 (new 액션) |
| `--append` | 기존 파일에 내용 추가 (new 액션) |
| `--overwrite` | 기존 파일 덮어쓰기 (new 액션) |
| `--query TEXT` | 검색 쿼리 (search 액션) |

## 주의사항

- Obsidian 앱이 실행 중이어야 URI가 처리된다
- `--file`에 한글 경로 사용 시 자동으로 URI 인코딩됨
- `--content`에 줄바꿈은 `\n`으로 전달 (셸 따옴표 주의)
- `--append` / `--overwrite` 동시 사용 불가
- Daily notes 플러그인 미설치 시 `daily` 액션은 동작 안 함
