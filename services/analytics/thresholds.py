#####
## thresholds.py

import pandas as pd
from typing import Tuple

def percentile_thresholds(series: pd.Series, window: int, p_amber: float, p_red: float) -> Tuple[pd.Series, pd.Series]:
    amber = series.rolling(window=window, min_periods=max(10, window // 3)).quantile(p_amber)
    red   = series.rolling(window=window, min_periods=max(10, window // 3)).quantile(p_red)
    return amber, red
