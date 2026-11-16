"""Reproduce the CTRL data profile and research studies.

The numbers on /CTRL/datasets/ and /CTRL/research/ come from this script.

Inputs
  --library  a checkout of github.com/MarkBrezina/Ctrl-Alt-DefeatTheMarket
             (commit 79108e33: Prosperity 1-3 files and the Prosperity 4 round 1 files)
  --p4       the prosperity4bt/resources folder of
             github.com/Xeeshan85/imc-prosperity-4-backtester (commit 40671cab),
             community-hosted Prosperity 4 rounds 0 and 2-5
Outputs (written to --out)
  profile.json   one record per CSV: edition, round, day, kind, rows, products, names
  studies.json   the anchor, basket and extremes studies

Usage
  python ctrl_research.py --library path/to/Ctrl-Alt-DefeatTheMarket \
                          --p4 path/to/prosperity4bt/resources --out results/
Requires pandas and numpy.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

P4_REPO = "Xeeshan85/imc-prosperity-4-backtester"
P4_COMMIT = "40671cab459e97fb417861348c9f86529cb428ca"


def read(path):
    head = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()[0]
    return pd.read_csv(path, sep="," if head.count(",") > head.count(";") else ";")


def git_blob_sha(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


# ------------------------------------------------------------------ profile
def profile(lib, p4):
    files = []
    for p in sorted(lib.rglob("*.csv")):
        rel = p.relative_to(lib).as_posix()
        if rel.startswith("Round 1/"):
            files.append((4, 1, "library", rel, p))  # Prosperity 4 round 1 (see notes)
        else:
            m = re.match(r"research/IMC(\d)/round (\d)/", rel)
            files.append((int(m.group(1)), int(m.group(2)), "library", rel, p))
    for p in sorted(p4.rglob("*.csv")):
        rnd = int(re.match(r"round(\d)/", p.relative_to(p4).as_posix()).group(1))
        if rnd != 1:  # round 1 is identical to the library copy
            files.append((4, rnd, "community", "prosperity4bt/resources/" + p.relative_to(p4).as_posix(), p))

    out, seen = [], {}
    for ed, rnd, src, rel, p in files:
        raw = p.read_bytes()
        df = read(p)
        name = p.name.lower()
        kind = "observations" if "observation" in name else "prices" if "price" in name else "trades"
        if kind == "prices" and "product" not in df.columns:
            kind = "observations"  # wide file: Prosperity 2 round 2 ORCHIDS and conditions
        m = re.search(r"round_(\d+)_day_(-?\d+)", p.name)
        rec = {"edition": ed, "round": rnd, "file_round": int(m.group(1)), "day": int(m.group(2)), "kind": kind,
               "source": src, "path": rel, "name": p.name, "bytes": len(raw), "git_blob": git_blob_sha(raw),
               "rows": int(len(df)), "columns": list(df.columns)}
        if kind == "prices":
            rec["products"] = sorted(df["product"].unique().tolist())
        elif kind == "trades":
            rec["products"] = sorted(df["symbol"].unique().tolist())
            rec["currency"] = sorted(df["currency"].dropna().unique().tolist())
            names = pd.concat([df["buyer"], df["seller"]]).dropna().astype(str)
            names = names[names.str.strip() != ""]
            rec["counterparties"] = sorted(set(names) - {"SUBMISSION"})
        else:
            rec["fields"] = [c for c in df.columns if c not in ("timestamp", "DAY", "day")]
        if src == "community":
            rec["source_url"] = f"https://github.com/{P4_REPO}/blob/{P4_COMMIT}/{rel}"
            rec["download_url"] = f"https://raw.githubusercontent.com/{P4_REPO}/{P4_COMMIT}/{rel}"
        sha = hashlib.sha1(raw).hexdigest()
        if sha in seen:
            rec["duplicate_of"] = seen[sha]
        else:
            seen[sha] = f"P{ed} round {rnd} · {p.name}"
        out.append(rec)
    return out


# ------------------------------------------------------------------ studies
def lib_file(lib, ed, rnd, name):
    return lib / f"research/IMC{ed}/round {rnd}" / f"IMC {ed} - {name}"


def wall(df, side):
    """Price of the level with the largest volume on one side of each snapshot."""
    prices = df[[f"{side}_price_{i}" for i in (1, 2, 3)]].to_numpy(dtype=float)
    vols = np.abs(df[[f"{side}_volume_{i}" for i in (1, 2, 3)]].to_numpy(dtype=float))
    vols = np.where(np.isnan(prices), -1, np.nan_to_num(vols, nan=-1))
    return prices[np.arange(len(df)), vols.argmax(axis=1)]


def anchor_study(lib, p4):
    sets = {
        "P1 · PEARLS": ("PEARLS", [lib_file(lib, 1, 1, f"prices_round_1_day_{d}.csv") for d in (-2, -1, 0)]),
        "P2 · AMETHYSTS": ("AMETHYSTS", [lib_file(lib, 2, 1, f"prices_round_1_day_{d}.csv") for d in (-2, -1, 0)]),
        "P3 · RAINFOREST_RESIN": ("RAINFOREST_RESIN", [lib_file(lib, 3, 1, f"prices_round_1_day_{d}.csv") for d in (-2, -1, 0)]),
        "P4 · EMERALDS": ("EMERALDS", [p4 / f"round0/prices_round_0_day_{d}.csv" for d in (-2, -1)]),
    }
    cols = [f"{s}_{k}_{i}" for s in ("bid", "ask") for k in ("price", "volume") for i in (1, 2, 3)]
    books, res = {}, {}
    for label, (prod, paths) in sets.items():
        px = pd.concat([read(p) for p in paths], ignore_index=True)
        px = px[px["product"] == prod].reset_index(drop=True)
        books[label] = px
        bb, ba = px["bid_price_1"], px["ask_price_1"]
        wm = (wall(px, "bid") + wall(px, "ask")) / 2
        take = (ba < 10000) | (bb > 10000)
        res[label] = {
            "days": len(paths), "snapshots": int(len(px)),
            "wall_mid_at_10000": round(float((wm == 10000).mean()), 4),
            "spread_median": float((ba - bb).median()),
            "takeable_share": round(float(take.mean()), 4), "takeable_per_day": round(float(take.sum() / len(paths)), 1),
            "best_bid_offsets": {int(k): round(float(v), 4) for k, v in (bb - 10000).dropna().astype(int).value_counts(normalize=True).sort_index().items()},
            "best_ask_offsets": {int(k): round(float(v), 4) for k, v in (ba - 10000).dropna().astype(int).value_counts(normalize=True).sort_index().items()},
        }
    a, b, c = (books[k][["day", "timestamp"] + cols].fillna(-1).to_numpy() for k in ("P1 · PEARLS", "P2 · AMETHYSTS", "P3 · RAINFOREST_RESIN"))
    identity = {"p1_p2_rows_equal": float((a == b).all(axis=1).mean()), "p2_p3_rows_equal": float((b == c).all(axis=1).mean()), "rows": int(len(a))}
    return {"products": res, "identity": identity}


def basket_study(lib):
    sets = {
        "P1 · PICNIC_BASKET": ([lib_file(lib, 1, 4, f"prices_round_4_day_{d}.csv") for d in (1, 2, 3)], "PICNIC_BASKET", {"BAGUETTE": 2, "DIP": 4, "UKULELE": 1}),
        "P2 · GIFT_BASKET": ([lib_file(lib, 2, 3, f"prices_round_3_day_{d}.csv") for d in (0, 1, 2)], "GIFT_BASKET", {"CHOCOLATE": 4, "STRAWBERRIES": 6, "ROSES": 1}),
        "P3 · PICNIC_BASKET1": ([lib_file(lib, 3, 2, f"prices_round_2_day_{d}.csv") for d in (-1, 0, 1)], "PICNIC_BASKET1", {"CROISSANTS": 6, "JAMS": 3, "DJEMBES": 1}),
        "P3 · PICNIC_BASKET2": ([lib_file(lib, 3, 2, f"prices_round_2_day_{d}.csv") for d in (-1, 0, 1)], "PICNIC_BASKET2", {"CROISSANTS": 4, "JAMS": 2}),
    }
    res, series = {}, {}
    for label, (paths, basket, weights) in sets.items():
        mids = pd.concat([read(p) for p in paths]).pivot_table(index=["day", "timestamp"], columns="product", values="mid_price")
        synthetic = sum(mids[k] * w for k, w in weights.items())
        spread = (mids[basket] - synthetic).dropna()
        phis, crossings, beta_b, beta_s = [], [], [], []
        for day, s in spread.groupby(level=0):
            x = s.to_numpy() - s.mean()
            phis.append(np.corrcoef(x[:-1], x[1:])[0, 1])
            crossings.append(int(np.sum(np.sign(x[1:]) != np.sign(x[:-1]))))
            bk, sy = mids[basket].loc[day].to_numpy(), synthetic.loc[day].to_numpy()
            dev = (bk - sy) - np.nanmean(bk - sy)
            k = 10  # who moves over the next 10 iterations after a deviation?
            ok = ~np.isnan(dev[:-k] + bk[k:] + sy[k:] + bk[:-k] + sy[:-k])
            beta_b.append(np.polyfit(dev[:-k][ok], (bk[k:] - bk[:-k])[ok], 1)[0])
            beta_s.append(np.polyfit(dev[:-k][ok], (sy[k:] - sy[:-k])[ok], 1)[0])
        phi = float(np.mean(phis))
        res[label] = {"weights": weights, "days": int(spread.index.get_level_values(0).nunique()),
                      "premium_mean": round(float(spread.mean()), 1), "premium_sd": round(float(spread.std()), 1),
                      "premium_by_day": [round(float(v), 1) for v in spread.groupby(level=0).mean()],
                      "ar1": round(phi, 4), "half_life_iterations": round(math.log(0.5) / math.log(phi)),
                      "zero_crossings_per_day": round(float(np.mean(crossings))),
                      "basket_move_per_unit_dev_10": round(float(np.mean(beta_b)), 4),
                      "synthetic_move_per_unit_dev_10": round(float(np.mean(beta_s)), 4)}
        series[label] = [[round(float(v), 1) for v in s.to_numpy()[::25]] for _, s in spread.groupby(level=0)]
    return {"baskets": res, "series": series}


def extremes_study(lib, p4):
    sets = []
    for rnd, days in ((1, (-2, -1, 0)), (3, (0, 1, 2)), (4, (1, 2, 3))):
        sets += [("P2", lib_file(lib, 2, 5, f"trades_round_{rnd}_day_{d}_withname.csv"), lib_file(lib, 2, rnd, f"prices_round_{rnd}_day_{d}.csv"), d) for d in days]
    sets += [("P3", lib_file(lib, 3, 5, f"trades_round_5_day_{d}.csv"), lib_file(lib, 3, 5, f"prices_round_5_day_{d}.csv"), d) for d in (2, 3, 4)]
    sets += [("P4", p4 / f"round4/trades_round_4_day_{d}.csv", p4 / f"round4/prices_round_4_day_{d}.csv", d) for d in (1, 2, 3)]
    rows = []
    for ed, tpath, ppath, day in sets:
        tr, px = read(tpath), read(ppath)
        lo = px.groupby("product")["mid_price"].min()
        hi = px.groupby("product")["mid_price"].max()
        for side, sign in (("buyer", 1), ("seller", -1)):
            t = tr[tr[side].notna() & (tr[side].astype(str).str.strip() != "") & (tr[side] != "SUBMISSION")]
            for r in t.itertuples(index=False):
                rng = hi.get(r.symbol, np.nan) - lo.get(r.symbol, np.nan)
                pos = (r.price - lo.get(r.symbol, np.nan)) / rng if rng and rng > 0 else np.nan
                rows.append({"edition": ed, "day": day, "trader": getattr(r, side), "product": r.symbol, "side": sign, "qty": int(r.quantity), "ts": int(r.timestamp), "pos": pos})
    R = pd.DataFrame(rows)
    summary = []
    for (ed, trader, product), g in R.groupby(["edition", "trader", "product"]):
        if len(g) < 3:
            continue
        at_ext = (((g.side > 0) & (g.pos <= 0.05)) | ((g.side < 0) & (g.pos >= 0.95))).mean()
        summary.append({"edition": ed, "trader": trader, "product": product, "trades": int(len(g)), "buys": int((g.side > 0).sum()),
                        "sells": int((g.side < 0).sum()), "qty_mode": int(g.qty.mode().iloc[0]), "at_extreme": round(float(at_ext), 3),
                        "buy_pos_mean": round(float(g[g.side > 0].pos.mean()), 3) if (g.side > 0).any() else None,
                        "sell_pos_mean": round(float(g[g.side < 0].pos.mean()), 3) if (g.side < 0).any() else None})
    best_p4 = max((s for s in summary if s["edition"] == "P4"), key=lambda s: s["at_extreme"])
    picks = [("P2", "Rhianna", "ROSES"), ("P3", "Olivia", "SQUID_INK"), ("P3", "Olivia", "CROISSANTS"), ("P3", "Olivia", "KELP"),
             ("P3", "Charlie", "KELP"), ("P4", best_p4["trader"], best_p4["product"])]
    dots = {}
    rng = np.random.default_rng(7)
    for ed, trader, product in picks:
        g = R[(R.edition == ed) & (R.trader == trader) & (R["product"] == product)]
        if len(g) > 160:  # thin out busy market makers so the chart stays legible
            g = g.iloc[np.sort(rng.choice(len(g), 160, replace=False))]
        dots[f"{ed} · {trader} · {product}"] = [[round(float(p), 4), int(s)] for p, s in zip(g.pos, g.side)]
    return {"summary": summary, "dots": dots, "p4_best": best_p4,
            "p4_traders": sorted(R[R.edition == "P4"].trader.unique().tolist())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--library", type=Path, required=True)
    ap.add_argument("--p4", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "profile.json").write_text(json.dumps(profile(a.library, a.p4), indent=1))
    studies = {"anchor": anchor_study(a.library, a.p4), "basket": basket_study(a.library), "extremes": extremes_study(a.library, a.p4)}
    (a.out / "studies.json").write_text(json.dumps(studies, indent=1))
    print("wrote", a.out / "profile.json", "and", a.out / "studies.json")


if __name__ == "__main__":
    main()
