from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.common.exceptions import APIError
from typing import Optional

from .config import settings


class AlpacaWrapper:
    def __init__(self):
        # If settings.env == "live", we go live; otherwise paper
        self.client = TradingClient(
            api_key=settings.api_key,
            secret_key=settings.api_secret,
            paper=(settings.env != "live"),
        )

    def account(self):
        return self.client.get_account()

    def is_trading_blocked(self) -> bool:
        acc = self.account()
        return bool(acc.trading_blocked)

    def submit_market_order(self, symbol: str, side: str, notional_usd: float):
        """
        side: 'buy' or 'sell'
        notional_usd: dollar value to trade
        """
        side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

        req = MarketOrderRequest(
            symbol=symbol,
            notional=notional_usd,
            side=side_enum,
            time_in_force=TimeInForce.DAY,
        )
        return self.client.submit_order(order_data=req)
