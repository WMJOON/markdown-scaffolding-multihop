---
name: md-obsidian-cli
description: >
  Obsidian CLI(`obsidian` 바이너리)를 AI CLI 에이전트에서 직접 실행하는 통합 워크플로우.
  노트 읽기·생성·편집·검색·태스크 관리·플러그인 제어·개발자 도구까지
  Obsidian에서 할 수 있는 모든 것을 터미널 한 줄로 자동화한다.
  트리거 예시: "Obsidian에서 노트 만들어줘", "일간 노트에 태스크 추가",
  "vault 검색해줘", "플러그인 다시 로드해줘", "obsidian cli 써줘".
---

# md-obsidian-cli

Obsidian 1.12+에 내장된 `obsidian` CLI 바이너리를 통해 실행 중인 Obsidian 앱을
터미널에서 직접 제어한다.

## 전제 조건

- **Obsidian 1.12 installer** 이상 설치
- Settings → General → **Command line interface** 활성화 후 등록
- Obsidian 앱이 실행 중이어야 함 (첫 명령 실행 시 자동 시작)

### PATH 설정

```bash
# macOS (zsh - 기본, 자동 등록됨)
# ~/.zprofile에 자동 추가:
export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"

# macOS (bash)
echo 'export PATH="$PATH:/Applications/Obsidian.app/Contents/MacOS"' >> ~/.bash_profile

# Linux (symlink 자동 생성)
# /usr/local/bin/obsidian → Obsidian 바이너리
```

## 기본 사용법

```bash
# 단일 명령 실행
obsidian <command> [param=value] [flag]

# TUI (인터랙티브 터미널) 모드
obsidian

# vault 지정 (첫 번째 파라미터)
obsidian vault=<name> <command>

# 출력을 클립보드로 복사
obsidian <command> --copy
```

## 파라미터 & 플래그

```bash
# 파라미터: param=value (공백 포함 시 따옴표)
obsidian create name=Note content="Hello world"

# 플래그: 값 없이 이름만 (boolean true)
obsidian create name=Note open overwrite

# 줄바꿈: \n, 탭: \t
obsidian create name=Note content="# Title\n\nBody"
```

## 주요 워크플로우

### 노트 읽기 / 열기

```bash
# 활성 파일 읽기
obsidian read

# 파일명으로 열기 (wikilink 해석 방식)
obsidian open file=Recipe

# 경로로 열기 (vault root 기준 정확한 경로)
obsidian open path="Templates/Recipe.md"

# 새 탭에서 열기
obsidian open file=Recipe newtab
```

### 노트 생성 / 편집

```bash
# 기본 생성
obsidian create name=Note

# 내용 포함 생성
obsidian create name="Daily Review" content="## Today\n\n- "

# 템플릿으로 생성
obsidian create name="Trip to Paris" template=Travel

# 내용 추가 (append)
obsidian append file=Note content="\n- 새 항목"

# 내용 앞에 삽입 (prepend, frontmatter 다음)
obsidian prepend file=Note content="## 요약\n"
```

### 일간 노트

```bash
obsidian daily                                      # 오늘 일간 노트 열기
obsidian daily:read                                 # 내용 읽기
obsidian daily:append content="- [ ] Buy groceries" # 태스크 추가
obsidian daily:prepend content="## 오늘의 목표\n"   # 앞에 삽입
obsidian daily:path                                 # 경로 확인
```

### 검색

```bash
obsidian search query="meeting notes"               # 파일 목록 반환
obsidian search:context query="TODO"                # grep 스타일 컨텍스트
obsidian search query="tag:project" total           # 결과 수만 반환
obsidian search query="meeting" --copy              # 결과를 클립보드로
```

### 태스크 관리

```bash
obsidian tasks                                      # 전체 태스크 목록
obsidian tasks todo                                 # 미완료 태스크
obsidian tasks daily                                # 오늘 일간 노트 태스크
obsidian task file=Note line=8 toggle               # 태스크 토글
obsidian task file=Note line=8 done                 # 완료 처리
```

### 속성(Properties)

```bash
obsidian properties file=Note                       # 파일 속성 보기
obsidian property:set name=status value=active file=Note
obsidian property:read name=tags file=Note
obsidian property:remove name=draft file=Note
```

### 태그

```bash
obsidian tags                                       # 전체 태그 목록
obsidian tags counts sort=count                     # 사용 빈도 순
obsidian tag name=project verbose                   # 특정 태그 파일 목록
```

### 플러그인 관리 (개발자)

```bash
obsidian plugin:reload id=my-plugin                 # 플러그인 리로드
obsidian plugins:enabled                            # 활성 플러그인 목록
obsidian plugin:install id=dataview enable          # 설치 후 활성화
```

### 개발자 도구

```bash
obsidian eval code="app.vault.getFiles().length"    # JS 실행
obsidian dev:screenshot path=screenshot.png         # 스크린샷
obsidian dev:console                                # 콘솔 메시지 보기
obsidian dev:errors                                 # JS 오류 목록
obsidian devtools                                   # DevTools 토글
```

## Python 자동화 스크립트

복잡한 자동화가 필요할 때 `scripts/obsidian_cli.py`를 사용한다.

```bash
# 배치 노트 생성
python3 scripts/obsidian_cli.py batch-create \
  --vault "my vault" \
  --names "회의록-01" "회의록-02" "회의록-03" \
  --template Meeting

# 검색 결과 파싱
python3 scripts/obsidian_cli.py search-parse \
  --query "tag:project status:active" \
  --format json
```

## 주의사항

- `file=<name>`: wikilink 방식 — 파일명만으로 매칭 (확장자·경로 불필요)
- `path=<path>`: vault root 기준 정확한 경로 (`folder/note.md`)
- `vault=<name>`: 명령 앞에 위치해야 함 (`obsidian vault=Notes daily`)
- `--copy`: 모든 명령에 추가 가능, 출력을 클립보드로 복사
- TUI 모드에서는 `obsidian` prefix 없이 명령 입력 가능
