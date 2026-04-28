# module.shell-integration — 자동화 패턴

## 기본 호출 패턴

```bash
# 단일 명령
obsidian <command> [param=value] [flag]

# vault 지정
obsidian vault="My Vault" <command>

# 출력 클립보드 복사
obsidian read file=Note --copy

# TUI 진입 후 명령 (prefix 불필요)
obsidian
> daily:append content="- [ ] 오늘 할 일"
```

## 출력 파이프라인

```bash
# JSON 출력 → jq 처리
obsidian search query="tag:project" format=json | jq '.[].path'

# 태스크 목록 → 파일 저장
obsidian tasks todo format=json > tasks.json

# 검색 컨텍스트 → grep 추가 필터
obsidian search:context query="TODO" | grep "2026"

# 속성 YAML → 파싱
obsidian properties file=Note format=yaml
```

## 일간 노트 자동화

```bash
# 매일 아침 루틴
obsidian daily                                          # 열기
obsidian daily:append content="## 오늘의 목표\n\n- "    # 섹션 추가

# 태스크 수집 → 일간 노트에 추가
TASKS=$(obsidian search:context query="- [ ]" format=text)
obsidian daily:append content="## 미완료 태스크\n$TASKS"

# 일간 노트 내용 읽어서 분석
obsidian daily:read --copy
```

## 배치 노트 생성

```bash
# 루프로 여러 노트 생성
for name in "회의록-01" "회의록-02" "회의록-03"; do
  obsidian create name="$name" template=Meeting
done

# 폴더 내 파일 목록 처리
obsidian files folder=Projects format=json | jq -r '.[].name' | while read name; do
  obsidian property:set name=reviewed value=true file="$name"
done
```

## 조건부 실행

```bash
# 파일 존재 여부 확인 후 분기
if obsidian read file=Note 2>/dev/null; then
  obsidian append file=Note content="\n## 업데이트"
else
  obsidian create name=Note content="# 새 노트"
fi

# 태스크 수가 0이면 알림
COUNT=$(obsidian tasks daily total)
[ "$COUNT" -eq 0 ] && echo "오늘 일간 노트에 태스크가 없습니다"
```

## 플러그인 개발 자동화

```bash
# 파일 변경 감지 → 플러그인 자동 리로드
fswatch -o ~/vault/.obsidian/plugins/my-plugin/ | while read; do
  obsidian plugin:reload id=my-plugin
  echo "플러그인 리로드 완료"
done

# 스크린샷 → 비교 테스트
obsidian dev:screenshot path=before.png
# ... 변경 작업 ...
obsidian dev:screenshot path=after.png

# JS 표현식 실행
obsidian eval code="app.vault.getFiles().length"
obsidian eval code="app.workspace.activeLeaf?.getViewState()"
```

## GraphRAG 연동 (md-graph-multihop)

```bash
# 그래프 질의 결과 → Obsidian 노트로 저장
CONTENT=$(python3 ../md-graph-multihop/scripts/graph_rag.py \
  --query "X와 Y의 관계는?" --hops 2 --context-only)

obsidian create \
  name="Insights/$(date +%Y-%m-%d)-graphrag" \
  content="$CONTENT" \
  open
```

## Python 래퍼 (`scripts/obsidian_cli.py`)

복잡한 출력 파싱이나 멀티스텝 자동화가 필요할 때 사용한다.

```python
import subprocess, json

def obsidian(command: str, **kwargs) -> str:
    args = ["obsidian"] + command.split()
    for k, v in kwargs.items():
        if v is True:
            args.append(k)
        else:
            args.append(f"{k}={v}")
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout.strip()

# 사용 예
output = obsidian("tasks", daily=True, format="json", todo=True)
tasks = json.loads(output)
```

## 주의사항

- Obsidian 앱이 반드시 실행 중이어야 함 (첫 명령 시 자동 시작 시도)
- `file=<name>`: 중복 파일명이 있으면 어떤 파일이 선택될지 불확실 → 중요한 작업은 `path=` 사용
- `append`는 멱등성 없음 — 반복 실행 시 내용이 중복 추가됨
- `delete permanent`는 되돌릴 수 없음 — 기본 trash 사용 권장
- TUI의 `vault:open`은 TUI 전용 — 단일 명령 모드에서는 `vault=` 파라미터 사용
