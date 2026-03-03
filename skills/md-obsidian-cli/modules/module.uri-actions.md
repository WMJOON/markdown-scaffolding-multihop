# module.uri-actions — URI 액션 레퍼런스

Obsidian이 지원하는 모든 `obsidian://` URI 액션의 파라미터·동작·예시를 정의한다.

---

## 공통 규칙

- 모든 파라미터 값은 **URI 퍼센트 인코딩** 필수
- 공백 → `%20`, 슬래시 → `%2F`, `#` → `%23`, `^` → `%5E`
- `vault` 생략 시 마지막으로 열린 볼트가 대상
- `file` 경로에서 `.md` 확장자는 생략 가능

---

## `open` — 노트/볼트 열기

**용도**: 볼트를 열거나 특정 노트로 이동

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `vault` | 권장 | 볼트 이름 또는 ID |
| `file` | 선택 | 볼트 내 상대 경로 (확장자 생략 가능) |
| `path` | 선택 | 절대 파일 경로 (`file` 대신 사용) |
| `paneType` | 선택 | `tab` / `split` / `window` |

**헤딩/블록으로 이동:**
- 헤딩: `file=Note%23Heading` (`#` → `%23`)
- 블록: `file=Note%23%5EBlockID` (`^` → `%5E`)

**예시:**
```
obsidian://open?vault=my%20vault
obsidian://open?vault=my%20vault&file=Projects%2F2026-Q1
obsidian://open?vault=my%20vault&file=Note%23Section
obsidian://open?path=%2FUsers%2Fuser%2Fvault%2Fnote.md
obsidian://open?vault=my%20vault&file=note&paneType=tab
```

---

## `new` — 새 노트 생성

**용도**: 노트를 생성하고 선택적으로 내용을 채움

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `vault` | 권장 | 볼트 이름 또는 ID |
| `name` | 선택 | 노트 이름 (경로 없이 이름만) |
| `file` | 선택 | 볼트 내 상대 경로 (폴더 포함) |
| `path` | 선택 | 절대 파일 경로 |
| `content` | 선택 | 노트 초기 내용 |
| `clipboard` | 선택 | `true` 시 클립보드 내용을 content로 사용 |
| `silent` | 선택 | `true` 시 에디터에서 열지 않음 |
| `append` | 선택 | `true` 시 기존 파일 끝에 content 추가 |
| `overwrite` | 선택 | `true` 시 기존 파일 내용 교체 |

**제약:**
- `append`와 `overwrite` 동시 사용 불가
- `content`와 `clipboard` 동시 사용 불가

**예시:**
```
obsidian://new?vault=my%20vault&name=Quick%20Note
obsidian://new?vault=my%20vault&file=Daily%2F2026-03-02&content=Today%27s%20notes
obsidian://new?vault=my%20vault&name=log&content=new%20entry&append=true
obsidian://new?vault=my%20vault&name=auto&content=text&silent=true
obsidian://new?vault=my%20vault&name=draft&clipboard=true
```

---

## `search` — 검색 열기

**용도**: Obsidian 내 검색 패널을 열고 선택적으로 쿼리를 실행

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `vault` | 권장 | 볼트 이름 또는 ID |
| `query` | 선택 | 검색 쿼리 문자열 |

**예시:**
```
obsidian://search?vault=my%20vault
obsidian://search?vault=my%20vault&query=GraphRAG
obsidian://search?vault=my%20vault&query=tag%3Aprojects%20status%3Aactive
```

---

## `daily` — 일간 노트 생성/열기

**용도**: 오늘 날짜의 Daily Note를 열거나 생성
**필수 조건**: Core Plugins → Daily notes 활성화

| 파라미터 | 필수 | 설명 |
|----------|------|------|
| `vault` | 권장 | 볼트 이름 또는 ID |

**예시:**
```
obsidian://daily?vault=my%20vault
```

---

## `choose-vault` — 볼트 관리자 열기

**용도**: 볼트 전환/추가 다이얼로그 열기

```
obsidian://choose-vault
```

---

## `hook-get-address` — Hook 통합

**용도**: Hook 앱과의 통합. 현재 열린 노트의 Hook 주소를 반환

x-callback-url 파라미터를 지원:
- `x-success`: 성공 시 호출할 URL (`name`, `url`, `file` 값이 전달됨)
- `x-error`: 실패 시 호출할 URL

```
obsidian://hook-get-address
```

---

## 단축 URI 형식

Obsidian은 다음 단축 형식도 지원한다:

```
# 볼트/파일 단축
obsidian://vault/my vault/my note

# 절대 경로 단축
obsidian:///absolute/path/to/my note
```
