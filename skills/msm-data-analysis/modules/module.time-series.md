# module.time-series

## 목적

날짜/시간 인덱스를 가진 시계열 데이터의 추세, 계절성, 정상성을 분석한다.

## 분석 항목

### 기본 통계

- 기간, 빈도 추정, 결측 타임스텝 수
- 전체 추세 방향 (선형 회귀 기울기)

### 정상성 검정 (ADF)

```
ADF Statistic < Critical Value (5%) 또는 p-value < 0.05
→ 정상성 충족 (단위근 없음) → 차분 불필요
→ 아니면 1차 차분 후 재검정 권장
```

| 출력 | 설명 |
|------|------|
| ADF Statistic | 검정 통계량 |
| p-value | 유의확률 |
| Critical Values | 1%, 5%, 10% 임계값 |
| Is Stationary | 판정 결과 |

### 이동 통계

- Rolling Mean (window=7/30) — 추세 평활화
- Rolling Std — 분산 변화 감지

### 자기상관 (ACF/PACF 텍스트 요약)

- Ljung-Box 검정: 자기상관 유의성
- lag 1, 7, 14, 30 자기상관 계수 출력

### STL 분해 (statsmodels)

추세(Trend) + 계절성(Seasonal) + 잔차(Residual) 분리.
결과를 수치 테이블로 출력 (처음/끝 10행).

## CLI

```bash
python3 time_series.py --csv data.csv --date-col date --value-col sales
python3 time_series.py --csv data.csv --date-col date --value-col revenue --freq M --output report.md
```

## when_unsure

- 날짜 파싱 실패 시: `--date-format` 옵션 제공 안내
- 관측값 < 24: STL 분해 건너뜀 (계절성 추정 불가)
- 결측 타임스텝 > 5%: 선형 보간 후 분석 (경고 표시)
