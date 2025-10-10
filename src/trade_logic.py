from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class Signal:
    symbol: str
    action: str  # 'BUY' or 'HOLD'
    notional: float

class ToyStrategy:
    """A placeholder strategy:
    - If minute-of-hour is divisible by 15, signal BUY; else HOLD.
    Replace with real logic (SMA crossovers, momentum, etc.)
    """
    def __init__(self, symbol: str, default_notional: float = 1.0):
        self.symbol = symbol
        self.default_notional = default_notional

    def next(self) -> Signal:
        minute = int(time.strftime("%M"))
        if minute % 15 == 0:
            return Signal(symbol=self.symbol, action="BUY", notional=self.default_notional)
        return Signal(symbol=self.symbol, action="HOLD", notional=0.0)
