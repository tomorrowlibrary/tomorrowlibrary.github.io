import numpy as np
import pandas as pd
from .data import validate_ohlcv


def run_backtest(bars, targets, initial_capital=10000.0, fee_bps=5.0, slippage_bps=1.0):
    """Single asset, fractional shares, no leverage beyond |target| <= 1.

    A target computed at close t can trade only at open t+1. Cash earns zero.
    Slippage is adverse on each order; fees apply to executed notional.
    Targets are fractions of equity AFTER trading costs, solved explicitly.
    Every run closes its remaining position at the final close.
    Short borrowing, funding, queues, market impact, lots and taxes are absent.
    """
    bars = validate_ohlcv(bars)
    targets = pd.Series(targets,dtype=float)
    if not targets.index.equals(bars.index) or not np.isfinite(targets).all() or (targets.abs()>1).any():
        raise ValueError("Supply aligned finite target weights in [-1,1].")
    if not all(np.isfinite(v) for v in [initial_capital,fee_bps,slippage_bps]) or initial_capital<=0 or fee_bps<0 or slippage_bps<0 or fee_bps+slippage_bps>=10000:
        raise ValueError("Capital must be positive and costs finite, non-negative and below 100%.")
    fee,slip = fee_bps/10000,slippage_bps/10000
    cash,shares = float(initial_capital),0.0
    records,trades = [],[]

    def execute(new_shares, price, time, reason):
        nonlocal cash,shares
        delta = new_shares-shares
        if abs(delta)<1e-12:
            return 0.0
        direction = float(np.sign(delta))
        fill = price*(1+slip*direction)
        commission = abs(delta)*fill*fee
        cash -= delta*fill + commission
        shares = new_shares
        cost = abs(delta)*price*slip+commission
        trades.append({"time":str(time),"quantity":delta,"reference_price":price,"fill_price":fill,"fee":commission,"total_cost":cost,"reason":reason})
        return cost

    for i,(time,row) in enumerate(bars.iterrows()):
        price = float(row["open"])
        pre_equity = cash+shares*price
        if pre_equity<=0:
            raise ValueError("Account became insolvent; stop rather than silently continuing.")
        weight = float(targets.iloc[i-1]) if i else 0.0
        direction = float(np.sign(weight*pre_equity/price-shares))
        k = slip+fee*(1+slip*direction)
        new_shares = weight*(pre_equity/price+direction*k*shares)/(1+weight*direction*k)
        cost = execute(new_shares,price,time,"next_open")
        if i==len(bars)-1:
            cost += execute(0.0,float(row["close"]),time,"final_close")
        equity = cash+shares*float(row["close"])
        if equity<=0:
            raise ValueError("Account became insolvent during a bar.")
        records.append({"equity":equity,"cash":cash,"shares":shares,"target":weight,"cost":cost})
    result = pd.DataFrame(records,index=bars.index)
    ledger = pd.DataFrame(trades,columns=["time","quantity","reference_price","fill_price","fee","total_cost","reason"])
    return result,ledger
