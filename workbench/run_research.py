import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from qtlib.data import load_ohlcv,load_prosperity_midpoints
from qtlib.features import trailing_features
from qtlib.models import walk_forward_ridge
from qtlib.backtest import run_backtest
from qtlib.risk import return_summary


def main():
    parser=argparse.ArgumentParser(description="Educational CSV-to-features-to-backtest workflow.")
    parser.add_argument("--csv",required=True,type=Path)
    parser.add_argument("--schema",choices=["ohlcv","prosperity"],default="ohlcv")
    parser.add_argument("--product",help="Product for Prosperity midpoint files.")
    parser.add_argument("--timestamp-unit",choices=["s","ms","us","ns"])
    parser.add_argument("--strategy",choices=["momentum","ridge"],default="momentum")
    parser.add_argument("--annualisation",type=float,required=True,help="Observations per year; use 1 for noncalendar competition proxies.")
    parser.add_argument("--fee-bps",type=float,default=5)
    parser.add_argument("--slippage-bps",type=float,default=1)
    parser.add_argument("--out",type=Path,default=Path("results/run"))
    args=parser.parse_args()
    if args.schema=="prosperity" and not args.product:
        parser.error("--schema prosperity requires --product.")
    bars=load_prosperity_midpoints(args.csv,args.product) if args.schema=="prosperity" else load_ohlcv(args.csv,args.timestamp_unit)
    if len(bars)<200:
        raise ValueError("Use at least 200 observations for this example workflow.")
    features=trailing_features(bars)
    target=bars.open.shift(-2)/bars.open.shift(-1)-1
    forecasts=walk_forward_ridge(features,target)
    # Both comparisons use the same out-of-sample evaluation window.
    start=150
    predictions=forecasts.iloc[start:].dropna()
    metrics={"ridge_mse":float(((predictions-target.reindex(predictions.index)).dropna()**2).mean()),
             "zero_forecast_mse":float((target.reindex(predictions.index).dropna()**2).mean())}
    if args.strategy=="ridge":
        if predictions.empty: raise ValueError("No valid out-of-sample predictions.")
        decisions=np.sign(forecasts).fillna(0)
    else:
        fast=bars.close.rolling(10,min_periods=10).mean()
        slow=bars.close.rolling(40,min_periods=40).mean()
        decisions=pd.Series(np.where(fast>slow,1.0,0.0),index=bars.index)
    # Begin evaluation flat. First evaluation decision is executed one open later.
    evaluation=bars.iloc[start:].copy()
    results,ledger=run_backtest(evaluation,decisions.iloc[start:],fee_bps=args.fee_bps,slippage_bps=args.slippage_bps)
    args.out.mkdir(parents=True,exist_ok=True)
    features.to_csv(args.out/"features.csv")
    forecasts.to_csv(args.out/"forecasts.csv")
    results.to_csv(args.out/"equity.csv")
    ledger.to_csv(args.out/"trades.csv",index=False)
    report={"strategy":args.strategy,"data_sha256":hashlib.sha256(args.csv.read_bytes()).hexdigest(),
            "schema":args.schema,"product":args.product,"annualisation":args.annualisation,
            "fee_bps":args.fee_bps,"slippage_bps":args.slippage_bps,
            "start_flat_at_observation":start,"forecasts":metrics,
            "performance":return_summary(results.equity,10000,args.annualisation),
            "trade_count":len(ledger),"total_cost":float(results.cost.sum()),
            "execution":"Close t decision -> next open; final close liquidation",
            "limitations":"Educational account model; no queues, impact, funding or borrow. Competition midpoints are a price proxy, not executable prices."}
    (args.out/"report.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps(report,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
