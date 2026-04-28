"""
descriptive_stats.py
기술 통계: 요약통계량, 왜도/첨도, 결측값 리포트
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from _data_loader import auto_load


def _missing_report(df: pd.DataFrame) -> pd.DataFrame:
    missing = df.isnull().sum()
    pct = (missing / len(df) * 100).round(2)
    return pd.DataFrame({"결측 수": missing, "결측률(%)": pct})[missing > 0]


def describe_numeric(df: pd.DataFrame, columns: Optional[list] = None) -> pd.DataFrame:
    """수치형 컬럼 기술 통계."""
    num_df = df.select_dtypes(include="number")
    if columns:
        num_df = num_df[[c for c in columns if c in num_df.columns]]
    if num_df.empty:
        return pd.DataFrame()

    rows = []
    for col in num_df.columns:
        s = num_df[col].dropna()
        rows.append({
            "컬럼": col,
            "count": len(s),
            "missing": df[col].isnull().sum(),
            "missing%": round(df[col].isnull().mean() * 100, 2),
            "mean": round(s.mean(), 4),
            "std": round(s.std(), 4),
            "min": round(s.min(), 4),
            "25%": round(s.quantile(0.25), 4),
            "50%": round(s.median(), 4),
            "75%": round(s.quantile(0.75), 4),
            "max": round(s.max(), 4),
            "skewness": round(float(stats.skew(s)), 4),
            "kurtosis": round(float(stats.kurtosis(s)), 4),
            "cv": round(s.std() / s.mean(), 4) if s.mean() != 0 else None,
        })
    return pd.DataFrame(rows).set_index("컬럼")


def describe_categorical(df: pd.DataFrame, columns: Optional[list] = None) -> pd.DataFrame:
    """범주형 컬럼 기술 통계."""
    cat_df = df.select_dtypes(exclude="number")
    if columns:
        cat_df = cat_df[[c for c in columns if c in cat_df.columns]]
    if cat_df.empty:
        return pd.DataFrame()

    rows = []
    for col in cat_df.columns:
        s = df[col].dropna()
        top = s.mode().iloc[0] if not s.empty else None
        freq = (s == top).sum() if top is not None else 0
        rows.append({
            "컬럼": col,
            "count": len(s),
            "unique": s.nunique(),
            "top": top,
            "freq": freq,
            "missing": df[col].isnull().sum(),
            "missing%": round(df[col].isnull().mean() * 100, 2),
        })
    return pd.DataFrame(rows).set_index("컬럼")


def format_md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "(해당 없음)\n"
    return df.to_markdown() + "\n"


def run(df: pd.DataFrame, columns: Optional[list] = None) -> str:
    lines = ["# 기술 통계 리포트\n"]

    num_result = describe_numeric(df, columns)
    if not num_result.empty:
        lines.append("## 수치형 변수 요약\n")
        lines.append(format_md_table(num_result))

    cat_result = describe_categorical(df, columns)
    if not cat_result.empty:
        lines.append("## 범주형 변수 요약\n")
        lines.append(format_md_table(cat_result))

    missing = _missing_report(df)
    lines.append("## 결측값 요약\n")
    lines.append(format_md_table(missing) if not missing.empty else "결측값 없음\n")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="기술 통계 분석")
    parser.add_argument("--csv", help="CSV 파일 경로")
    parser.add_argument("--json", help="JSON 파일 경로")
    parser.add_argument("--md-dir", help="Markdown 디렉토리")
    parser.add_argument("--frontmatter-keys", help="frontmatter 키 (쉼표 구분)")
    parser.add_argument("--columns", help="분석할 컬럼 (쉼표 구분, 기본: 전체)")
    parser.add_argument("--output", help="Markdown 리포트 저장 경로")
    args = parser.parse_args()

    df = auto_load(args.csv, args.json, args.md_dir, args.frontmatter_keys)
    columns = [c.strip() for c in args.columns.split(",")] if args.columns else None
    report = run(df, columns)
    print(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n리포트 저장: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
