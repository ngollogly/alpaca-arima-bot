def save_returns_only(
    in_csv: str,
    out_csv: str | None = None,
    ts_col: str = "ts",
    price_col: str = "close",
):
    """
    Reads a CSV with price data, computes simple percent returns, and saves a
    'returns-only' CSV with columns [timestamp, return].

    Parameters
    ----------
    in_csv : str
        Path to input CSV (must contain timestamp and price columns).
    out_csv : str or None, optional
        Output file path. If None, creates one based on input name.
    ts_col : str, default 'ts'
        Column name representing timestamps.
    price_col : str, default 'close'
        Column name used to compute percent change.

    Example
    -------
    save_returns_only('data/SPY_1Day.csv')
    save_returns_only('data/AAPL_1Day.csv', ts_col='date', price_col='adj_close')
    """
    import pandas as pd
    from pathlib import Path

    in_path = Path(in_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Input file not found: {in_csv}")

    # Derive output filename if not provided
    if out_csv is None:
        stem = in_path.stem  # e.g., "SPY_1Day"
        out_csv = in_path.parent / f"{stem}_returns_only.csv"

    df = pd.read_csv(in_path, parse_dates=[ts_col])
    df = df.sort_values(ts_col).reset_index(drop=True)

    if price_col not in df.columns:
        raise ValueError(f"'{price_col}' column not found in {in_csv}")

    df["return"] = df[price_col].pct_change()
    df = df.dropna(subset=["return"])[[ts_col, "return"]]

    df.to_csv(out_csv, index=False)
    print(f"✅ Saved {len(df)} rows → {out_csv}")
