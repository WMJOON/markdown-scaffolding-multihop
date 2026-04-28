# module.descriptive-stats

## 목적

수치형·범주형 데이터의 기본 분포와 특성을 요약한다.

## 출력 항목

### 수치형 컬럼

| 항목 | 설명 |
|------|------|
| count | 유효값 수 |
| missing | 결측값 수 (%) |
| mean | 평균 |
| std | 표준편차 |
| min / max | 최솟값 / 최댓값 |
| 25% / 50% / 75% | 사분위수 |
| skewness | 왜도 (|값| > 1: 강한 비대칭) |
| kurtosis | 첨도 (초과 첨도, 정규분포=0) |
| cv | 변동계수 (std/mean) |

### 범주형 컬럼

| 항목 | 설명 |
|------|------|
| count | 유효값 수 |
| unique | 고유값 수 |
| top | 최빈값 |
| freq | 최빈값 빈도 |
| missing | 결측값 수 (%) |

## 해석 가이드

| 왜도 범위 | 해석 |
|-----------|------|
| -0.5 ~ 0.5 | 대칭에 가까움 |
| 0.5 ~ 1.0 또는 -1.0 ~ -0.5 | 중간 비대칭 |
| > 1.0 또는 < -1.0 | 강한 비대칭 (변환 고려) |

## CLI

```bash
python3 descriptive_stats.py --csv data.csv
python3 descriptive_stats.py --csv data.csv --columns col1,col2 --output report.md
python3 descriptive_stats.py --md-dir ./notes --frontmatter-keys score,rating --output report.md
```

## 결과 포맷 (Markdown 리포트)

```markdown
# 기술 통계 리포트

## 수치형 변수 요약

| 컬럼 | count | missing | mean | std | min | 25% | 50% | 75% | max | skewness | kurtosis |
...

## 범주형 변수 요약

| 컬럼 | count | unique | top | freq | missing |
...

## 결측값 요약

| 컬럼 | 결측 수 | 결측률 |
...
```
