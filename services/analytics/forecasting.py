###
#######   forecasting.py

import pandas as pd
from typing import Tuple

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except Exception:
    ExponentialSmoothing = None

try:
    from statsmodels.tsa.arima.model import ARIMA
except Exception:
    ARIMA = None


def forecast(
    dates: pd.DatetimeIndex,
    values: pd.Series,
    horizon_days: int,
    prefer_ets: bool,
    prefer_arima: bool,
    arima_order: Tuple[int, int, int],
) -> pd.DataFrame:
    if len(values.dropna()) < 20:
        return pd.DataFrame(columns=["forecast_date", "forecast_value", "model_name"])

    df = pd.DataFrame({"ds": dates, "y": values}).dropna().set_index("ds").asfreq("D")
    df["y"] = df["y"].interpolate(limit_direction="both")
    y = df["y"]

    rows = []

    if prefer_ets and ExponentialSmoothing is not None:
        try:
            fit = ExponentialSmoothing(y, trend="add", seasonal=None, initialization_method="estimated").fit(optimized=True)
            fc = fit.forecast(horizon_days)
            for d, v in fc.items():
                rows.append({"forecast_date": d.date(), "forecast_value": float(v), "model_name": "ETS"})
        except Exception:
            pass

    if prefer_arima and ARIMA is not None:
        try:
            fit = ARIMA(y, order=arima_order).fit()
            fc = fit.forecast(steps=horizon_days)
            fc.index = pd.date_range(start=y.index[-1] + pd.Timedelta(days=1), periods=horizon_days, freq="D")
            for d, v in fc.items():
                rows.append({"forecast_date": d.date(), "forecast_value": float(v), "model_name": f"ARIMA{arima_order}"})
        except Exception:
            pass

    return pd.DataFrame(rows)

