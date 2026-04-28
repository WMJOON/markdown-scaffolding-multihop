---
name: msm-data-analysis
description: >
  Markdown frontmatter 또는 CSV/JSON 데이터에 대해 기술 통계, 상관 분석, 분포 검정,
  회귀 분석, 시계열 분석을 수행하는 통계 분석 스크립트 패키지.
  md-graph-multihop과 연계하여 그래프 노드의 frontmatter 수치 데이터를 분석하거나,
  독립적인 CSV/JSON 데이터를 분석할 수 있다.
  트리거 예시: "기술통계 내줘", "상관관계 분석해줘", "정규성 검정해줘",
  "회귀분석 돌려줘", "시계열 분석해줘", "데이터 분석 스크립트 써줘".
---

# md-data-analysis

Markdown frontmatter 데이터 및 범용 CSV/JSON 데이터에 대한 **통계 분석 스크립트 패키지**.

## 스크립트

```
scripts/
├── stats_cli.py              # 통합 CLI 진입점
├── _data_loader.py           # 공통 데이터 로더 (CSV/JSON/MD frontmatter)
├── descriptive_stats.py      # 기술 통계
├── correlation_analysis.py   # 상관 분석
├── distribution_test.py      # 분포 검정 + 가설 검정
├── regression_analysis.py    # 회귀 분석 (OLS)
└── time_series.py            # 시계열 분석
```

## 빠른 시작

```bash
# 통합 CLI — 분석 종류 + 데이터 소스 지정
python3 stats_cli.py --analysis descriptive --csv data.csv
python3 stats_cli.py --analysis correlation  --csv data.csv --columns col1,col2,col3
python3 stats_cli.py --analysis distribution --csv data.csv --column col1
python3 stats_cli.py --analysis regression   --csv data.csv --target y --features x1,x2
python3 stats_cli.py --analysis timeseries   --csv data.csv --date-col date --value-col value

# Markdown frontmatter에서 직접 읽기 (md-graph-multihop 연계)
python3 stats_cli.py --analysis descriptive --md-dir ./notes --frontmatter-keys rating,score,count

# 결과를 md 리포트로 저장
python3 stats_cli.py --analysis descriptive --csv data.csv --output ./reports/
```

## 개별 스크립트 직접 실행

```bash
python3 descriptive_stats.py    --csv data.csv --output report.md
python3 correlation_analysis.py --csv data.csv --columns col1,col2 --method pearson
python3 distribution_test.py    --csv data.csv --column score --test shapiro,ks,anderson
python3 regression_analysis.py  --csv data.csv --target price --features area,rooms,age
python3 time_series.py          --csv data.csv --date-col date --value-col sales
```

## 입력 소스

| 소스 | 옵션 | 비고 |
|------|------|------|
| CSV 파일 | `--csv <path>` | pandas 기본 처리 |
| JSON 파일 | `--json <path>` | records 또는 dict 형식 |
| MD frontmatter | `--md-dir <dir> --frontmatter-keys k1,k2` | graph-config.yaml 연동 가능 |

## 분석 모듈

| 모듈 | 분석 내용 |
|------|-----------|
| `module.descriptive-stats.md` | 요약통계, 분포 요약, 결측값 리포트 |
| `module.correlation.md` | Pearson/Spearman/Kendall 상관행렬 |
| `module.distribution-test.md` | 정규성 검정, 동분산 검정, 비모수 검정 |
| `module.regression.md` | OLS 선형/다중 회귀, VIF, 잔차 진단 |
| `module.time-series.md` | 추세 분해, ADF 정상성 검정, 자기상관 |
