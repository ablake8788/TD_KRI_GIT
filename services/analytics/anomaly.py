############
####  anomaly.py

import numpy as np
import pandas as pd
from typing import Tuple

def zscore(series: pd.Series, window: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
    mean = series.rolling(window=window, min_periods=max(10, window // 3)).mean()
    std  = series.rolling(window=window, min_periods=max(10, window // 3)).std(ddof=0)
    z = (series - mean) / std.replace(0, np.nan)
    return z, mean, std

def ewma(series: pd.Series, lam: float) -> pd.Series:
    return series.ewm(alpha=lam, adjust=False).mean()

def control_limits(ewma_series: pd.Series, baseline_std: pd.Series, k: float) -> Tuple[pd.Series, pd.Series]:
    ucl = ewma_series + k * baseline_std
    lcl = ewma_series - k * baseline_std
    return ucl, lcl

def anomaly_flag(series: pd.Series, z: pd.Series, ucl: pd.Series, z_threshold: float, use_ucl: bool) -> pd.Series:
    flag = (z.abs() >= z_threshold)
    if use_ucl:
        flag = flag | (series > ucl)
    return flag.fillna(False).astype(bool)
