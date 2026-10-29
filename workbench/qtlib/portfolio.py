import numpy as np
import pandas as pd


def constrained_weights(weights, max_asset_weight=1.0):
    """Long-only targets. Unallocated weight remains in cash; no redistribution."""
    weights = pd.Series(weights, dtype=float)
    if weights.empty or weights.index.has_duplicates or not np.isfinite(weights).all():
        raise ValueError("Need finite, uniquely named asset weights.")
    if not 0 < max_asset_weight <= 1 or (weights < 0).any() or weights.sum() > 1+1e-12:
        raise ValueError("Long-only weights must sum to at most one; cap is in (0,1].")
    return weights.clip(upper=max_asset_weight)


def equal_weights(assets, max_asset_weight=1.0):
    assets = list(assets)
    if not assets or len(set(assets)) != len(assets):
        raise ValueError("Supply unique asset names.")
    return constrained_weights(pd.Series(1/len(assets), index=assets), max_asset_weight)


def inverse_volatility_weights(training_returns, max_asset_weight=1.0):
    """Estimate from a supplied historical window; caller controls its cutoff."""
    if len(training_returns) < 2 or not np.isfinite(training_returns.to_numpy()).all():
        raise ValueError("Need at least two complete finite training observations.")
    vol = training_returns.std(ddof=1)
    if (vol <= 0).any() or not np.isfinite(vol).all():
        raise ValueError("Each asset needs positive finite volatility.")
    raw = 1/vol
    return constrained_weights(raw/raw.sum(), max_asset_weight)


def lagged_portfolio_returns(asset_returns, decision_weights):
    """Weights decided at t apply to returns ending at t+1. Cash returns zero.

    This helper omits turnover costs. Use it for inspecting weights, not as a
    substitute for execution or a portfolio account simulator.
    """
    if not asset_returns.index.equals(decision_weights.index) or not asset_returns.columns.equals(decision_weights.columns):
        raise ValueError("Returns and weights must have exactly matching axes.")
    if not np.isfinite(decision_weights.to_numpy()).all() or (decision_weights < 0).any().any() or (decision_weights.sum(axis=1)>1+1e-12).any():
        raise ValueError("Need finite long-only decisions summing to at most one.")
    held = decision_weights.shift(1).fillna(0)
    if ((~np.isfinite(asset_returns)) & (held != 0)).any().any():
        raise ValueError("Missing return for an invested asset.")
    return (held*asset_returns.fillna(0)).sum(axis=1)
