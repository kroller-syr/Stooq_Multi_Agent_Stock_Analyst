import io
import pandas as pd
import requests
from datetime import datetime

import time
import random
import requests

def _get_with_retries(url: str, timeout_s: int, retries: int = 5) -> requests.Response:
    last_err = None
    for attempt in range(retries):
        try:
            return requests.get(
                url,
                timeout=timeout_s,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
        except requests.RequestException as e:
            last_err = e
            sleep_s = min(10.0, (2 ** attempt) + random.random())
            time.sleep(sleep_s)
    raise last_err

def _normalize_stooq_symbol(ticker: str) -> str:
    sym = ticker.strip().upper()
    if "." not in sym:
        sym = f"{sym}.US"
    return sym

def fetch_stock_history_stooq(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeout_s: int = 20,
) -> pd.DataFrame:
    symbol = _normalize_stooq_symbol(ticker)

    # Historical daily CSV endpoint (NOT the quote endpoint)
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"

    resp = _get_with_retries(url, timeout_s=timeout_s)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text))
    df.columns = [c.lower() for c in df.columns]

    # Stooq historical CSV columns are typically: date, open, high, low, close, volume
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.tz_localize(None)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)

    start = start_date.replace(tzinfo=None)
    end = end_date.replace(tzinfo=None)
    df = df[(df["date"] >= start) & (df["date"] <= end)].copy()

    if df.empty:
        raise ValueError(f"No rows in date range for {ticker} between {start.date()} and {end.date()}")

    return df
