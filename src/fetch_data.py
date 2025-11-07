#1) Request daily bars for a symbol

# src/fetch_data.py
from pathlib import Path
import argparse
import logging
from logging.handlers import RotatingFileHandler

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from src.config import settings

TF_MAP = {
    "1Day": TimeFrame.Day,
    "1Min": TimeFrame.Minute,
    "5Min": TimeFrame(5, TimeFrame.Minute),
    "15Min": TimeFrame(15, TimeFrame.Minute),
    "30Min": TimeFrame(30, TimeFrame.Minute),
    "1Hour": TimeFrame.Hour,
}

def fetch_bars(symbol: str, start: str, end: str | None, timeframe: str = "1Day") -> pd.DataFrame:
    """Fetch historical bars from Alpaca and return a tidy DataFrame."""
    if timeframe not in TF_MAP:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    client = StockHistoricalDataClient(
        api_key=settings.api_key,
        secret_key=settings.api_secret
    )

    req = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=TF_MAP[timeframe],
        start=start,
        end=end,
    )

    bars = client.get_stock_bars(req)
    df = bars.df.copy()

    if df.empty:
        return df

    # MultiIndex → flat columns
    df = df.reset_index()  # now has symbol, timestamp, ...
    df.rename(columns={
        "timestamp": "ts",
        "trade_count": "trades",
    }, inplace=True)

    cols = [
        c for c in
        ["symbol", "ts", "open", "high", "low", "close", "volume", "vwap", "trades"]
        if c in df.columns
    ]
    df = df[cols].sort_values("ts").reset_index(drop=True)
    return df

#2) Save new data to CSV automatically (with merge)
def merge_and_save(df_new: pd.DataFrame, outfile: Path, logger: logging.Logger) -> pd.DataFrame:
    """Merge newly fetched data into an existing CSV (if any), drop duplicates, and save."""
    if df_new.empty:
        logger.warning("No new data to save.")
        return df_new

    if outfile.exists():
        existing = pd.read_csv(outfile, parse_dates=["ts"])
        logger.info(f"Existing file found: {outfile}, rows={len(existing)}")

        combined = pd.concat([existing, df_new], ignore_index=True)
        # Drop duplicates based on symbol + timestamp
        combined = combined.drop_duplicates(subset=["symbol", "ts"]).sort_values("ts").reset_index(drop=True)
    else:
        logger.info(f"No existing file found. Creating new file at {outfile}")
        combined = df_new.copy()

    outfile.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(outfile, index=False)
    logger.info(f"Saved {len(combined)} total rows → {outfile}")
    return combined

# 3) Add error logging that writes to logs/fetch_data.log
def setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("fetch_data")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if this is called twice
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_path,
            maxBytes=500_000,  # ~500 KB
            backupCount=3,
            encoding="utf-8",
        )
        fmt = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger

#4) Wire it all together in main()
def main():
    parser = argparse.ArgumentParser(description="Fetch historical stock bars from Alpaca")
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol, e.g. SPY")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD (UTC)")
    parser.add_argument("--end", default=None, help="End date YYYY-MM-DD (UTC, optional)")
    parser.add_argument("--timeframe", default="1Day", choices=list(TF_MAP.keys()))
    parser.add_argument("--outfile", default=None, help="Output CSV path (default: data/{symbol}_{timeframe}.csv)")
    args = parser.parse_args()

    data_dir = Path("data")
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_logger(logs_dir / "fetch_data.log")

    outfile = Path(args.outfile) if args.outfile else data_dir / f"{args.symbol}_{args.timeframe}.csv"
    logger.info(
        f"Starting fetch: symbol={args.symbol}, timeframe={args.timeframe}, "
        f"start={args.start}, end={args.end}, outfile={outfile}"
    )

    try:
        df_new = fetch_bars(
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            timeframe=args.timeframe,
        )
        logger.info(f"Fetched {len(df_new)} new rows from Alpaca.")

        merged = merge_and_save(df_new, outfile, logger)
        print(f"Done. Total rows in {outfile}: {len(merged)}")

    except Exception as e:
        logger.exception(f"Error during data fetch: {e}")
        print("❌ Error during data fetch. See logs/fetch_data.log for details.")

if __name__ == "__main__":
    main()
