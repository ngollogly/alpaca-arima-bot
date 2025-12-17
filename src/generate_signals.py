from pathlib import Path
import pandas as pd

from src.modeling_arima import forecast_next_return
from src.config_strategy import PORTFOLIOS, DEFAULT_PORTFOLIO, UP_THRESHOLD, DOWN_THRESHOLD

# Compute project root based on THIS file's location
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"


def classify_signal(r):
    if r > UP_THRESHOLD:
        return "long"
    elif r < DOWN_THRESHOLD:
        return "short"
    else:
        return "flat"


def build_signals_df(portfolio_name: str = DEFAULT_PORTFOLIO) -> pd.DataFrame:
    symbols = PORTFOLIOS[portfolio_name]
    records = []

    for sym in symbols:
        path = DATA_DIR / f"{sym}_1Day_returns_only.csv"
        df = pd.read_csv(path, parse_dates=["ts"])
        df = df.sort_values("ts").dropna(subset=["return"]).reset_index(drop=True)

        series = df["return"]
        forecast = forecast_next_return(series)

        records.append(
            {
                "symbol": sym,
                "forecast_return": forecast,
                "signal": classify_signal(forecast),
                "n_points": len(series),
            }
        )

    return pd.DataFrame(records)