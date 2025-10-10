from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.common.exceptions import APIError
from .config import settings

class AlpacaWrapper:
    def __init__(self):
        self.client = TradingClient(
            api_key=settings.api_key,
            secret_key=settings.api_secret,
            paper=(settings.env != "live")
        )

    def account(self):
        return self.client.get_account()

    def is_trading_blocked(self) -> bool:
        acc = self.account()
        return bool(acc.trading_blocked)

    def submit_market_buy(self, symbol: str, notional_usd: float):
        req = MarketOrderRequest(
            symbol=symbol,
            notional=notional_usd,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        return self.client.submit_order(order_data=req)
