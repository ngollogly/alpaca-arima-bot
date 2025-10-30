# src/fetch_data.py
from pathlib import Path
from datetime import datetime
import argparse
import pandas as pd

# Alpaca market data (v2)
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Use absolute import to avoid package confusion
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
        end=end
    )

    bars = client.get_stock_bars(req)
    df = bars.df.copy()

    if df.empty:
        return df

    # MultiIndex → flat
    df = df.reset_index()   # columns: symbol, timestamp, open, high, low, close, volume, vwap, trade_count...
    df.rename(columns={
        "timestamp": "ts",
        "trade_count": "trades"
    }, inplace=True)

    cols = [c for c in ["symbol", "ts", "open", "high", "low", "close", "volume", "vwap", "trades"] if c in df.columns]
    df = df[cols].sort_values("ts").reset_index(drop=True)
    return df

def main():
    p = argparse.ArgumentParser(description="Fetch historical stock bars from Alpaca")
    p.add_argument("--symbol", default="SPY")
    p.add_argument("--start", required=True, help="YYYY-MM-DD (UTC)")
    p.add_argument("--end", default=None, help="YYYY-MM-DD (UTC) - optional")
    p.add_argument("--timeframe", default="1Day", choices=list(TF_MAP.keys()))
    p.add_argument("--outfile", default=None, help="CSV path (default: data/{symbol}_{timeframe}.csv)")
    args = p.parse_args()

    df = fetch_bars(symbol=args.symbol, start=args.start, end=args.end, timeframe=args.timeframe)

    outdir = Path("data"); outdir.mkdir(parents=True, exist_ok=True)
    outfile = Path(args.outfile) if args.outfile else outdir / f"{args.symbol}_{args.timeframe}.csv"

    if df.empty:
        print("No data returned. Check symbol, dates, market hours, or data permissions.")
        return

    df.to_csv(outfile, index=False)
    print(f"Saved {len(df):,} rows → {outfile}")

if __name__ == "__main__":
    main()
