import argparse, sys, csv, os
from datetime import datetime
from .config import settings
from .logger import get_logger
from .alpaca_client import AlpacaWrapper
from .trade_logic import ToyStrategy

LOG_FIELDS = ["ts", "symbol", "action", "notional", "order_id", "status", "message"]

def write_trade_log(row: dict, path: str = "logs/trades.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if not file_exists:
            w.writeheader()
        w.writerow(row)

def smoke_check(logger):
    try:
        alp = AlpacaWrapper()
        acc = alp.account()
        logger.info(f"Connected. Account status={acc.status}, equity={acc.equity}, cash={acc.cash}")
        if alp.is_trading_blocked():
            logger.warning("Trading is currently blocked on this account.")
        return True
    except Exception as e:
        logger.exception("Smoke check failed: %s", e)
        return False

def run_test(symbol: str, allow_trade: bool, notional: float, logger):
    strat = ToyStrategy(symbol=symbol, default_notional=notional or settings.default_notional)
    signal = strat.next()
    logger.info(f"Strategy signal: {signal}")
    order_id = ""
    status = "NOOP"
    message = ""

    if signal.action == "BUY" and allow_trade:
        try:
            alp = AlpacaWrapper()
            o = alp.submit_market_buy(signal.symbol, signal.notional)
            order_id = getattr(o, "id", "")
            status = getattr(o, "status", "submitted")
            message = "order submitted"
            logger.info(f"Submitted BUY {signal.symbol} notional={signal.notional} order_id={order_id}")
        except Exception as e:
            status = "ERROR"
            message = str(e)
            logger.exception("Order submission failed")

    elif signal.action == "BUY" and not allow_trade:
        message = "Dry run: trade suppressed (use --allow-trade to enable)"
        logger.info(message)
    else:
        message = "No trade signal"
        logger.info(message)

    write_trade_log({
        "ts": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "action": signal.action,
        "notional": signal.notional,
        "order_id": order_id,
        "status": status,
        "message": message
    })

def main():
    parser = argparse.ArgumentParser(description="Alpaca bot starter")
    parser.add_argument("--check", action="store_true", help="Smoke test (no orders)")
    parser.add_argument("--test-symbol", default="AAPL", help="Symbol for test runs")
    parser.add_argument("--allow-trade", action="store_true", help="Actually place a small paper trade if signaled")
    parser.add_argument("--notional", type=float, default=0.0, help="USD notional for test trade (default from settings)")
    args = parser.parse_args()

    logger = get_logger("bot", settings.log_dir)

    if args.check:
        ok = smoke_check(logger)
        sys.exit(0 if ok else 1)

    run_test(symbol=args.test_symbol, allow_trade=args.allow_trade, notional=args.notional, logger=logger)

if __name__ == "__main__":
    main()
