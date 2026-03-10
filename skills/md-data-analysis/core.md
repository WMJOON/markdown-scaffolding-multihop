# md-data-analysis — Core

## 역할

Markdown frontmatter 및 범용 정형 데이터(CSV/JSON)에 대한 **통계 분석 스크립트 패키지**.
md-graph-multihop의 데이터 분석 레이어로 동작하거나, 독립 실행형 분석 도구로 사용한다.

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **데이터 소스** | CSV/JSON 파일 또는 Markdown frontmatter 수치 필드 |
| **분석 리포트** | 각 분석 결과를 Markdown 표 + 해석 텍스트로 출력 |
| **frontmatter 로더** | md 파일의 YAML frontmatter에서 수치/범주형 데이터 추출 |
| **통합 CLI** | `stats_cli.py`로 모든 분석 모듈 단일 진입점 제공 |

## 데이터 흐름

```
[입력]
  CSV / JSON            → _data_loader.load_csv() / load_json()
  MD frontmatter        → _data_loader.load_frontmatter()
        ↓
  pandas DataFrame
        ↓
[분석]
  descriptive_stats     → 요약통계 + 분포 리포트
  correlation_analysis  → 상관행렬 + 유의성
  distribution_test     → 정규성/동분산/비모수 검정
  regression_analysis   → OLS 회귀 + 잔차 진단
  time_series           → 추세 분해 + 정상성 검정
        ↓
[출력]
  stdout (텍스트 표)   → 기본 출력
  --output <dir>       → Markdown 리포트 파일 저장
```

## 의존성

```
pandas>=2.0
numpy>=1.24
scipy>=1.11
statsmodels>=0.14   # 회귀 분석, 시계열
pyyaml>=6.0         # MD frontmatter 파싱
```

## 모듈 구성

- `module.descriptive-stats.md` — 기술 통계 정책
- `module.correlation.md` — 상관 분석 정책
- `module.distribution-test.md` — 분포/가설 검정 정책
- `module.regression.md` — 회귀 분석 정책
- `module.time-series.md` — 시계열 분석 정책

## when_unsure

- 컬럼 타입 추론 실패 시: 숫자형 변환 가능 컬럼만 분석, 나머지는 범주형으로 처리
- 표본 크기 < 30: 정규성 검정 결과에 "소표본 주의" 경고 추가
- 결측값 > 20%인 컬럼: 분석 전 경고, `--drop-na` 플래그로 제거 또는 기본 제외
