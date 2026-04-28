# module.regression

## 목적

수치형 종속변수에 대한 OLS(최소제곱) 선형 회귀를 수행하고 모델 적합도와 잔차를 진단한다.

## 분석 항목

### 모델 요약

| 항목 | 설명 |
|------|------|
| R² | 설명력 (0~1, 높을수록 좋음) |
| Adj. R² | 변수 수 보정 R² |
| F-statistic | 모델 전체 유의성 |
| AIC / BIC | 모델 비교 기준 (낮을수록 좋음) |

### 계수 테이블

| 항목 | 설명 |
|------|------|
| coef | 회귀 계수 |
| std err | 표준 오차 |
| t | t-통계량 |
| P>\|t\| | p-value |
| 95% CI | 신뢰 구간 |

### 다중공선성 진단 (VIF)

```
VIF < 5   : 낮은 다중공선성 (양호)
VIF 5~10  : 중간 (주의)
VIF > 10  : 높은 다중공선성 (제거 또는 결합 고려)
```

### 잔차 진단

| 진단 | 방법 | 해석 |
|------|------|------|
| 정규성 | Shapiro-Wilk (잔차) | p > 0.05: 정규성 충족 |
| 등분산 | Breusch-Pagan | p > 0.05: 등분산 충족 |
| 독립성 | Durbin-Watson (d) | d ≈ 2: 자기상관 없음 |

## CLI

```bash
python3 regression_analysis.py --csv data.csv --target price --features area,rooms,age
python3 regression_analysis.py --csv data.csv --target y --features x1,x2 --vif --output report.md
```

## when_unsure

- VIF 계산: 독립변수 2개 이상일 때만 수행
- 표본 n < 독립변수 수 × 10: "소표본 경고" 출력
- 이진 종속변수 감지: "로지스틱 회귀 고려" 안내 메시지
