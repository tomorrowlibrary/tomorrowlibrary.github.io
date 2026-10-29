# Tomorrow Library research workbench

A small educational workflow: CSV -> validated bars -> trailing features -> chronological ridge baseline -> target positions -> next-open execution -> equity, costs and risk reports.

This is a reference implementation, not the old TMRW or WTech engine. It does not connect to a broker. It runs locally; the website provides documentation and downloads.

## Run

Use Python 3.10 or newer. From this directory:

    python -m venv .venv

Activate it with .venv\Scripts\activate on Windows, or source .venv/bin/activate on macOS/Linux. Then:

    python -m pip install -r requirements.txt
    python -m unittest discover -s tests -v
    python make_synthetic_fixture.py
    python run_research.py --csv data/SYNTHETIC-fixture.csv --annualisation 252 --out results/install-check

The fixture is deliberately synthetic. Its performance has no market interpretation. The annualisation example of 252 belongs to the daily demonstration; choose the correct frequency for your own series.

For an original Prosperity price CSV:

    python download_data.py --list
    python download_data.py --collection "Prosperity 2" --contains round_0 --out data

The included catalogue has the same captured files as the website. Select the downloaded price file and a product present in it. The downloader verifies recorded byte sizes and Git blob hashes before saving. Original source reuse terms remain applicable.

    python run_research.py --csv "path/to/prices.csv" --schema prosperity --product AMETHYSTS --annualisation 1 --out results/prosperity-proxy

The adapter uses midpoints and an ordinal observation index. OHLC fields are the same midpoint; no calendar intervals or exchange fills are inferred. Use an edition-compatible exchange backtester to evaluate actual competition submissions.

For ordinary OHLCV data, supply timestamp, open, high, low, close and optionally volume. Column names are case insensitive. Numeric timestamps need --timestamp-unit s or ms (or us/ns).

Try the ridge decision rule with --strategy ridge. Models fit only earlier observations; the two-row gap ensures each training label finishes before the test block. The ridge target is the next-open-to-following-open return. The PnL engine additionally accounts for slippage, fees and its forced final liquidation, so prediction MSE and trading PnL measure different things.

## Modules

| Module | Purpose |
| --- | --- |
| qtlib/data.py | OHLCV validation and competition midpoint adapter |
| qtlib/features.py | Trailing returns, volatility and displacement |
| qtlib/models.py | Ridge fit, training-only scaler and expanding evaluation |
| qtlib/portfolio.py | Long-only weights, inverse volatility, caps and lagged returns |
| qtlib/risk.py | Historical tail losses, drawdowns, volatility and zero-cash-rate Sharpe |
| qtlib/backtest.py | Single-asset cash/share account, next-open fills and trade ledger |

## Timing and limits

A close-t signal can trade at open t+1. Targets are fractions of equity after costs. Rebalance costs include fees and adverse slippage. Positions close at the final close and pay exit costs. Cash earns zero. No borrow, funding, impact, queues, partial fills, leverage beyond target absolute value 1, lot constraints or taxes are modelled.

Portfolio helpers are independently usable building blocks; the CLI account engine is single asset. The lagged portfolio-return helper omits execution costs and assumes the caller only supplies information available before each decision.

The signal is an illustrative baseline, not a claimed source of alpha. Forecast and PnL results include only a chronological evaluation segment after 150 observations, beginning flat. Repeatedly tuning on this segment makes it development data: reserve another untouched period for a final assessment.

## Outputs

features.csv, forecasts.csv, equity.csv, trades.csv, report.json. The report records the data SHA-256, configuration, costs and modelling limits. Never annualise a competition event index as if it were a calendar time series.

New workbench code is provided under the accompanying MIT licence. External repository examples retain their original attribution and terms; this licence does not grant rights to source datasets or external material.
