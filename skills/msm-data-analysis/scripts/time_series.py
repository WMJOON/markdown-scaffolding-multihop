"""
time_series.py
시계열 분석: ADF 정상성 검정, 이동통계, 자기상관(Ljung-Box), STL 분해
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


def load_ts(df: pd.DataFrame, date_col: str, value_col: str,
            freq: Optional[str] = None) -> pd.Series:
    """DataFrame에서 시계열 Series 생성."""
    ts = df[[date_col, value_col]].copy()
    ts[date_col] = pd.to_datetime(ts[date_col])
    ts = ts.sort_values(date_col).set_index(date_col)[value_col]
    if freq:
        ts = ts.asfreq(freq)
    # 결측 타임스텝 선형 보간
    missing_before = ts.isnull().sum()
    if missing_before > 0:
        ts = ts.interpolate(method="linear")
    return ts, missing_before


def adf_test(ts: pd.Series) -> dict:
    """ADF 정상성 검정."""
    from statsmodels.tsa.stattools import adfuller
    result = adfuller(ts.dropna(), autolag="AIC")
    return {
        "ADF Statistic": round(result[0], 6),
        "p-value": round(result[1], 6),
        "Is Stationary": result[1] < 0.05,
        "Critical Value 1%": round(result[4]["1%"], 4),
        "Critical Value 5%": round(result[4]["5%"], 4),
        "Critical Value 10%": round(result[4]["10%"], 4),
    }


def rolling_stats(ts: pd.Series, window: int = 7) -> pd.DataFrame:
    """이동평균 + 이동표준편차."""
    df = pd.DataFrame({
        "value": ts,
        f"rolling_mean_{window}": ts.rolling(window).mean().round(4),
        f"rolling_std_{window}": ts.rolling(window).std().round(4),
    })
    return df


def ljung_box(ts: pd.Series, lags: list = None) -> pd.DataFrame:
    """Ljung-Box 자기상관 검정."""
    from statsmodels.stats.diagnostic import acorr_ljungbox
    lags = lags or [1, 7, 14, 30]
    valid_lags = [l for l in lags if l < len(ts)]
    if not valid_lags:
        return pd.DataFrame()
    lb = acorr_ljungbox(ts.dropna(), lags=valid_lags, return_df=True)
    lb.index.name = "lag"
    lb = lb.reset_index()
    lb.columns = ["lag", "lb_stat", "p-value"]
    lb["유의"] = lb["p-value"].apply(
        lambda p: "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))
    )
    lb["lb_stat"] = lb["lb_stat"].round(4)
    lb["p-value"] = lb["p-value"].round(6)
    return lb


def stl_decompose(ts: pd.Series, period: int = None) -> Optional[pd.DataFrame]:
    """STL 분해. 관측값 < 2*period이면 None 반환."""
    from statsmodels.tsa.seasonal import STL
    if period is None:
        period = _guess_period(ts)
    if period is None or len(ts) < 2 * period:
        return None
    stl = STL(ts.dropna(), period=period, robust=True).fit()
    df = pd.DataFrame({
        "trend": stl.trend.round(4),
        "seasonal": stl.seasonal.round(4),
        "residual": stl.resid.round(4),
    })
    return df


def _guess_period(ts: pd.Series) -> Optional[int]:
    """인덱스 빈도로 계절 주기 추정."""
    if ts.index.freq is None:
        return None
    freq_str = str(ts.index.freq)
    mapping = {"D": 7, "W": 52, "M": 12, "MS": 12, "Q": 4, "QS": 4, "A": None, "AS": None, "H": 24}
    for k, v in mapping.items():
        if freq_str.startswith(k):
            return v
    return None


def run(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    freq: Optional[str] = None,
) -> str:
    try:
        ts, missing_before = load_ts(df, date_col, value_col, freq)
    except Exception as e:
        return f"# 시계열 분석 오류\n\n{e}\n"

    lines = [f"# 시계열 분석 리포트\n",
             f"**변수**: {value_col}  **날짜**: {date_col}  **기간**: {ts.index.min()} ~ {ts.index.max()}\n",
             f"**관측 수**: {len(ts)}  **결측 타임스텝(보간)**: {missing_before}\n"]

    # 기본 통계
    slope, intercept, r, p, _ = stats.linregress(np.arange(len(ts)), ts.values)
    trend_dir = "상승" if slope > 0 else "하락"
    lines.append(f"**추세**: {trend_dir} (기울기={slope:.4f}, R={r:.4f})\n")

    # ADF
    lines.append("## ADF 정상성 검정\n")
    try:
        adf = adf_test(ts)
        adf_df = pd.DataFrame([adf])
        lines.append(adf_df.to_markdown(index=False) + "\n")
        if not adf["Is Stationary"]:
            lines.append("> ℹ️ 비정상성 감지. 1차 차분 후 재검정을 권장합니다.\n")
        # 1차 차분 후 ADF
        if not adf["Is Stationary"]:
            diff_ts = ts.diff().dropna()
            adf2 = adf_test(diff_ts)
            lines.append("### 1차 차분 후 ADF\n")
            lines.append(pd.DataFrame([adf2]).to_markdown(index=False) + "\n")
    except Exception as e:
        lines.append(f"ADF 계산 불가: {e}\n")

    # 이동 통계
    window = min(7, max(2, len(ts) // 10))
    roll = rolling_stats(ts, window=window)
    lines.append(f"## 이동 통계 (window={window})\n")
    lines.append(roll.tail(10).to_markdown() + "\n")

    # Ljung-Box
    lines.append("## 자기상관 (Ljung-Box)\n")
    try:
        lb = ljung_box(ts)
        if not lb.empty:
            lines.append(lb.to_markdown(index=False) + "\n")
    except Exception as e:
        lines.append(f"Ljung-Box 계산 불가: {e}\n")

    # STL 분해
    lines.append("## STL 분해\n")
    try:
        stl_df = stl_decompose(ts)
        if stl_df is None:
            lines.append("관측값 부족으로 STL 분해 건너뜀 (최소 2×period 필요)\n")
        else:
            lines.append("*(처음 5행 / 마지막 5행)*\n")
            lines.append(pd.concat([stl_df.head(5), stl_df.tail(5)]).to_markdown() + "\n")
    except Exception as e:
        lines.append(f"STL 분해 불가: {e}\n")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="시계열 분석")
    parser.add_argument("--csv")
    parser.add_argument("--json")
    parser.add_argument("--md-dir")
    parser.add_argument("--frontmatter-keys")
    parser.add_argument("--date-col", required=True, help="날짜 컬럼명")
    parser.add_argument("--value-col", required=True, help="값 컬럼명")
    parser.add_argument("--freq", help="시계열 빈도 (D/W/M/Q 등)")
    parser.add_argument("--output")
    args = parser.parse_args()

    df = auto_load(args.csv, args.json, args.md_dir, args.frontmatter_keys)
    report = run(df, args.date_col, args.value_col, args.freq)
    print(report)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"\n리포트 저장: {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
