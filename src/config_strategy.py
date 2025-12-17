"""
Strategy configuration settings.

You can add new portfolios, thresholds, and parameters here without 
changing any strategy or modeling code.
"""

# --- Portfolios -------------------------------------------------------------

PORTFOLIOS = {
    "TIER1": ["DIA", "SPY", "XLF", "QQQ", "PG"],
    # You can add more named portfolios later, e.g.:
    # "INDEX_ETFS": ["SPY", "QQQ", "IWM", "DIA"],
    # "MEGACAPS": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
}

# Default portfolio the strategy should use
DEFAULT_PORTFOLIO = "TIER1"


# --- Forecast → Trading Signal Thresholds ----------------------------------

UP_THRESHOLD = 0.0008     # +0.08%
DOWN_THRESHOLD = -0.0008  # -0.08%


# --- Portfolio Exposure (for later, when you use weights) -------------------

LONG_EXPOSURE = 0.20      # +20% total long exposure
SHORT_EXPOSURE = -0.20    # -20% total short exposure
