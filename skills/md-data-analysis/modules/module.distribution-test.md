# module.distribution-test

## 목적

데이터의 분포 특성을 검정하고 분석 방법 선택에 필요한 전제 조건을 확인한다.

## 지원 검정

### 정규성 검정

| 검정 | 함수 | 추천 상황 |
|------|------|-----------|
| **Shapiro-Wilk** | `scipy.stats.shapiro` | n < 5000, 가장 강력 |
| **Kolmogorov-Smirnov** | `scipy.stats.kstest` | 대표본, 단일 분포 비교 |
| **Anderson-Darling** | `scipy.stats.anderson` | 정규/지수/로지스틱 등 다양한 분포 |
| **D'Agostino-Pearson** | `scipy.stats.normaltest` | 왜도+첨도 기반 |

### 동분산 검정 (두 그룹 이상)

| 검정 | 함수 | 비고 |
|------|------|------|
| **Levene** | `scipy.stats.levene` | 정규성 불필요, 일반적 |
| **Bartlett** | `scipy.stats.bartlett` | 정규분포 가정 필요 |

### 두 집단 비교

| 검정 | 함수 | 적용 조건 |
|------|------|-----------|
| **t-test (독립)** | `scipy.stats.ttest_ind` | 정규성 + 등분산 |
| **Welch t-test** | `ttest_ind(equal_var=False)` | 정규성, 이분산 |
| **Mann-Whitney U** | `scipy.stats.mannwhitneyu` | 비모수 |
| **Wilcoxon** | `scipy.stats.wilcoxon` | 비모수, 대응표본 |

### 세 집단 이상 비교

| 검정 | 함수 | 적용 조건 |
|------|------|-----------|
| **One-way ANOVA** | `scipy.stats.f_oneway` | 정규성 + 등분산 |
| **Kruskal-Wallis** | `scipy.stats.kruskal` | 비모수 |

## 검정 결과 해석 가이드

```
p-value < 0.05 → 귀무가설 기각
  정규성 검정: "정규분포가 아닐 가능성" → 비모수 검정 고려
  동분산 검정: "이분산" → Welch t-test 또는 Kruskal-Wallis 사용
  집단 비교: "집단 간 유의한 차이 있음"
```

## CLI

```bash
python3 distribution_test.py --csv data.csv --column score --test shapiro
python3 distribution_test.py --csv data.csv --column score --test all
python3 distribution_test.py --csv data.csv --compare-groups group_col --value-col score
```
