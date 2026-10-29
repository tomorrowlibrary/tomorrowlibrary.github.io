import unittest
import numpy as np
import pandas as pd
from qtlib.data import validate_ohlcv
from qtlib.features import trailing_features
from qtlib.models import walk_forward_ridge
from qtlib.portfolio import equal_weights,constrained_weights,lagged_portfolio_returns
from qtlib.risk import historical_tail,return_summary
from qtlib.backtest import run_backtest


def bars(prices):
    values=np.asarray(prices,dtype=float)
    return pd.DataFrame({c:values for c in ["open","high","low","close"]})


class ResearchTests(unittest.TestCase):
    def test_signal_cannot_capture_same_bar_move(self):
        data=bars([100,100,150,150])
        result,trades=run_backtest(data,pd.Series([0,0,1,0]),fee_bps=0,slippage_bps=0)
        self.assertAlmostEqual(result.equity.iloc[-1],10000)
        self.assertEqual(trades.iloc[0]["time"],"3")

    def test_cash_and_exit_accounting(self):
        result,trades=run_backtest(bars([100,100,110]),pd.Series([1,1,0]),fee_bps=0,slippage_bps=0)
        self.assertAlmostEqual(result.equity.iloc[-1],11000)
        self.assertEqual(result.shares.iloc[-1],0)
        self.assertAlmostEqual(result.cash.iloc[-1],11000)
        self.assertAlmostEqual(trades.quantity.sum(),0)

    def test_costs_and_target_equity_constraint(self):
        result,trades=run_backtest(bars([100,100,100]),pd.Series([1,1,1]),fee_bps=10,slippage_bps=10)
        self.assertGreater(trades.total_cost.sum(),0)
        self.assertAlmostEqual(result.equity.iloc[-1],10000-trades.total_cost.sum())
        self.assertGreaterEqual(result.cash.min(),-1e-8)
        self.assertAlmostEqual(result.shares.iloc[1]*100/result.equity.iloc[1],1)

    def test_short_loses_on_rally(self):
        result,_=run_backtest(bars([100,100,110]),pd.Series([-1,-1,0]),fee_bps=0,slippage_bps=0)
        self.assertAlmostEqual(result.equity.iloc[-1],9000)

    def test_features_do_not_depend_on_future(self):
        data=bars(100+np.sin(np.arange(300)/5)+np.arange(300)*.01)
        changed=data.copy()
        changed.loc[201:,["open","high","low","close"]]*=2
        pd.testing.assert_frame_equal(trailing_features(data).iloc[:201],trailing_features(changed).iloc[:201])

    def test_model_predictions_do_not_depend_on_future(self):
        rng=np.random.default_rng(3)
        x=pd.DataFrame(rng.normal(size=(400,3)))
        y=pd.Series(rng.normal(size=400))
        original=walk_forward_ridge(x,y,initial_train=100,test_size=50)
        x2=x.copy();y2=y.copy()
        x2.iloc[201:]*=200;y2.iloc[201:]+=900
        pd.testing.assert_series_equal(original.iloc[:201],walk_forward_ridge(x2,y2,initial_train=100,test_size=50).iloc[:201])

    def test_training_label_gap(self):
        x=pd.DataFrame(np.arange(400).reshape(200,2),dtype=float)
        y=pd.Series(np.linspace(0,1,200))
        original=walk_forward_ridge(x,y,initial_train=100,test_size=20,gap=2)
        y.iloc[98:120]=100000
        changed=walk_forward_ridge(x,y,initial_train=100,test_size=20,gap=2)
        pd.testing.assert_series_equal(original.iloc[100:120],changed.iloc[100:120])

    def test_risk_includes_initial_capital(self):
        report=return_summary([90,80],100,252)
        self.assertAlmostEqual(report["max_drawdown"],.2)
        self.assertAlmostEqual(report["total_return"],-.2)
        tail=historical_tail([-.1,-.2,.1],confidence=.8)
        self.assertAlmostEqual(tail["expected_shortfall"],.2)

    def test_portfolio_weights_and_lag(self):
        self.assertAlmostEqual(equal_weights(["A","B"]).sum(),1)
        self.assertAlmostEqual(constrained_weights({"A":.8,"B":.2},.4).sum(),.6)
        returns=pd.DataFrame({"A":[0,.5,0]})
        weights=pd.DataFrame({"A":[0,1,0]})
        self.assertAlmostEqual(lagged_portfolio_returns(returns,weights).sum(),0)

    def test_invalid_data_is_rejected(self):
        data=bars([100,101,102])
        data.loc[1,"low"]=120
        with self.assertRaises(ValueError):validate_ohlcv(data)
        data=bars([100,101,102]);data.index=[1,1,2]
        with self.assertRaises(ValueError):validate_ohlcv(data)
        with self.assertRaises(ValueError):run_backtest(bars([100,100,100]),pd.Series([2,0,0]))


if __name__=="__main__":
    unittest.main()
