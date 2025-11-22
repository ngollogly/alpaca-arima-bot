"""
src/config_symbols.py

Defines symbol universes (portfolios) used in the project.
You can import:
- SYMBOLS_ALL       → full universe
- SYMBOLS_ETF       → broad market / sector ETFs
- SYMBOLS_TECH      → large-cap tech
- SYMBOLS_DEFENSIVE → more stable/defensive names
- PORTFOLIOS        → dict of name → list of symbols
"""

# Broad index & sector ETFs
SYMBOLS_ETF = [
    "SPY",  # S&P 500
    "QQQ",  # Nasdaq-100
    "DIA",  # Dow Jones
    "IWM",  # Russell 2000
    "XLK",  # Tech sector
    "XLF",  # Financials
    "XLE",  # Energy
    "XLY",  # Consumer Discretionary
    "XLV",  # Health Care
]

# Large-cap tech / growth
SYMBOLS_TECH = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
]

# Defensive / consumer / staples
SYMBOLS_DEFENSIVE = [
    "PG",
    "KO",
    "MCD",
    "JNJ",
    "HD",
]

# Full universe (deduplicated)
SYMBOLS_ALL = sorted(set(SYMBOLS_ETF + SYMBOLS_TECH + SYMBOLS_DEFENSIVE))

# Named portfolios for convenience
PORTFOLIOS = {
    "all": SYMBOLS_ALL,
    "etf": SYMBOLS_ETF,
    "tech": SYMBOLS_TECH,
    "defensive": SYMBOLS_DEFENSIVE,
}
