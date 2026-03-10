"""
regression_analysis.py
OLS 선형/다중 회귀 분석: 계수, R², 잔차 진단, VIF
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from _data_loader import auto_load


def _vif(X: pd.DataFrame) -> pd.DataFrame:
    """분산팽창지수(VIF) 계산."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    vif_data = pd.DataFrame()
    vif_data["변수"] = X.columns
    vif_data["VIF"] = [
        round(variance_inflation_factor(X.values, i), 4)
        for i in range(X.shape[1])
    ]
    return vif_data


def run_ols(
    df: pd.DataFrame,
    target: str,
    features: List[str],
    calc_vif: bool = True,
) -> str:
    import statsmodels.api as sm

    sub = df[[target] + features].dropna()
    y = sub[target]
    X = sub[features]
    X_const = sm.add_constant(X)

    model = sm.OLS(y, X_const).fit()
    lines = [f"# 회귀 분석 리포트\n",
             f"**종속변수**: {target}  **독립변수**: {', '.join(features)}\n",
             f"**표본 수**: {len(sub)}\n"]

    # 모델 요약
    lines.append("## 모델 요약\n")
    summary = {
        "R²": round(model.rsquared, 4),
        "Adj. R²": round(model.rsquared_adj, 4),
        "F-statistic": round(model.fvalue, 4),
        "F p-value": round(model.f_pvalue, 6),
        "AIC": round(model.aic, 2),
        "BIC": round(model.bic, 2),
    }
    lines.append(pd.DataFrame([summary]).to_markdown(index=False) + "\n")

    # 계수 테이블
    lines.append("## 회귀 계수\n")
    coef_df = pd.DataFrame({
        "변수": model.params.index,
        "coef": model.params.round(6).values,
        "std err": model.bse.round(6).values,
        "t": model.tvalues.round(4).values,
        "P>|t|": model.pvalues.round(6).values,
        "CI_lower": model.conf_int()[0].round(6).values,
        "CI_upper": model.conf_int()[1].round(6).values,
    })
    coef_df["유의"] = coef_df["P>|t|"].apply(
        lambda p: "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
    )
    lines.append(coef_df.to_markdown(index=False) + "\n")

    # VIF
    if calc_vif and len(features) >= 2:
        try:
            vif_df = _vif(X)
            vif_df["판정"] = vif_df["VIF"].apply(
                lambda v: "양호" if v < 5 else ("주의" if v < 10 else "⚠️ 높음")
            )
            lines.append("## 다중공선성 진단 (VIF)\n")
            lines.append(vif_df.to_markdown(index=False) + "\n")
        except Exception:
            lines.append("## VIF\nVIF 계산 불가 (statsmodels 필요)\n")

    # 잔차 진단
    residuals = model.resid
    lines.append("## 잔차 진단\n")
    diag = {}

    sw_stat, sw_p = stats.shapiro(residuals if len(residuals) <= 5000 else residuals.sample(5000))
    diag["정규성 (Shapiro-Wilk)"] = f"W={sw_stat:.4f}, p={sw_p:.4f} — {'충족' if sw_p >= 0.05 else '위반'}"

    try:
        from statsmodels.stats.diagnostic import het_breuschpagan
        bp_stat, bp_p, _, _ = het_breuschpagan(residuals, X_const)
        diag["등분산 (Breusch-Pagan)"] = f"LM={bp_stat:.4f}, p={bp_p:.4f} — {'충족' if bp_p >= 0.05 else '위반'}"
    except Exception:
        diag["등분산 (Breusch-Pagan)"] = "계산 불가"

    try:
        from statsmodels.stats.stattools import durbin_watson
        dw = durbin_watson(residuals)
        diag["독립성 (Durbin-Watson)"] = f"d={dw:.4f} — {'양호' if 1.5 < dw < 2.5 else '주의'}"
    except Exception:
        diag["독립성 (Durbin-Watson)"] = "계산 불가"

    for k, v in diag.items():
        lines.append(f"- **{k}**: {v}\n")

    # 소표본 경고
    if len(sub) < len(features) * 10:
        lines.append(f"\n> ⚠️ 소표본 경고: 표본({len(sub)}) < 독립변수×10({len(features)*10})\n")

    # 이진 종속변수 안내
    if y.nunique() == 2:
        lines.append("\n> 💡 종속변수가 이진형입니다. 로지스틱 회귀를 고려하세요.\n")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="OLS 회귀 분석")
    parser.add_argument("--csv")
    parser.add_argument("--json")
    parser.add_argument("--md-dir")
    parser.add_argument("--frontmatter-keys")
    parser.add_argument("--target", required=True, help="종속변수 컬럼")
    parser.add_argument("--features", required=True, help="독립변수 컬럼 (쉼표 구분)")
    parser.add_argument("--vif", action="store_true", default=True, help="VIF 계산 포함")
    parser.add_argument("--output")
    args = parser.parse_args()

    df = auto_load(args.csv, args.json, args.md_dir, args.frontmatter_keys)
    features = [f.strip() for f in args.features.split(",")]
    report = run_ols(df, args.target, features, calc_vif=args.vif)
    print(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n리포트 저장: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
