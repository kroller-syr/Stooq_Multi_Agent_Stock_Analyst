import os

from openai import OpenAI

from src.config import AppConfig, date_range_years_back
from src.state import ProjectState
from src.data_stocks import fetch_stock_history_stooq
from src.data_news import fetch_gdelt_articles
from src.analysis_stats import compute_stats_and_charts
from src.analysis_sentiment import score_articles_sentiment
from src.synthesis import generate_report_and_recommendation, supervisor_qa_retry_if_needed
from src.report_docx import save_report_docx


class Supervisor:
    def __init__(self, cfg: AppConfig):
        self.cfg = cfg
        os.makedirs(cfg.figures_dir, exist_ok=True)
        os.makedirs(cfg.reports_dir, exist_ok=True)
        self.client = OpenAI()

    def run(self, ticker: str) -> ProjectState:
        start, end = date_range_years_back(self.cfg.years_back)

        state = ProjectState(
            ticker=ticker,
            company_query=ticker,
            start_date=start,
            end_date=end,
        )

        # A) Stock data
        state.stock_df = fetch_stock_history_stooq(
            ticker=ticker,
            start_date=start,
            end_date=end,
            timeout_s=self.cfg.http_timeout_s,
        )
        self._validate_stock(state)

        # B) Stats + charts
        stats_res = compute_stats_and_charts(
            stock_df=state.stock_df,
            ticker=ticker,
            figures_dir=self.cfg.figures_dir,
        )
        state.stats = stats_res.metrics
        state.figure_paths.extend(stats_res.figure_paths)
        self._validate_stats(state)

        # C) News
        state.articles = fetch_gdelt_articles(
            query=state.company_query,
            start_date=start,
            end_date=end,
            max_records=self.cfg.max_articles,
            timeout_s=self.cfg.http_timeout_s,
        )
        self._validate_articles(state)

        # D) Sentiment
        state.sentiment = score_articles_sentiment(state.articles)
        self._validate_sentiment(state)

        # E/F) LLM synthesis + recommendation
        first = generate_report_and_recommendation(
            client=self.client,
            state=state,
            model=self.cfg.llm_model,
        )
        final = supervisor_qa_retry_if_needed(
            client=self.client,
            state=state,
            first_pass=first,
            model=self.cfg.llm_model,
        )

        state.report_text = final.get("report_markdown")
        state.recommendation = final.get("recommendation")

        # Stable appendix refs from retrieved articles
        refs_lines = ["References (Article URLs)"]
        per_article = state.sentiment.get("per_article") or []
        for i, a in enumerate(per_article[:20], start=1):
            title = a.get("title") or "Untitled"
            url = a.get("url") or ""
            refs_lines.append(f"[{i}] {title} — {url}")
        references_text = "\n".join(refs_lines)

        # Save DOCX report
        state.report_path = save_report_docx(
            ticker=state.ticker,
            report_markdown=state.report_text or "",
            references_text=references_text,
            figure_paths=state.figure_paths,
            reports_dir=self.cfg.reports_dir,
        )

        return state

    # --- validations ---
    def _validate_stock(self, state: ProjectState) -> None:
        if state.stock_df is None or state.stock_df.empty:
            raise RuntimeError("Stock agent returned no data.")
        if len(state.stock_df) < 50:
            raise RuntimeError(f"Too few stock rows ({len(state.stock_df)}). Check timeframe/source.")

    def _validate_stats(self, state: ProjectState) -> None:
        if not state.stats:
            raise RuntimeError("Stats agent produced empty metrics.")
        if not state.figure_paths:
            raise RuntimeError("Stats agent produced no figures.")

    def _validate_articles(self, state: ProjectState) -> None:
        if state.articles is None:
            state.articles = []

    def _validate_sentiment(self, state: ProjectState) -> None:
        if not state.sentiment:
            raise RuntimeError("Sentiment agent produced empty output.")