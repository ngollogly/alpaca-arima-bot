# Alpaca Bot Starter

A minimal, production-minded scaffold to connect to Alpaca (paper), log activity, and prepare for strategy iterations.

## Quickstart

1) Create and activate a virtual env:
```bash
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

2) Install dependencies:
```bash
pip install -r requirements.txt
```

3) Add your keys to `.env` (copy `.env.example`):
```bash
cp .env.example .env
# then edit .env with your actual keys
```

4) Smoke test the connection (no orders placed):
```bash
python src/main.py --check
```

5) Run a safe paper-trade test (places a **$1 notional** market BUY if market is open and you pass --allow-trade):
```bash
python src/main.py --test-symbol AAPL --allow-trade
```

> By default `main.py` runs **DRY-RUN** unless `--allow-trade` is set. Keep it off until you're ready.

## Project structure

```
alpaca-bot-starter/
├─ src/
│  ├─ config.py           # loads env, global settings
│  ├─ logger.py           # structured logger
│  ├─ alpaca_client.py    # thin client wrapper
│  ├─ trade_logic.py      # placeholder strategy
│  └─ main.py             # CLI entry
├─ data/                  # input data, cached quotes
├─ logs/                  # runtime & trade logs
├─ reports/               # csv performance reports, figures
├─ notebooks/             # experiments
├─ requirements.txt
├─ .env.example
└─ README.md
```

## Next steps

- Add position sizing, stop-loss & diversification in `trade_logic.py`
- Wire in trade/performance logging (already scaffolded)
- Build a simple Streamlit or matplotlib report in `reports/`
