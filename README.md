# Multi-Agent Stock + News Research Pipeline (OpenAI)

A terminal-driven, multi-stage “multi-agent” pipeline that pulls historical stock data and time-aligned news coverage,
runs statistical and sentiment analysis, and produces a synthesized report and recommendation using OpenAI. 
The final output includes charts and a Word report saved to disk.

> **Disclaimer:** This project is for educational/informational purposes only and does **not** constitute financial advice.

---

## What This Project Does

Given a single ticker entered in the terminal (e.g., `AAPL`), the system:

1. **Fetches historical stock data** (daily OHLCV) for the selected timeframe (default: ~1 year).
2. **Computes statistical metrics** (returns, volatility, drawdown, etc.) and generates **charts**:
   - Close price series
   - Daily returns series
   - Drawdown series
3. **Fetches news articles** over the *same date range* using GDELT.
4. **Performs sentiment analysis** on articles (baseline lexicon scoring from title + snippet).
5. **Synthesizes a narrative report** and **generates a BUY/HOLD/SELL recommendation** using OpenAI.
6. **Supervisor QA pass** checks the report structure and fixes issues (one corrective pass).
7. **Exports a DOCX report** to `outputs/reports/` and saves figures to `outputs/figures/`.

---

## Architecture Overview

The pipeline is orchestrated by a `Supervisor` that coordinates specialist “agents” (implemented as modules/steps):

- **Stock Data Agent**: downloads historical OHLCV from Stooq (free, no API key)
- **Stats Agent**: computes metrics + saves charts (matplotlib)
- **News Agent**: queries GDELT by timeframe (free, no API key) with retry/backoff
- **Sentiment Agent**: baseline sentiment scoring (positive/negative keyword hits)
- **Synthesis Agent (OpenAI)**: produces a structured report and sources
- **Recommendation Agent (OpenAI)**: outputs a non-personalized recommendation + confidence
- **Supervisor QA (OpenAI)**: checks for missing sections/format and repairs once if needed

---

## Data Sources

- **Stock Data**: Stooq historical CSV (free, daily bars; not guaranteed real-time)
- **News**: GDELT 2.1 DOC API (free; may rate limit with HTTP 429)

---

## Output Artifacts

Generated on each run:

- `outputs/figures/`
  - `{TICKER}_close.png`
  - `{TICKER}_daily_returns.png`
  - `{TICKER}_drawdown.png`
- `outputs/reports/`
  - `{TICKER}_report_YYYYMMDD_HHMMSS.docx`

---

## Requirements

- **Python**: 3.12 recommended
- **OpenAI API key**: required for synthesis + recommendation
- Internet connectivity (for Stooq, GDELT, OpenAI)

---

## Setup

### 1) Create and activate a virtual environment (Windows / PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

#Dependencies
python -m pip install -U openai python-dotenv pydantic pandas numpy requests python-dateutil matplotlib python-docx

#Project Structure
multi_agent_stock_research/
├─ .env
├─ .gitignore
├─ main.py
├─ src/
│  ├─ config.py
│  ├─ state.py
│  ├─ data_stocks.py
│  ├─ data_news.py
│  ├─ analysis_stats.py
│  ├─ analysis_sentiment.py
│  ├─ synthesis.py
│  ├─ report_docx.py
│  └─ supervisor.py
└─ outputs/
   ├─ figures/
   └─ reports/
