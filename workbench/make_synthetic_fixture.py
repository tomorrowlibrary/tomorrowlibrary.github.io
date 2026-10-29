"""Create deterministic SYNTHETIC OHLCV for installation and accounting checks."""
from pathlib import Path
import numpy as np
import pandas as pd

if __name__=="__main__":
    rng=np.random.default_rng(20261029)
    n=800
    close=100*np.exp(np.cumsum(rng.normal(0,0.006,n)))
    opening=np.r_[100,close[:-1]]*np.exp(rng.normal(0,0.001,n))
    data=pd.DataFrame({"timestamp":pd.date_range("2020-01-01",periods=n,freq="D",tz="UTC"),
                       "open":opening,"high":np.maximum(opening,close)*1.003,
                       "low":np.minimum(opening,close)*0.997,"close":close,
                       "volume":rng.integers(100,1000,n)})
    Path("data").mkdir(exist_ok=True)
    data.to_csv("data/SYNTHETIC-fixture.csv",index=False)
    print("Created data/SYNTHETIC-fixture.csv — simulated values, not historical market data.")
