# module.correlation

## 목적

수치형 변수 간 상관관계를 정량화하고 통계적 유의성을 검정한다.

## 지원 방법

| 방법 | 적용 조건 | 비고 |
|------|-----------|------|
| **Pearson** | 정규분포 가정, 선형 관계 | 기본값 |
| **Spearman** | 비모수, 단조 관계 | 순위 기반 |
| **Kendall τ** | 비모수, 소표본 안정적 | 계산 비용 높음 |

## 출력 항목

1. **상관행렬** — 선택된 수치형 컬럼 전체 × 전체
2. **유의성 행렬** — p-value 기준 (*, **, ***)
3. **강한 상관 쌍** — |r| ≥ 0.7인 변수 쌍 목록
4. **다중공선성 경고** — |r| ≥ 0.9인 쌍 (회귀 분석 전 확인 권장)

## 유의성 기호

| 기호 | p-value |
|------|---------|
| *** | < 0.001 |
| ** | < 0.01 |
| * | < 0.05 |
| (빈칸) | ≥ 0.05 |

## CLI

```bash
python3 correlation_analysis.py --csv data.csv --method pearson
python3 correlation_analysis.py --csv data.csv --columns x1,x2,x3 --method spearman
python3 correlation_analysis.py --csv data.csv --method kendall --output report.md
```

## when_unsure

- 컬럼 지정 없을 때: 수치형 컬럼 전체 자동 선택
- 표본 n < 30: Spearman 또는 Kendall 권장 메시지 출력
