# module.aggregation

## 집계 함수 정의

### sum
```
result = Σ values (None 제외)
```

### avg
```
result = Σ values / count (None 제외)
```

### weighted_avg
```
result = Σ (value × weight) / Σ weight
- weight가 None 또는 0인 노드는 제외
- 유효 노드가 0개면 None 반환
```

### max / min
```
result = max/min(values) (None 제외)
- 유효 값이 없으면 None
```

### count
```
result = 인접 노드 수 (value 유무 무관)
```

## 엣지 케이스 처리

| 상황 | 처리 |
|------|------|
| 인접 노드 없음 | None 반환, 기존 필드 유지 |
| 모든 값이 None | None 반환, 기존 필드 유지 |
| 문자열/리스트 필드 | 집계 불가, 경고 출력 후 스킵 |
| weighted_avg에서 weight 합계 = 0 | None 반환 |

## frontmatter 업데이트 정책

1. 원본 md 파일을 읽어 `---...---` 블록 교체
2. 기존 frontmatter의 다른 필드는 보존
3. `write_to` 필드만 업데이트 (없으면 추가)
4. `updated_at_field` 지정 시 ISO 날짜 기록
5. 파일 인코딩: UTF-8 유지
