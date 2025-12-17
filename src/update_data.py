from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta, timezone
import csv

import pandas as pd

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from .config import settings
from .config_strategy import PORTFOLIOS, DEFAULT_PORTFOLIO


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

AUDIT_LOG = LOG_DIR / "data_updates.csv"


def _append_audit(row: dict):
    file_exists = AUDIT_LOG.exists()
    with AUDIT_LOG.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp_utc",
                "symbol",
                "bars_file",
                "had_existing_file",
                "last_ts_before",
                "requested_start",
                "requested_end",
                "new_rows_fetched",
                "rows_after_save",
                "status",
                "message",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _read_existing_last_ts(path: Path) -> tuple[bool, datetime | None]:
    if not path.exists():
        return False, None

    df = pd.read_csv(path, parse_dates=["ts"])
    if df.empty:
        return True, None

    df = df.dropna(subset=["ts"]).sort_values("ts")
    last_ts = df["ts"].iloc[-1]
    # Ensure timezone-aware UTC for safe comparisons
    if last_ts.tzinfo is None:
        last_ts = last_ts.replace(tzinfo=timezone.utc)
    else:
        last_ts = last_ts.astimezone(timezone.utc)
    return True, last_ts


def _fetch_daily_bars(symbol: str, start_utc: datetime, end_utc: datetime) -> pd.DataFrame:
    """
    Fetch daily bars from Alpaca between start_utc and end_utc (UTC).
    Returns DataFrame with columns at least: ts, open, high, low, close, volume
    """
    client = StockHistoricalDataClient(
        api_key=settings.api_key,
        secret_key=settings.api_secret,
    )

    req = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start_utc,
        end=end_utc,
        adjustment="raw",
    )

    bars = client.get_stock_bars(req).df

    if bars is None or len(bars) == 0:
        return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])

    # Alpaca returns multi-index df: (symbol, timestamp)
    bars = bars.reset_index()

    # Normalize column name for timestamp
    if "timestamp" in bars.columns:
        bars = bars.rename(columns={"timestamp": "ts"})

    # Keep only this symbol (defensive)
    if "symbol" in bars.columns:
        bars = bars[bars["symbol"] == symbol].copy()

    # Keep common columns
    keep = [c for c in ["ts", "open", "high", "low", "close", "volume"] if c in bars.columns]
    bars = bars[keep].copy()

    # Ensure ts is datetime
    bars["ts"] = pd.to_datetime(bars["ts"], utc=True)

    return bars.sort_values("ts").reset_index(drop=True)


def _merge_save_bars(existing_path: Path, new_bars: pd.DataFrame) -> tuple[int, int]:
    """
    Merge new bars into existing CSV:
    - dedupe on ts
    - sort by ts
    Returns (new_rows_added, total_rows_after_save)
    """
    if existing_path.exists():
        df_old = pd.read_csv(existing_path, parse_dates=["ts"])
        df_old["ts"] = pd.to_datetime(df_old["ts"], utc=True)
    else:
        df_old = pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])

    before = len(df_old)

    if not new_bars.empty:
        df = pd.concat([df_old, new_bars], ignore_index=True)
    else:
        df = df_old.copy()

    df = df.drop_duplicates(subset=["ts"]).sort_values("ts").reset_index(drop=True)

    after = len(df)
    new_rows_added = max(0, after - before)

    existing_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(existing_path, index=False)

    return new_rows_added, after


def _write_returns_only(bars_csv: Path, returns_csv: Path):
    df = pd.read_csv(bars_csv, parse_dates=["ts"])
    df = df.sort_values("ts").reset_index(drop=True)
    df["return"] = df["close"].pct_change()
    df = df.dropna(subset=["return"])[["ts", "return"]]
    returns_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(returns_csv, index=False)


def update_portfolio_data(
    portfolio_name: str = DEFAULT_PORTFOLIO,
    lookback_days_if_missing: int = 3650,  # ~10 years
    end_buffer_days: int = 3,              # extend end a bit to avoid market holiday gaps
):
    """
    Incrementally update daily bars + returns-only CSVs for all symbols in a portfolio.

    - If bars CSV doesn't exist, fetch lookback_days_if_missing of history.
    - If it exists, fetch from last_ts + 1 day to now + end_buffer_days.
    - Always rewrites returns-only CSV from bars CSV (fast enough).
    - Logs one audit row per symbol to logs/data_updates.csv
    """
    symbols = PORTFOLIOS[portfolio_name]

    now_utc = datetime.now(timezone.utc)
    end_utc = now_utc + timedelta(days=end_buffer_days)

    for sym in symbols:
        bars_path = DATA_DIR / f"{sym}_1Day.csv"
        returns_path = DATA_DIR / f"{sym}_1Day_returns_only.csv"

        had_file, last_ts = _read_existing_last_ts(bars_path)

        if last_ts is None:
            start_utc = now_utc - timedelta(days=lookback_days_if_missing)
        else:
            # start after the last saved day (daily bars)
            start_utc = last_ts + timedelta(days=1)

        audit = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": sym,
            "bars_file": str(bars_path),
            "had_existing_file": had_file,
            "last_ts_before": "" if last_ts is None else last_ts.isoformat(),
            "requested_start": start_utc.isoformat(),
            "requested_end": end_utc.isoformat(),
            "new_rows_fetched": 0,
            "rows_after_save": 0,
            "status": "started",
            "message": "",
        }

        try:
            new_bars = _fetch_daily_bars(sym, start_utc=start_utc, end_utc=end_utc)
            audit["new_rows_fetched"] = int(len(new_bars))

            new_added, total_after = _merge_save_bars(bars_path, new_bars)
            audit["rows_after_save"] = int(total_after)

            _write_returns_only(bars_path, returns_path)

            audit["status"] = "success"
            audit["message"] = f"added={new_added}, saved_total={total_after}"

        except Exception as e:
            audit["status"] = "error"
            audit["message"] = repr(e)

        _append_audit(audit)
