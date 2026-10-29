import numpy as np
import pandas as pd


def historical_tail(returns, confidence=0.95):
    """VaR and ES on losses=-returns. Positive is a loss; negative is a gain."""
    x = np.asarray(returns, dtype=float)
    if len(x) == 0 or not np.isfinite(x).all() or not 0 < confidence < 1:
        raise ValueError("Supply finite returns and confidence in (0,1).")
    losses = -x
    var = float(np.quantile(losses, confidence))
    return {"var":var, "expected_shortfall":float(losses[losses >= var].mean())}


def return_summary(equity, initial_capital, periods_per_year):
    values = np.asarray(equity, dtype=float)
    if not len(values) or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Need positive finite equity.")
    if initial_capital <= 0 or not np.isfinite(initial_capital) or periods_per_year <= 0 or not np.isfinite(periods_per_year):
        raise ValueError("Specify positive initial capital and annualisation.")
    path = np.r_[initial_capital,values]
    ret = path[1:]/path[:-1]-1
    drawdown = path/np.maximum.accumulate(path)-1
    std = float(np.std(ret,ddof=1)) if len(ret)>1 else 0.0
    return {
        "total_return":float(values[-1]/initial_capital-1),
        "max_drawdown":float(-drawdown.min()),
        "annualised_volatility":float(std*np.sqrt(periods_per_year)),
        "sharpe_zero_cash_rate":float(ret.mean()/std*np.sqrt(periods_per_year)) if std>1e-15 else None,
        "periods":len(ret),
        **historical_tail(ret),
    }
