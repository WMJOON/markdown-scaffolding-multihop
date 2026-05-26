# msm-obsidian-projection Core

## Protocol

| Phase | 도구 | 입력 | 출력 | 검증 |
|-------|------|------|------|------|
| **DESIGN** | — | `--domain` 지정 | 템플릿 경로 | dry-run: "생성될 파일" 목록 |
| **EXECUTE** | DuckDB + Jinja2 | parquet snapshot | MD + JSON | generated marker 부착 |
| **EVALUATE** | artifact marker | obsidian-projection/ | 파일 존재 + marker | HITL: marker 없으면 덮어쓰기 거부 |

## 흐름

```
1. DuckDB로 instance/snapshots/*.parquet 읽기
2. 각 row를 Jinja2 템플릿으로 렌더링
3. obsidian-projection/{domain}/{id}.md 파일 생성
4. frontmatter에 <!-- msm:generated --> marker 포함
5. Obsidian Bases 호환 JSON도 함께 생성
```

## 산출 위치

```
<target>/obsidian-projection/{domain}/
  ├── {entity_id}.md          (generated artifact)
  ├── {entity_id}.base.json   (Obsidian Bases manifest)
  └── ...
```

## HITL 정책

1. **marker 필수**: 모든 생성 파일에 `<!-- msm:generated -->` 주석 필수
2. **덮어쓰기 차단**: marker 없는 기존 파일은 HITL (사용자 확인 필수)
3. **dry-run 우선**: `--apply` 없으면 생성될 파일 목록만 출력

## Obsidian Bases JSON

```json
{
  "version": "1.0.0",
  "name": "{domain}",
  "entries": [
    {
      "id": "{entity_id}",
      "title": "{entity_name}",
      "path": "obsidian-projection/{domain}/{entity_id}.md",
      "tags": ["{tag1}", "{tag2}"]
    }
  ]
}
```

## CLI 예시

```bash
# dry-run: 생성될 파일 목록 확인
scripts/msm-obsidian-projection run --target repo/ --domain concept

# 실제 생성
scripts/msm-obsidian-projection run --target repo/ --domain concept --apply

# 생성된 파일 목록
scripts/msm-obsidian-projection list --target repo/
```

## 제약

- 모든 파일은 자동 생성이므로 직접 편집하지 않음
- marker 제거하면 HITL에 걸림
- dry-run 상태에서는 파일을 생성하지 않음
