"""
distribution_test.py
분포 검정: 정규성(Shapiro/KS/Anderson/D'Agostino), 동분산, 집단 비교
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
from scipy import stats

from _data_loader import auto_load


def normality_tests(series: pd.Series) -> dict:
    """단일 수치형 시리즈의 정규성 검정."""
    s = series.dropna()
    n = len(s)
    results = {"n": n, "검정": {}}

    # Shapiro-Wilk (n < 5000 권장)
    if n >= 3:
        stat, p = stats.shapiro(s if n <= 5000 else s.sample(5000, random_state=42))
        results["검정"]["Shapiro-Wilk"] = {
            "statistic": round(float(stat), 6),
            "p-value": round(float(p), 6),
            "정규성": "충족" if p >= 0.05 else "기각",
            "비고": "n>5000: 표본 5000개 사용" if n > 5000 else "",
        }

    # KS test (정규분포)
    s_std = (s - s.mean()) / s.std()
    stat_ks, p_ks = stats.kstest(s_std, "norm")
    results["검정"]["Kolmogorov-Smirnov"] = {
        "statistic": round(float(stat_ks), 6),
        "p-value": round(float(p_ks), 6),
        "정규성": "충족" if p_ks >= 0.05 else "기각",
        "비고": "",
    }

    # D'Agostino-Pearson (n >= 8)
    if n >= 8:
        stat_d, p_d = stats.normaltest(s)
        results["검정"]["D'Agostino-Pearson"] = {
            "statistic": round(float(stat_d), 6),
            "p-value": round(float(p_d), 6),
            "정규성": "충족" if p_d >= 0.05 else "기각",
            "비고": "",
        }

    # Anderson-Darling
    ad = stats.anderson(s, dist="norm")
    crit_5 = ad.critical_values[2]  # 5% 임계값
    results["검정"]["Anderson-Darling"] = {
        "statistic": round(float(ad.statistic), 6),
        "p-value": "—",
        "정규성": "충족" if ad.statistic < crit_5 else "기각",
        "비고": f"5% 임계값={crit_5:.4f}",
    }

    if n < 30:
        results["경고"] = "n < 30: 소표본. 정규성 검정 결과 해석 주의."
    return results


def homogeneity_test(df: pd.DataFrame, group_col: str, value_col: str) -> dict:
    """동분산 검정: Levene + Bartlett."""
    groups = [g[value_col].dropna().values
              for _, g in df.groupby(group_col)
              if g[value_col].notna().sum() >= 2]
    if len(groups) < 2:
        return {"오류": "그룹이 2개 미만"}

    lev_stat, lev_p = stats.levene(*groups)
    bar_stat, bar_p = stats.bartlett(*groups)
    return {
        "Levene": {"statistic": round(float(lev_stat), 4),
                   "p-value": round(float(lev_p), 4),
                   "등분산": "충족" if lev_p >= 0.05 else "기각"},
        "Bartlett": {"statistic": round(float(bar_stat), 4),
                     "p-value": round(float(bar_p), 4),
                     "등분산": "충족" if bar_p >= 0.05 else "기각"},
    }


def group_comparison(df: pd.DataFrame, group_col: str, value_col: str) -> str:
    """집단 간 비교: 그룹 수에 따라 t-test 또는 ANOVA/Kruskal-Wallis."""
    groups = {name: g[value_col].dropna().values
              for name, g in df.groupby(group_col)}
    k = len(groups)
    lines = [f"### 집단 비교: {value_col} by {group_col} ({k}그룹)\n"]

    if k == 2:
        g1, g2 = list(groups.values())
        t_stat, t_p = stats.ttest_ind(g1, g2, equal_var=False)
        mw_stat, mw_p = stats.mannwhitneyu(g1, g2, alternative="two-sided")
        lines.append(f"**Welch t-test**: t={t_stat:.4f}, p={t_p:.4f} "
                     f"({'유의' if t_p < 0.05 else '비유의'})\n")
        lines.append(f"**Mann-Whitney U**: U={mw_stat:.1f}, p={mw_p:.4f} "
                     f"({'유의' if mw_p < 0.05 else '비유의'})\n")
    elif k >= 3:
        f_stat, f_p = stats.f_oneway(*groups.values())
        kw_stat, kw_p = stats.kruskal(*groups.values())
        lines.append(f"**One-way ANOVA**: F={f_stat:.4f}, p={f_p:.4f} "
                     f"({'유의' if f_p < 0.05 else '비유의'})\n")
        lines.append(f"**Kruskal-Wallis**: H={kw_stat:.4f}, p={kw_p:.4f} "
                     f"({'유의' if kw_p < 0.05 else '비유의'})\n")
    return "\n".join(lines)


def format_test_result(col: str, result: dict) -> str:
    lines = [f"### {col} (n={result['n']})\n"]
    if "경고" in result:
        lines.append(f"> ⚠️ {result['경고']}\n")
    rows = []
    for test_name, r in result["검정"].items():
        rows.append({
            "검정": test_name,
            "statistic": r["statistic"],
            "p-value": r["p-value"],
            "정규성": r["정규성"],
            "비고": r.get("비고", ""),
        })
    lines.append(pd.DataFrame(rows).to_markdown(index=False) + "\n")
    return "\n".join(lines)


def run(
    df: pd.DataFrame,
    column: Optional[str] = None,
    group_col: Optional[str] = None,
    value_col: Optional[str] = None,
) -> str:
    lines = ["# 분포 검정 리포트\n"]

    # 정규성 검정
    num_df = df.select_dtypes(include="number")
    cols = [column] if column and column in num_df.columns else num_df.columns.tolist()
    if cols:
        lines.append("## 정규성 검정\n")
        for col in cols:
            result = normality_tests(df[col])
            lines.append(format_test_result(col, result))

    # 동분산 + 집단 비교
    if group_col and value_col:
        hom = homogeneity_test(df, group_col, value_col)
        lines.append("## 동분산 검정\n")
        rows = [{"검정": k, **v} for k, v in hom.items() if isinstance(v, dict)]
        lines.append(pd.DataFrame(rows).to_markdown(index=False) + "\n")
        lines.append(group_comparison(df, group_col, value_col))

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="분포 검정")
    parser.add_argument("--csv")
    parser.add_argument("--json")
    parser.add_argument("--md-dir")
    parser.add_argument("--frontmatter-keys")
    parser.add_argument("--column", help="정규성 검정 대상 컬럼 (미지정 시 수치형 전체)")
    parser.add_argument("--compare-groups", dest="group_col",
                        help="집단 비교 기준 컬럼")
    parser.add_argument("--value-col", help="집단 비교 값 컬럼")
    parser.add_argument("--output")
    args = parser.parse_args()

    df = auto_load(args.csv, args.json, args.md_dir, args.frontmatter_keys)
    report = run(df, args.column, args.group_col, args.value_col)
    print(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n리포트 저장: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
