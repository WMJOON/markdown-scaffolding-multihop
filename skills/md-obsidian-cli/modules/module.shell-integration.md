# module.shell-integration — 쉘 통합 패턴

Claude Code 세션에서 `obsidian_cli.py`를 활용하는 실전 패턴을 정의한다.

---

## 기본 호출 패턴

```bash
# 스크립트 직접 실행
python3 scripts/obsidian_cli.py <action> [options]

# 볼트 환경변수 설정으로 반복 생략
export OBSIDIAN_VAULT="my vault"
python3 scripts/obsidian_cli.py open --file "note"
```

---

## dry-run으로 URI 확인 후 실행

```bash
# URI 미리 확인
python3 scripts/obsidian_cli.py --dry-run new \
  --vault "my vault" \
  --file "Projects/2026-Q1-Review" \
  --content "## Q1 Review\n\n- 항목1"

# 결과 확인 후 실제 실행
python3 scripts/obsidian_cli.py new \
  --vault "my vault" \
  --file "Projects/2026-Q1-Review" \
  --content "## Q1 Review\n\n- 항목1"
```

---

## 배치 노트 생성

```bash
# 여러 노트를 순차 생성
for note in "회의록-01" "회의록-02" "회의록-03"; do
  python3 scripts/obsidian_cli.py new \
    --vault "my vault" \
    --file "Meetings/$note" \
    --silent
  sleep 0.5   # Obsidian 처리 대기
done
```

---

## Python 스크립트에서 직접 임포트

```python
from obsidian_cli import build_uri, run_uri

# URI 빌드만
uri = build_uri("open", vault="my vault", file="Projects/Note")
print(uri)  # obsidian://open?vault=my%20vault&file=Projects%2FNote

# 빌드 + 실행
run_uri("new", vault="my vault", name="auto-note", content="내용", silent=True)
```

---

## md-graph-multihop 결과를 Obsidian에 저장

```bash
# 1. 그래프 추론 결과 추출
python3 scripts/graph_rag.py \
  --query "GraphRAG 핵심 인사이트" \
  --hops 2 \
  --context-only > /tmp/insight.txt

# 2. Claude가 추론한 결과를 Obsidian 노트로 저장
CONTENT=$(cat /tmp/insight.txt)
python3 scripts/obsidian_cli.py new \
  --vault "my vault" \
  --file "Insights/2026-03-02-graphrag" \
  --content "$CONTENT"
```

---

## 검색 결과 기반 노트 열기

```bash
# 검색 후 특정 노트 열기 (수동 선택)
python3 scripts/obsidian_cli.py search \
  --vault "my vault" \
  --query "tag:project status:active"

# 알려진 노트 직접 열기
python3 scripts/obsidian_cli.py open \
  --vault "my vault" \
  --file "Projects/Active/주요-프로젝트"
```

---

## 조건부 실행 (노트 존재 여부 확인)

```bash
VAULT_PATH="/Users/user/Documents/my vault"
NOTE="Projects/New-Note"

if [ -f "$VAULT_PATH/$NOTE.md" ]; then
  # 기존 파일에 추가
  python3 scripts/obsidian_cli.py new \
    --vault "my vault" \
    --file "$NOTE" \
    --content "\n## 추가 섹션\n내용" \
    --append
else
  # 새 파일 생성
  python3 scripts/obsidian_cli.py new \
    --vault "my vault" \
    --file "$NOTE" \
    --content "## 새 노트\n내용"
fi
```

---

## URI 직접 실행

```bash
# 미리 알고 있는 URI를 직접 실행
python3 scripts/obsidian_cli.py exec \
  "obsidian://open?vault=my%20vault&file=Dashboard"

# macOS에서 직접 실행 (스크립트 없이)
open "obsidian://open?vault=my%20vault&file=Dashboard"

# Linux
xdg-open "obsidian://open?vault=my%20vault&file=Dashboard"
```

---

## 주의사항

| 상황 | 해결책 |
|------|--------|
| 한글 볼트/파일명 | 스크립트가 자동 NFC → URI 인코딩 처리 |
| 경로에 공백 포함 | `--vault "my vault"` 처럼 따옴표로 감쌈 |
| Obsidian 미실행 | URI 호출 전 앱을 먼저 실행해야 함 |
| `daily` 액션 오류 | Obsidian Core Plugins → Daily notes 활성화 |
| `--append` 무한 추가 | 멱등성 없음 — 스크립트 재실행 시 중복 추가됨 |
