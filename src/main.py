import argparse
import sys

from .config import settings
from .logger import get_logger
from .alpaca_client import AlpacaWrapper
from .generate_signals import build_signals_df
from .trading_engine import execute_test_trades
from .config_strategy import DEFAULT_PORTFOLIO
from .update_data import update_portfolio_data


def smoke_check(logger):
    """
    Simple connectivity test to Alpaca:
    - gets account info
    - logs status, equity, cash
    - warns if trading is blocked
    """
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


def run_strategy(portfolio: str, allow_trade: bool, notional: float, no_update: bool, update_only: bool, logger):

    """
    End-to-end:
    - build ARIMA-based signals for a portfolio
    - print signals table
    - optionally place tiny paper trades
    """
    if not no_update:
        logger.info(f"Updating market data for portfolio='{portfolio}'...")
        update_portfolio_data(portfolio_name=portfolio)
    else:
        logger.info("Skipping data update (--no-update). Using existing CSVs.")

    if update_only:
        logger.info("Update-only mode (--update-only). Exiting after data update.")
        return

    logger.info(f"Building signals for portfolio='{portfolio}'")
    signals_df = build_signals_df(portfolio_name=portfolio)

    print("=== Signals ===")
    print(signals_df)

    if not allow_trade:
        logger.info("Dry run: NOT placing trades (use --allow-trade to enable).")
        return

    # If notional is 0 or negative, fall back to a small default (e.g., $1)
    trade_notional = notional if notional > 0 else 1.0
    logger.info(f"Placing paper trades at notional=${trade_notional:.2f} per symbol.")
    execute_test_trades(signals_df, notional_usd=trade_notional)


def main():
    parser = argparse.ArgumentParser(description="ARIMA-based Alpaca bot")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Smoke test Alpaca connection (no orders).",
    )
    parser.add_argument(
        "--portfolio",
        default=DEFAULT_PORTFOLIO,
        help=f"Portfolio name to use (default: {DEFAULT_PORTFOLIO}).",
    )
    parser.add_argument(
        "--allow-trade",
        action="store_true",
        help="Actually place small paper trades based on signals.",
    )
    parser.add_argument(
        "--notional",
        type=float,
        default=0.0,
        help="USD notional per trade (default: $1 if not specified).",
    )
    parser.add_argument(
        "--no-update", 
        action="store_true", 
        help="Skip data update step.",
    )
    parser.add_argument(
        "--update-only", 
        action="store_true", 
        help="Only update data then exit.",
    )

    args = parser.parse_args()

    logger = get_logger("bot", settings.log_dir)

    if args.check:
        ok = smoke_check(logger)
        sys.exit(0 if ok else 1)

    run_strategy(
        portfolio=args.portfolio,
        allow_trade=args.allow_trade,
        notional=args.notional,
        no_update=args.no_update,
        update_only=args.update_only,
        logger=logger,
    )



if __name__ == "__main__":
    main()
