# URI 파라미터 완전 레퍼런스

출처: https://help.obsidian.md/cli (Obsidian 공식 문서)

---

## URI 기본 형식

```
obsidian://action?param1=value1&param2=value2
```

모든 값은 퍼센트 인코딩 필수.

---

## 인코딩 빠른 참조

| 문자 | 인코딩 | 용도 |
|------|--------|------|
| 공백 | `%20` | 볼트명, 파일명 |
| `/` | `%2F` | 경로 구분자 (file 파라미터 내) |
| `#` | `%23` | 헤딩 앵커 |
| `^` | `%5E` | 블록 참조 |
| `'` | `%27` | 아포스트로피 |
| `&` | `%26` | 콘텐츠 내 앰퍼샌드 |

---

## 액션별 파라미터 전체 목록

### `open`

| 파라미터 | 타입 | 설명 | 예시 |
|----------|------|------|------|
| `vault` | string | 볼트 이름 또는 ID | `my%20vault` |
| `file` | string | 볼트 내 상대 경로 | `Projects%2FNote` |
| `path` | string | 절대 파일 경로 | `%2FUsers%2Fuser%2Fnote.md` |
| `paneType` | enum | 열기 위치 | `tab` / `split` / `window` |

헤딩 이동: `file=Note%23Heading`
블록 이동: `file=Note%23%5EBlockID`

### `new`

| 파라미터 | 타입 | 설명 | 예시 |
|----------|------|------|------|
| `vault` | string | 볼트 이름 또는 ID | `my%20vault` |
| `name` | string | 노트 이름 (경로 없음) | `Quick%20Note` |
| `file` | string | 볼트 내 상대 경로 | `Daily%2F2026-03-02` |
| `path` | string | 절대 파일 경로 | `%2FUsers%2Fuser%2Fnote.md` |
| `content` | string | 초기 노트 내용 | `Hello%20World` |
| `clipboard` | bool | 클립보드 내용을 content로 | `true` |
| `silent` | bool | 에디터에서 열지 않음 | `true` |
| `append` | bool | 기존 파일 끝에 추가 | `true` |
| `overwrite` | bool | 기존 파일 내용 교체 | `true` |

### `search`

| 파라미터 | 타입 | 설명 | 예시 |
|----------|------|------|------|
| `vault` | string | 볼트 이름 또는 ID | `my%20vault` |
| `query` | string | 검색 쿼리 | `tag%3Aproject` |

### `daily`

| 파라미터 | 타입 | 설명 | 예시 |
|----------|------|------|------|
| `vault` | string | 볼트 이름 또는 ID | `my%20vault` |

**필수**: Core Plugins → Daily notes 활성화

### `choose-vault`

파라미터 없음. 볼트 관리자 다이얼로그 열기.

### `hook-get-address`

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `x-success` | URL | 성공 시 콜백 URL (`name`, `url`, `file` 전달) |
| `x-error` | URL | 실패 시 콜백 URL |

---

## 단축 URI 형식

```
obsidian://vault/<볼트명>/<파일명>
obsidian:///<절대경로>
```

---

## 볼트 ID vs 볼트 이름

- **이름**: 볼트 폴더명 (공백 인코딩 필요)
- **ID**: Obsidian 내부 UUID (이름 변경에도 불변)
  - 위치 (macOS): `~/Library/Application Support/obsidian/obsidian.json`

---

## obsidian_cli.py 지원 액션 대응

| CLI 서브커맨드 | URI 액션 | 비고 |
|---------------|---------|------|
| `open` | `open` | 전체 파라미터 지원 |
| `new` | `new` | 전체 파라미터 지원 |
| `search` | `search` | 전체 파라미터 지원 |
| `daily` | `daily` | vault 파라미터 지원 |
| `exec` | 직접 URI | URI 문자열 그대로 실행 |
