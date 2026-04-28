"""
stats_cli.py
통합 CLI 진입점. 분석 종류와 데이터 소스를 지정해 개별 분석 모듈을 호출한다.

사용:
    python3 stats_cli.py --analysis descriptive --csv data.csv
    python3 stats_cli.py --analysis correlation  --csv data.csv --method spearman
    python3 stats_cli.py --analysis distribution --csv data.csv --column score
    python3 stats_cli.py --analysis regression   --csv data.csv --target y --features x1,x2
    python3 stats_cli.py --analysis timeseries   --csv data.csv --date-col date --value-col val
    python3 stats_cli.py --analysis descriptive  --md-dir ./notes --frontmatter-keys score,rating
"""
from __future__ import annotations

import argparse
import sys

from _data_loader import auto_load


def main() -> int:
    parser = argparse.ArgumentParser(
        description="통계 분석 통합 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 데이터 소스
    src = parser.add_argument_group("데이터 소스")
    src.add_argument("--csv", help="CSV 파일 경로")
    src.add_argument("--json", help="JSON 파일 경로")
    src.add_argument("--md-dir", help="Markdown frontmatter 디렉토리")
    src.add_argument("--frontmatter-keys", help="추출할 frontmatter 키 (쉼표 구분)")

    # 분석 종류
    parser.add_argument(
        "--analysis", "-a",
        required=True,
        choices=["descriptive", "correlation", "distribution", "regression", "timeseries", "all"],
        help="수행할 분석 종류",
    )
    parser.add_argument("--output", "-o", help="리포트 저장 디렉토리")

    # 분석별 옵션
    opt = parser.add_argument_group("분석 옵션")
    opt.add_argument("--columns", help="분석 컬럼 (descriptive/correlation, 쉼표 구분)")
    opt.add_argument("--column", help="단일 컬럼 (distribution)")
    opt.add_argument("--method", default="pearson",
                     choices=["pearson", "spearman", "kendall"],
                     help="상관 방법 (기본: pearson)")
    opt.add_argument("--compare-groups", dest="group_col",
                     help="집단 비교 기준 컬럼 (distribution)")
    opt.add_argument("--value-col", help="집단 비교 / 시계열 값 컬럼")
    opt.add_argument("--target", help="회귀 종속변수")
    opt.add_argument("--features", help="회귀 독립변수 (쉼표 구분)")
    opt.add_argument("--date-col", help="시계열 날짜 컬럼")
    opt.add_argument("--freq", help="시계열 빈도 (D/W/M/Q)")

    args = parser.parse_args()

    df = auto_load(args.csv, args.json, args.md_dir, args.frontmatter_keys)

    from pathlib import Path
    import os

    def save(report: str, name: str) -> None:
        if args.output:
            out = Path(args.output) / f"{name}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report, encoding="utf-8")
            print(f"저장: {out}", file=sys.stderr)

    analyses = (
        ["descriptive", "correlation", "distribution", "regression", "timeseries"]
        if args.analysis == "all"
        else [args.analysis]
    )

    for analysis in analyses:
        if analysis == "descriptive":
            from descriptive_stats import run
            cols = [c.strip() for c in args.columns.split(",")] if args.columns else None
            report = run(df, cols)
            print(report)
            save(report, "descriptive_stats")

        elif analysis == "correlation":
            from correlation_analysis import run
            cols = [c.strip() for c in args.columns.split(",")] if args.columns else None
            report = run(df, cols, args.method)
            print(report)
            save(report, "correlation_analysis")

        elif analysis == "distribution":
            from distribution_test import run
            report = run(df, args.column, args.group_col, args.value_col)
            print(report)
            save(report, "distribution_test")

        elif analysis == "regression":
            if not args.target or not args.features:
                print("[오류] --target과 --features가 필요합니다.", file=sys.stderr)
                return 1
            from regression_analysis import run_ols
            features = [f.strip() for f in args.features.split(",")]
            report = run_ols(df, args.target, features)
            print(report)
            save(report, "regression_analysis")

        elif analysis == "timeseries":
            if not args.date_col or not args.value_col:
                print("[오류] --date-col과 --value-col이 필요합니다.", file=sys.stderr)
                return 1
            from time_series import run
            report = run(df, args.date_col, args.value_col, args.freq)
            print(report)
            save(report, "time_series")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
