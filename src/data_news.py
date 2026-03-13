from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import time
import random
import requests

def _get_with_retries(url: str, params: dict, timeout_s: int, retries: int = 8) -> requests.Response:
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                params=params,
                timeout=timeout_s,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )

            # Handle GDELT rate limiting
            if resp.status_code == 429:
                # Respect Retry-After if present, otherwise exponential backoff + jitter
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait_s = float(retry_after)
                else:
                    wait_s = min(30.0, (2 ** attempt) + random.random())

                time.sleep(wait_s)
                continue

            resp.raise_for_status()
            return resp

        except requests.RequestException:
            # Network/DNS hiccup path
            wait_s = min(10.0, (2 ** attempt) + random.random())
            time.sleep(wait_s)

    raise RuntimeError("GDELT request failed after retries (network or rate limit).")

def _gdelt_datetime(dt: datetime) -> str:
    """
    GDELT expects UTC timestamps like YYYYMMDDHHMMSS
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y%m%d%H%M%S")


def fetch_gdelt_articles(
    query: str,
    start_date: datetime,
    end_date: datetime,
    max_records: int = 10,
    timeout_s: int = 20,
) -> list[dict[str, Any]]:
    """
    Uses GDELT 2.1 DOC API (free, no API key) to fetch news articles for `query`
    within [start_date, end_date].
    Returns a list of dicts with basic fields (title, url, source, date, snippet).
    """
    start = _gdelt_datetime(start_date)
    end = _gdelt_datetime(end_date)

    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "artlist",          # list of articles
        "format": "json",
        "startdatetime": start,
        "enddatetime": end,
        "maxrecords": str(max_records),
        "sort": "datedesc",
    }

    resp = _get_with_retries(url, params=params, timeout_s=timeout_s)
    resp.raise_for_status()
    data = resp.json()

    articles = []
    for a in data.get("articles", []) or []:
        articles.append(
            {
                "title": a.get("title"),
                "url": a.get("url"),
                "sourceCountry": a.get("sourceCountry"),
                "sourceCollection": a.get("sourceCollection"),
                "seendate": a.get("seendate"),
                "domain": a.get("domain"),
                "language": a.get("language"),
                "snippet": a.get("snippet"),
            }
        )

    return articles