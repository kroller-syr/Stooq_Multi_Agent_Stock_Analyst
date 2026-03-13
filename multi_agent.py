from src.config import AppConfig
from src.supervisor import Supervisor
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def main():
    ticker = input("Enter a stock ticker (e.g., MSFT): ").strip().upper()
    if not ticker:
        print("No ticker provided.")
        return

    cfg = AppConfig(years_back=1, max_articles=10, llm_model="gpt-4.1-mini")
    supervisor = Supervisor(cfg)

    state = supervisor.run(ticker)

    print("\n=== PIPELINE COMPLETE (Block #4) ===")
    print(f"Ticker: {state.ticker}")
    print(f"Stock rows: {len(state.stock_df) if state.stock_df is not None else 0}")
    print(f"Articles: {len(state.articles)}")
    print(f"Recommendation: {state.recommendation}")
    print(f"Report saved to: {state.report_path}")
    print("Figures:")
    for p in state.figure_paths:
        print(" ", p)

if __name__ == "__main__":
    main()