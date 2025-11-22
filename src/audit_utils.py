# src/audit_utils.py
from pathlib import Path
from datetime import datetime
import pandas as pd

AUDIT_FILE = Path("reports/data_audit_log.csv")

def record_data_run(
    run_id: str,
    portfolio: str,
    symbols: list[str],
    n_success: int,
    n_failed: int,
    started_at: datetime,
    finished_at: datetime,
):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "run_id": run_id,
        "portfolio": portfolio,
        "symbols": ",".join(symbols),
        "n_symbols": len(symbols),
        "n_success": n_success,
        "n_failed": n_failed,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
    }

    if AUDIT_FILE.exists():
        df = pd.read_csv(AUDIT_FILE)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])

    df.to_csv(AUDIT_FILE, index=False)
    print(f"✅ Audit updated → {AUDIT_FILE}")
