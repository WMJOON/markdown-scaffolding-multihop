"""
correlation_analysis.py
상관 분석: Pearson / Spearman / Kendall 상관행렬 + 유의성 검정
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


def _sig_star(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return ""


def compute_correlation(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "pearson",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    상관행렬과 p-value 행렬 반환.

    Returns:
        (corr_matrix, pval_matrix)
    """
    num_df = df.select_dtypes(include="number")
    if columns:
        num_df = num_df[[c for c in columns if c in num_df.columns]]
    num_df = num_df.dropna()

    n = len(num_df)
    cols = num_df.columns.tolist()
    corr_mat = pd.DataFrame(np.nan, index=cols, columns=cols)
    pval_mat = pd.DataFrame(np.nan, index=cols, columns=cols)

    func_map = {
        "pearson": stats.pearsonr,
        "spearman": stats.spearmanr,
        "kendall": stats.kendalltau,
    }
    func = func_map.get(method, stats.pearsonr)

    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i == j:
                corr_mat.loc[c1, c2] = 1.0
                pval_mat.loc[c1, c2] = 0.0
            elif i < j:
                r, p = func(num_df[c1], num_df[c2])
                corr_mat.loc[c1, c2] = round(float(r), 4)
                corr_mat.loc[c2, c1] = round(float(r), 4)
                pval_mat.loc[c1, c2] = round(float(p), 4)
                pval_mat.loc[c2, c1] = round(float(p), 4)

    return corr_mat, pval_mat


def strong_pairs(corr_mat: pd.DataFrame, threshold: float = 0.7) -> list[dict]:
    pairs = []
    cols = corr_mat.columns.tolist()
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1:]:
            r = corr_mat.loc[c1, c2]
            if abs(r) >= threshold:
                pairs.append({"변수1": c1, "변수2": c2, "상관계수": r})
    return sorted(pairs, key=lambda x: -abs(x["상관계수"]))


def run(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "pearson",
) -> str:
    corr_mat, pval_mat = compute_correlation(df, columns, method)
    lines = [f"# 상관 분석 리포트 ({method})\n"]

    # 상관행렬
    lines.append("## 상관행렬\n")
    lines.append(corr_mat.round(4).to_markdown() + "\n")

    # 유의성 표시 포함 행렬
    sig_df = corr_mat.copy().astype(str)
    for c1 in corr_mat.index:
        for c2 in corr_mat.columns:
            r = corr_mat.loc[c1, c2]
            p = pval_mat.loc[c1, c2]
            sig_df.loc[c1, c2] = f"{r:.3f}{_sig_star(p)}"
    lines.append("## 상관행렬 (유의성 포함)\n")
    lines.append("> \\*\\*\\* p<0.001  \\*\\* p<0.01  \\* p<0.05\n")
    lines.append(sig_df.to_markdown() + "\n")

    # 강한 상관 쌍
    pairs = strong_pairs(corr_mat, threshold=0.7)
    lines.append("## 강한 상관 쌍 (|r| ≥ 0.7)\n")
    if pairs:
        lines.append(pd.DataFrame(pairs).to_markdown(index=False) + "\n")
        high = [p for p in pairs if abs(p["상관계수"]) >= 0.9]
        if high:
            lines.append(f"\n> ⚠️ 다중공선성 주의 (|r| ≥ 0.9): "
                         f"{', '.join(f'{p[\"변수1\"]}↔{p[\"변수2\"]}' for p in high)}\n")
    else:
        lines.append("강한 상관 쌍 없음 (|r| < 0.7)\n")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="상관 분석")
    parser.add_argument("--csv")
    parser.add_argument("--json")
    parser.add_argument("--md-dir")
    parser.add_argument("--frontmatter-keys")
    parser.add_argument("--columns", help="분석 컬럼 (쉼표 구분)")
    parser.add_argument("--method", default="pearson",
                        choices=["pearson", "spearman", "kendall"])
    parser.add_argument("--output")
    args = parser.parse_args()

    df = auto_load(args.csv, args.json, args.md_dir, args.frontmatter_keys)
    columns = [c.strip() for c in args.columns.split(",")] if args.columns else None
    report = run(df, columns, args.method)
    print(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n리포트 저장: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
