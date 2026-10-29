import numpy as np
import pandas as pd


def fit_ridge(x, y, penalty=1.0):
    """Fit the scaler and ridge coefficients using ONLY the supplied training rows."""
    if not np.isfinite(penalty) or penalty <= 0:
        raise ValueError("A finite positive ridge penalty is required.")
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if x.ndim != 2 or len(x) != len(y) or len(x) < x.shape[1] + 2:
        raise ValueError("Not enough aligned training rows.")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Training values must be finite.")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale = np.where(scale > 0, scale, 1.0)
    z = (x - mean) / scale
    intercept = float(y.mean())
    coef = np.linalg.solve(z.T @ z + penalty * np.eye(z.shape[1]), z.T @ (y-intercept))
    return {"mean":mean, "scale":scale, "coef":coef, "intercept":intercept}


def predict_ridge(model, x):
    x = np.asarray(x, dtype=float)
    return model["intercept"] + ((x-model["mean"])/model["scale"]) @ model["coef"]


def walk_forward_ridge(features, target, initial_train=150, test_size=100, gap=2, penalty=1.0):
    """Expanding-window, out-of-sample forecasts.

    For a close-t feature predicting open[t+2]/open[t+1]-1, keep gap >= 2:
    training labels then finish strictly before each test block begins.
    Predictions are made only on finite test feature rows. No score tuning.
    """
    if not features.index.equals(target.index):
        raise ValueError("Features and target must have the same ordered index.")
    if initial_train < 10 or test_size < 1 or gap < 2:
        raise ValueError("Require initial_train >= 10, test_size >= 1, gap >= 2.")
    output = pd.Series(np.nan, index=features.index, name="forecast")
    x, y = features.to_numpy(dtype=float), target.to_numpy(dtype=float)
    for start in range(initial_train, len(features), test_size):
        stop = start-gap
        mask = np.isfinite(x[:stop]).all(axis=1) & np.isfinite(y[:stop])
        if mask.sum() < x.shape[1]+2:
            continue
        model = fit_ridge(x[:stop][mask], y[:stop][mask], penalty=penalty)
        end = min(start+test_size, len(features))
        valid = np.isfinite(x[start:end]).all(axis=1)
        positions = np.arange(start,end)[valid]
        output.iloc[positions] = predict_ridge(model, x[positions])
    return output
