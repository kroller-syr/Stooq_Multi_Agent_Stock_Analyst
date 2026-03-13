from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import pandas as pd

@dataclass
class ProjectState:
    ticker: str
    company_query: str

    start_date: datetime
    end_date: datetime

    #Artifacts produced by the pipeline
    stock_df: Optional[pd.DataFrame] = None
    stats: dict[str, Any] = field(default_factory=dict)

    articles: list[dict[str, Any]] = field(default_factory=list)
    sentiment: dict[str, Any] = field(default_factory=dict)

    report_text: Optional[str] = None
    recommendation: Optional[str] = None

    #File Outputs
    figure_paths: list[str] = field(default_factory=list)
    report_path: Optional[str] = None
