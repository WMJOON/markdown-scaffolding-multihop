# module.insight-save

## 목적

Claude 멀티홉 추론 결과를 wikilink로 연결된 md 노드로 저장한다.
저장된 노드는 다음 `graph_builder.py` 실행 시 그래프에 자동 포함된다.

## 저장 정책

### 파일명
`{날짜}_{슬러그}.md` (예: `2026-02-28_경쟁사분석.md`)

### Frontmatter 필드

KB 구조 원칙(SPEC v0.1.1)의 instance frontmatter 스키마를 따른다.

```yaml
type: insight                      # concept 폴더명 (ontology/insight/ 에 저장 시)
status: draft                      # draft | experimental | validated | deprecated
date:                              # 저장 날짜
tags:                              # 사용자 지정 태그
generated: "Claude multihop"
sources:                           # 근거가 있는 경우 evidence 경로 참조
  - evidence/[topic]/sources/[file].md
relations:                         # 연결 노드
  - type: related-to
    target: "[[ontology/[concept]/[node]]]"
domain:                            # 도메인 레이블 (인덱싱용)
```

### 본문
- 추론 결과 텍스트
- 하단에 `## Related` 섹션 + wikilink 자동 추가

## 출력 디렉토리 결정 우선순위

1. `--output` 명시적 경로
2. `--config graph-config.yaml`의 `insight_dir` 필드
3. `./insights/` (기본값)
