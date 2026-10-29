import numpy as np
import pandas as pd


def trailing_features(bars, window=20):
    """Information available at close t. No centred windows or future fills."""
    if not isinstance(window, int) or window < 2:
        raise ValueError("window must be an integer >= 2.")
    close = bars["close"].astype(float)
    ret = close.pct_change(fill_method=None)
    mean = close.rolling(window, min_periods=window).mean()
    std = close.rolling(window, min_periods=window).std(ddof=1)
    result = pd.DataFrame({
        "return_1": ret,
        "return_window": close.pct_change(window, fill_method=None),
        "volatility": ret.rolling(window, min_periods=window).std(ddof=1),
        "displacement_z": (close - mean) / std.replace(0, np.nan),
    }, index=bars.index)
    return result.replace([np.inf, -np.inf], np.nan)
