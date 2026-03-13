import os
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


@dataclass
class StatsResult:
    metrics: dict[str, Any]
    figure_paths: list[str]


def compute_stats_and_charts(
    stock_df: pd.DataFrame,
    ticker: str,
    figures_dir: str = "outputs/figures",
) -> StatsResult:
    """
    Computes basic return statistics and saves figures:
      1) Close price over time
      2) Daily returns over time
      3) Drawdown over time
    """
    os.makedirs(figures_dir, exist_ok=True)

    df = stock_df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    # Daily log returns
    df["ret"] = df["close"].pct_change()
    df["log_ret"] = np.log(df["close"]).diff()

    # Equity curve & drawdown (based on close)
    df["equity"] = (1.0 + df["ret"].fillna(0.0)).cumprod()
    df["peak"] = df["equity"].cummax()
    df["drawdown"] = df["equity"] / df["peak"] - 1.0

    # Metrics (annualization assumes ~252 trading days/year)
    valid_rets = df["ret"].dropna()
    mean_daily = float(valid_rets.mean()) if len(valid_rets) else float("nan")
    vol_daily = float(valid_rets.std()) if len(valid_rets) else float("nan")
    ann_return = (1.0 + mean_daily) ** 252 - 1.0 if np.isfinite(mean_daily) else float("nan")
    ann_vol = vol_daily * np.sqrt(252) if np.isfinite(vol_daily) else float("nan")

    max_dd = float(df["drawdown"].min()) if len(df) else float("nan")

    metrics = {
        "rows": int(len(df)),
        "start_date": str(df["date"].iloc[0].date()),
        "end_date": str(df["date"].iloc[-1].date()),
        "start_close": float(df["close"].iloc[0]),
        "end_close": float(df["close"].iloc[-1]),
        "total_return": float(df["close"].iloc[-1] / df["close"].iloc[0] - 1.0),
        "mean_daily_return": mean_daily,
        "daily_volatility": vol_daily,
        "annualized_return_est": float(ann_return),
        "annualized_volatility_est": float(ann_vol),
        "max_drawdown": max_dd,
    }

    paths: list[str] = []

    # Figure 1: Close price
    fig1 = plt.figure()
    plt.plot(df["date"], df["close"])
    plt.title(f"{ticker} Close Price")
    plt.xlabel("Date")
    plt.ylabel("Close")
    p1 = os.path.join(figures_dir, f"{ticker}_close.png")
    plt.tight_layout()
    plt.savefig(p1, dpi=160)
    plt.close(fig1)
    paths.append(p1)

    # Figure 2: Daily returns
    fig2 = plt.figure()
    plt.plot(df["date"], df["ret"])
    plt.title(f"{ticker} Daily Returns")
    plt.xlabel("Date")
    plt.ylabel("Return")
    p2 = os.path.join(figures_dir, f"{ticker}_daily_returns.png")
    plt.tight_layout()
    plt.savefig(p2, dpi=160)
    plt.close(fig2)
    paths.append(p2)

    # Figure 3: Drawdown
    fig3 = plt.figure()
    plt.plot(df["date"], df["drawdown"])
    plt.title(f"{ticker} Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    p3 = os.path.join(figures_dir, f"{ticker}_drawdown.png")
    plt.tight_layout()
    plt.savefig(p3, dpi=160)
    plt.close(fig3)
    paths.append(p3)

    return StatsResult(metrics=metrics, figure_paths=paths)