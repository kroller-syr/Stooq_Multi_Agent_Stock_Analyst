from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass(frozen=True)
class AppConfig:
    #1-5 Years of data depending on API preference and practicality
    years_back: int = 2

    #GDELT pulls can be very large, so keeping size limited for version 1 of code
    max_articles: int = 30

    #Polite timeouts
    http_timeout_s: int = 20

    #output directory for logs and results
    outputs_dir: str = "outputs"
    figures_dir: str = "outputs/figures"
    reports_dir: str = "outputs/reports"
    llm_model: str = "gpt-4.1-mini"

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def date_range_years_back(years_back: int) -> tuple[datetime, datetime]:
    end = utc_now()
    start = end - timedelta(days=int(365 * years_back))
    return start, end

