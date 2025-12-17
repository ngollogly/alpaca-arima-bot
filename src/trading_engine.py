# src/trading_engine.py

from pathlib import Path
from datetime import datetime
import csv
from typing import List, Dict

import pandas as pd
from alpaca.common.exceptions import APIError

from .alpaca_client import AlpacaWrapper
from .config_strategy import LONG_EXPOSURE, SHORT_EXPOSURE


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
TRADES_LOG = LOG_DIR / "trades.csv"


def compute_test_orders(signals_df: pd.DataFrame, notional_usd: float = 1.0) -> List[Dict]:
    """
    For now:
    - 'long'  → BUY $notional
    - 'short' → NO ORDER (skipped; fractional shorts not allowed)
    - 'flat'  → NO ORDER
    """
    orders = []

    for _, row in signals_df.iterrows():
        sym = row["symbol"]
        signal = row["signal"]
        forecast = float(row["forecast_return"])

        if signal == "flat":
            continue

        if signal == "short":
            # Just log that we'd *like* to short, but skip placing an order for now
            print(f"Skipping SHORT signal for {sym} (forecast={forecast:.6f}) – shorting fractional notional not supported.")
            continue

        # If we got here, signal == "long"
        orders.append(
            {
                "symbol": sym,
                "side": "buy",
                "notional": float(notional_usd),
                "signal": signal,
                "forecast_return": forecast,
            }
        )

    return orders


def append_trades_log(records: List[Dict], status: str, error: str = ""):
    """
    Append execution attempts to logs/trades.csv
    One row per attempted order.
    """
    if not records:
        return

    file_exists = TRADES_LOG.exists()

    with TRADES_LOG.open("a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "symbol",
                "side",
                "notional",
                "signal",
                "forecast_return",
                "status",
                "error",
                "order_id",
            ],
        )
        if not file_exists:
            writer.writeheader()

        ts = datetime.utcnow().isoformat()

        for rec in records:
            writer.writerow(
                {
                    "timestamp": ts,
                    "symbol": rec["symbol"],
                    "side": rec["side"],
                    "notional": rec["notional"],
                    "signal": rec["signal"],
                    "forecast_return": rec["forecast_return"],
                    "status": status,
                    "error": error,
                    "order_id": rec.get("order_id", ""),
                }
            )


def execute_test_trades(signals_df: pd.DataFrame, notional_usd: float = 1.0):
    """
    End-to-end:
    - build tiny $1 test orders from ARIMA signals
    - send them to Alpaca paper trading
    - log results to logs/trades.csv
    """
    alpaca = AlpacaWrapper()

    if alpaca.is_trading_blocked():
        print("❌ Trading is blocked on this account.")
        return

    orders = compute_test_orders(signals_df, notional_usd=notional_usd)

    if not orders:
        print("No trades to place (all signals flat).")
        return

    success_records = []
    error_records = []

    for o in orders:
        print(
            f"Placing {o['side'].upper()} ${o['notional']} in {o['symbol']} "
            f"(signal={o['signal']}, forecast={o['forecast_return']:.6f})"
        )
        try:
            resp = alpaca.submit_market_order(
                symbol=o["symbol"],
                side=o["side"],
                notional_usd=o["notional"],
            )
            o["order_id"] = getattr(resp, "id", "")
            success_records.append(o)

        except APIError as e:
            print(f"  ❌ APIError for {o['symbol']}: {e}")
            o["order_id"] = ""
            error_records.append(o)
        except Exception as e:
            print(f"  ❌ Unexpected error for {o['symbol']}: {e}")
            o["order_id"] = ""
            error_records.append(o)

    # Log successes and errors
    if success_records:
        append_trades_log(success_records, status="success", error="")
    if error_records:
        append_trades_log(error_records, status="error", error="see console")

    print(f"✅ Done. Success: {len(success_records)}, Errors: {len(error_records)}")
    print(f"Trades logged to: {TRADES_LOG}")
