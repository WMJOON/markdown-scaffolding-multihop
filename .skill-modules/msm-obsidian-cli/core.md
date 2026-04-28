# core — md-obsidian-cli

## 개요

Obsidian 1.12+부터 내장된 `obsidian` CLI 바이너리를 통해
실행 중인 Obsidian 앱에 명령을 전달한다.
외부 API·플러그인 없이 Settings에서 활성화만 하면 즉시 사용 가능하다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **CLI 바이너리** | `obsidian` 실행 파일 (Obsidian 앱 내부에 포함) |
| **단일 명령 모드** | `obsidian <command> [params]` — 스크립트/자동화에 적합 |
| **TUI 모드** | `obsidian` 단독 실행 — 인터랙티브, 자동완성·히스토리 지원 |
| **파라미터** | `param=value` 형식, 공백 포함 시 따옴표 필요 |
| **플래그** | 값 없이 이름만 — boolean true (`open`, `overwrite`, `total` 등) |
| **`--copy`** | 모든 명령에 추가 가능 — 출력을 클립보드로 복사 |
| **vault 지정** | `vault=<name>` 또는 `vault=<id>` — 명령 앞에 위치 |
| **파일 지정** | `file=<name>` (wikilink 방식) 또는 `path=<exact-path>` |

## 아키텍처

```
터미널/스크립트
    │
    ▼
obsidian <command>     ← PATH에 등록된 CLI 바이너리
    │
    ▼
실행 중인 Obsidian 앱  ← IPC (로컬 소켓)
    │
    ▼
vault 파일 시스템 / 플러그인 API / 개발자 도구
```

## 설치 흐름

```
Obsidian 1.12 installer 설치
    → Settings → General → Command line interface 활성화
    → "Register" 클릭
    → PATH 자동 등록 (macOS: ~/.zprofile, Linux: /usr/local/bin/obsidian 심링크)
    → 터미널 재시작
    → obsidian help 로 확인
```

## 파일 타겟팅 규칙

```bash
# file=<name>: wikilink 해석 — 파일명만으로 매칭 (경로·확장자 불필요)
obsidian read file=Recipe          # "Recipe.md" 어느 폴더에 있어도 찾음

# path=<path>: vault root 기준 정확한 경로
obsidian read path="Templates/Recipe.md"

# 기본값: 현재 활성 파일
obsidian read
```

## vault 지정 규칙

```bash
# CWD가 vault 폴더면 자동 감지
cd ~/vault && obsidian daily

# 명시적 지정 (명령 앞에 위치)
obsidian vault=Notes daily
obsidian vault="My Vault" search query="test"
```

## 출력 형식

대부분의 list 명령은 `format=` 파라미터를 지원한다:

| 형식 | 설명 |
|------|------|
| `text` / `tsv` | 기본값 (명령별로 다름) |
| `json` | 구조화 출력, 파이프 처리에 적합 |
| `csv` | 스프레드시트 연동 |
| `md` | Markdown 테이블 |
| `yaml` | properties 명령 기본값 |

## 모듈 구성

- `module.commands.md` — 전체 명령 카테고리별 레퍼런스
- `module.shell-integration.md` — 자동화·파이프라인 패턴

## Python 스크립트

`scripts/obsidian_cli.py` — 복잡한 배치 자동화·출력 파싱을 위한 Python 래퍼.
기본 CLI 호출이 가능하면 직접 `obsidian` 명령을 사용하는 것이 더 간결하다.
