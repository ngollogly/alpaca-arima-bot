# src/modeling_arima.py

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA

def forecast_next_return(series: pd.Series, order=(1, 0, 1)) -> float:
    """
    Fit a simple ARIMA model with a fixed (p,d,q) order
    and return a 1-step-ahead forecast of returns.

    - Converts to a plain NumPy array (avoids pandas index quirks).
    - If fitting fails, returns 0.0 and prints the error.
    """
    # Clean series
    series = series.dropna().astype(float)

    # Require a decent history length
    if len(series) < 100:
        print(f"Series too short for ARIMA (len={len(series)}). Returning 0.0.")
        return 0.0

    # Convert to numpy array to avoid index-related issues
    y = np.asarray(series.values, dtype="float64")

    try:
        model = ARIMA(
            y,
            order=order,
            trend="n",                  # no constant for returns
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit = model.fit()

        forecast = fit.forecast(steps=1)[0]
        return float(forecast)

    except Exception as e:
        print(f"ARIMA failed for series length {len(y)} with order={order}: {repr(e)}")
        return 0.0
