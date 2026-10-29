from pathlib import Path
import numpy as np
import pandas as pd


def validate_ohlcv(frame):
    """Validate already-indexed bars without sorting or filling missing prices."""
    if len(frame) < 3 or not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError("Need at least three uniquely indexed bars in increasing order.")
    names = ["open", "high", "low", "close"]
    if not set(names).issubset(frame.columns):
        raise ValueError("Required columns: open, high, low, close.")
    out = frame.copy()
    for name in names:
        out[name] = pd.to_numeric(out[name], errors="raise")
    values = out[names].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Prices must be finite and strictly positive.")
    if ((out.high < out[["open", "close", "low"]].max(axis=1)) |
            (out.low > out[["open", "close", "high"]].min(axis=1))).any():
        raise ValueError("High / low must contain the open and close.")
    if "volume" in out:
        out["volume"] = pd.to_numeric(out["volume"], errors="raise")
        if not np.isfinite(out.volume.to_numpy()).all() or (out.volume < 0).any():
            raise ValueError("Recorded volumes must be finite and non-negative.")
    return out


def load_ohlcv(path, timestamp_unit=None):
    """CSV with timestamp, open, high, low, close and optional volume.

    Text timestamps are interpreted as UTC. Numeric timestamps require an
    explicit unit (s, ms, us or ns); no interval is inferred.
    """
    data = pd.read_csv(Path(path))
    data.columns = [str(x).strip().lower() for x in data.columns]
    if data.columns.has_duplicates or "timestamp" not in data:
        raise ValueError("Use unique column names and a timestamp column.")
    ts = data.pop("timestamp")
    if pd.api.types.is_numeric_dtype(ts):
        if timestamp_unit not in {"s", "ms", "us", "ns"}:
            raise ValueError("Numeric timestamps require --timestamp-unit.")
        index = pd.to_datetime(ts, unit=timestamp_unit, utc=True, errors="raise")
    else:
        index = pd.to_datetime(ts, utc=True, errors="raise")
    if index.isna().any():
        raise ValueError("Timestamps cannot be missing.")
    data.index = pd.DatetimeIndex(index, name="timestamp")
    return validate_ohlcv(data)


def load_prosperity_midpoints(path, product):
    """Adapter for original semicolon-separated Prosperity price snapshots.

    The observation index is ordinal, NOT a calendar timestamp. All OHLC
    fields are the same midpoint proxy. This cannot model fills or queues.
    """
    data = pd.read_csv(path, sep=";")
    required = {"day", "timestamp", "product", "mid_price"}
    if not required.issubset(data):
        raise ValueError("Expected a Prosperity price file with day, timestamp, product, mid_price.")
    data = data.loc[data["product"] == product].copy()
    if len(data) < 3 or data[["day", "timestamp"]].duplicated().any():
        raise ValueError("Select a product with at least three unique observations.")
    if data[["day", "timestamp"]].isna().any().any():
        raise ValueError("Missing day or event timestamp.")
    pairs = list(zip(data.day, data.timestamp))
    if pairs != sorted(pairs):
        raise ValueError("Competition observations must be in day/timestamp order.")
    out = pd.DataFrame({name: pd.to_numeric(data.mid_price, errors="raise").to_numpy()
                        for name in ("open", "high", "low", "close")})
    out["day"] = data.day.to_numpy()
    out["event_timestamp"] = data.timestamp.to_numpy()
    out.index.name = "observation"
    out = validate_ohlcv(out)
    out.attrs["source_kind"] = "competition_midpoint_proxy"
    return out
