---
name: md-obsidian-cli
description: >
  Obsidian CLI(`obsidian` 바이너리)를 AI CLI 에이전트에서 직접 실행하는 통합 워크플로우.
  노트 읽기·생성·편집·검색·태스크 관리·플러그인 제어·개발자 도구·그래프 계층 구조 설계까지
  Obsidian에서 할 수 있는 모든 것을 터미널 한 줄로 자동화한다.
  트리거: "Obsidian에서 노트 만들어줘", "일간 노트에 태스크 추가", "vault 검색해줘",
  "플러그인 다시 로드해줘", "obsidian cli 써줘", "그래프 계층 구조 설계",
  "허브 파일 구조", "L0/L1/L2 폴더 패턴", "Obsidian 폴더 가시성".
---

# md-obsidian-cli

Obsidian 1.12+에 내장된 `obsidian` CLI 바이너리를 통해 실행 중인 Obsidian 앱을
터미널에서 직접 제어한다.

## 전제 조건

- Obsidian 1.12+ 설치 → Settings → General → **Command line interface** 활성화 → Register
- Obsidian 앱이 실행 중이어야 함 (첫 명령 시 자동 시작 시도)
- PATH: macOS는 `~/.zprofile`에 자동 등록, Linux는 `/usr/local/bin/obsidian` 심링크

## 빠른 시작

```bash
obsidian daily:read
obsidian create name="Note" content="# Hello\n\n- " open
obsidian search query="tag:project" format=json
obsidian tasks todo
```

## 파일 타겟팅

```bash
file=<name>   # wikilink 방식 — 파일명만으로 매칭 (경로·확장자 불필요)
path=<path>   # vault root 기준 정확한 경로
vault=<name>  # 명령 앞에 위치 (obsidian vault=Notes daily)
```

## 모듈 & 참조

| 파일 | 내용 | 언제 읽을지 |
|------|------|-----------|
| `core.md` | 핵심 개념, 아키텍처, 파일 타겟팅·vault 지정·출력 형식 규칙 | 동작 원리 파악, 파라미터 헷갈릴 때 |
| `modules/module.commands.md` | 전체 명령 카테고리별 레퍼런스 (파라미터·플래그·예시) | 특정 명령 파라미터 확인 시 |
| `modules/module.shell-integration.md` | 자동화·파이프라인·Python 래퍼 패턴 | 배치 처리, 조건부 실행, GraphRAG 연동 시 |
| `references/cli-reference.md` | 전체 명령 빠른 참조표 | 명령명 목록 훑어볼 때 |
| `references/graph-hierarchy-patterns.md` | Obsidian 폴더 계층 구조 설계 패턴 | L0/L1/L2 허브 구조, 그래프 가시성 설계 시 |
