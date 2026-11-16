"""Build the generated parts of the CTRL guide.

  python tools/ctrl/build_ctrl.py            # data terminal, known alphas, research log, landing-page matrix
  python tools/ctrl/build_ctrl.py --chapters # also re-wrap the four chapter pages in the shared CTRL shell

Inputs (all in the repository):
  catalogue/datasets.json      raw and source links for the Library's own files
  CTRL/datasets/profile.json   file-by-file profile  (CTRL/research/code/ctrl_research.py)
  CTRL/research/studies.json   study results          (CTRL/research/code/ctrl_research.py)
  CTRL/alphas/alphas.json      the known-alphas registry; edit this file to add a pattern
Outputs:
  CTRL/datasets/index.html, CTRL/alphas/index.html, CTRL/research/index.html
  the region between <!-- ctrl:matrix --> markers in CTRL/index.html
The landing page and chapter pages stay hand-authored. Run tools/build.py afterwards
so search and the sitemap pick up the pages.
"""
import json
import re
import sys
from collections import defaultdict
from html import escape, unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CTRL = ROOT / "CTRL"
LIB_REPO = "https://github.com/MarkBrezina/Ctrl-Alt-DefeatTheMarket/blob/79108e330ef5e1cbec4489932184bce82f0644ee/"
P4_REPO = "https://github.com/Xeeshan85/imc-prosperity-4-backtester/tree/40671cab459e97fb417861348c9f86529cb428ca/prosperity4bt/resources"


def e(value):
    return escape(str(value), quote=True)


def mb(n):
    return f"{n / 1e6:.1f} MB"


def num(n):
    return f"{n:,}"


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


# --------------------------------------------------------------------------- shell
NAV = [
    ("guide", [("↖", "Overview", "index.html"), ("01", "Data &amp; research", "data/index.html"),
               ("02", "Market dynamics &amp; alpha", "market-dynamics/index.html"),
               ("03", "Inventory, portfolio &amp; risk", "inventory-risk/index.html"),
               ("04", "Execution, orders &amp; backtests", "execution-backtesting/index.html")]),
    ("terminal", [("db", "Historical data", "datasets/index.html"), ("α", "Known alphas", "alphas/index.html"),
                  ("Σ", "Research studies", "research/index.html")]),
]


def nav_html(current, label):
    out = ""
    for group, items in NAV:
        out += f'<p class="ctrl-nav-group">{group}</p><nav class="ctrl-chapter-nav" aria-label="{e(group.title())} pages">'
        for glyph, text, href in items:
            cur = ' aria-current="page"' if href == current else ""
            out += f'<a href="../{href}"{cur}><span>{glyph}</span><span>{text}</span></a>'
        out += "</nav>"
    return out


def shell(slug, title, description, crumb, body, current, script=False, mobile_label=None):
    """Wrap an inner CTRL page (one folder below /CTRL/) in the shared terminal shell."""
    url = f"https://tomorrowlibrary.github.io/CTRL/{slug}/"
    sidebar = (f'<aside class="ctrl-sidebar" aria-label="Guide navigation"><div class="ctrl-sidebar-inner">{nav_html(current, crumb)}'
               f'<div class="ctrl-sidebar-note">Preparing for the next edition.<a href="../index.html#prosperity-5">Getting started with Prosperity 5</a></div></div></aside>')
    mobile = (f'<details class="ctrl-mobile-nav"><summary>{mobile_label or "Browse the guide"}</summary>{nav_html(current, crumb)}</details>')
    js = '\n  <script defer src="../../assets/ctrl.js"></script>' if script else ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)} | Tomorrow Library</title>
  <meta name="description" content="{e(description)}">
  <link rel="canonical" href="{url}">
  <meta property="og:title" content="{e(title)} | Tomorrow Library">
  <meta property="og:description" content="{e(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{url}">
  <meta name="theme-color" content="#050b16">
  <link rel="icon" href="../../assets/wave-mark.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../../assets/ctrl.css">{js}
</head>
<body class="ctrl-site">
  <a class="skip" href="#main">Skip to content</a>
  <div class="network"><span class="network-label">TOMORROW / KNOWLEDGE &amp; METHODS</span><nav aria-label="Tomorrow projects"><a href="https://tomorrowcapitalresearch.github.io/">Capital Research</a><a href="../../index.html" aria-current="true">Library</a><a href="https://tomorrowmarkets.github.io/">Markets ↗</a></nav></div>
  <header class="site-head">
    <a class="brand" href="../../index.html"><img src="../../assets/wave-mark.svg" alt="" width="30" height="32"><span class="brand-name">Tomorrow Library<small>CTRL / IMC Prosperity guide</small></span></a>
    <nav class="ctrl-header-nav" aria-label="Main navigation"><a href="../../guide.html">Learn</a><a href="../../competitions.html">Compete</a><a class="ctrl-header-home" href="../index.html#prosperity-5">Prosperity 5 on standby</a></nav>
  </header>
  <div class="ctrl-shell">
    <nav class="ctrl-breadcrumb" aria-label="Breadcrumb"><a href="../../index.html">Library</a><span aria-hidden="true">/</span><a href="../../competitions.html">Compete</a><span aria-hidden="true">/</span><a href="../index.html">IMC Prosperity</a><span aria-hidden="true">/</span><span aria-current="page">{crumb}</span></nav>
    <div class="ctrl-guide-layout">
  {sidebar}
  <main class="ctrl-article" id="main">
    {mobile}
{body}
  </main>
</div>
  </div>
  <footer class="ctrl-footer"><div><span class="ctrl-footer-name">Ctrl+Alt+DefeatTheMarket</span><p>An independent learning guide by Tomorrow Library. Not affiliated with IMC.</p></div><nav aria-label="Footer"><a href="../index.html">Guide overview</a><a href="../datasets/index.html">Historical data</a><a href="../alphas/index.html">Known alphas</a><a href="../research/index.html">Research</a><a href="https://prosperity.imc.com/">Official IMC Prosperity ↗</a><a href="https://github.com/tomorrowlibrary/tomorrowlibrary.github.io">GitHub ↗</a></nav></footer>
</body>
</html>
'''


# --------------------------------------------------------------------------- data
ROUND_NOTES = {
    (1, 1): "PEARLS, anchored near 10,000, and BANANAS, which drift.",
    (1, 2): "Adds COCONUTS and PINA_COLADAS, the pair Stanford Cardinal traded at a 15/8 ratio.",
    (1, 3): "Adds BERRIES, DIVING_GEAR and DOLPHIN_SIGHTINGS. DOLPHIN_SIGHTINGS appears in the prices file but never trades: it is an observation, not a market.",
    (1, 4): "Adds PICNIC_BASKET with its ingredients BAGUETTE, DIP and UKULELE.",
    (2, 0): "The tutorial: one day of AMETHYSTS and STARFRUIT.",
    (2, 1): "AMETHYSTS, anchored at 10,000, and STARFRUIT, which drifts.",
    (2, 2): "Only ORCHIDS observations survive in the archive: price, transport fees, tariffs, sunlight and humidity in one wide table. The files are named prices_* but hold no order book.",
    (2, 3): "GIFT_BASKET with CHOCOLATE, STRAWBERRIES and ROSES.",
    (2, 4): "COCONUT and COCONUT_COUPON, a call option on it.",
    (2, 5): "No new prices. Trades from rounds 1, 3 and 4 re-released with buyer and seller names.",
    (3, 1): "RAINFOREST_RESIN, anchored at 10,000, KELP, which drifts, and the jumpier SQUID_INK.",
    (3, 2): "Adds CROISSANTS, JAMS, DJEMBES and two baskets built from them.",
    (3, 3): "Adds VOLCANIC_ROCK and five vouchers with strikes from 9,500 to 10,500. Day 3 already includes MAGNIFICENT_MACARONS.",
    (3, 4): "Adds MAGNIFICENT_MACARONS, with external prices, tariffs, fees, sugar price and sunlight index in the observations files.",
    (3, 5): "Same products; the trades now carry buyer and seller names.",
    (4, 0): "The tutorial: EMERALDS, anchored at 10,000, and TOMATOES, which drift.",
    (4, 1): "ASH_COATED_OSMIUM, which drifts, and INTARIAN_PEPPER_ROOT, which follows a trend.",
    (4, 2): "Same products. The round added a market-access auction through a bid() method.",
    (4, 3): "HYDROGEL_PACK, VELVETFRUIT_EXTRACT and ten vouchers on it, VEV_4000 to VEV_6500.",
    (4, 4): "Same products; the trades now carry counterparty IDs such as Mark 01.",
    (4, 5): "Fifty products in ten families of five: GALAXY_SOUNDS, MICROCHIP, OXYGEN_SHAKE, PANEL, PEBBLES, ROBOT, SLEEP_POD, SNACKPACK, TRANSLATOR and UV_VISOR.",
}
EDITIONS = {1: ("Prosperity 1", "2023, SeaShells"), 2: ("Prosperity 2", "2024, SeaShells"),
            3: ("Prosperity 3", "2025, SeaShells"), 4: ("Prosperity 4", "April 2026, XIRECs")}
MISSING = {(1, 0): "No tutorial data in the archive.", (1, 5): "Round 5 (names revealed) is not in the archive.",
           (3, 0): "No tutorial data in the archive.", (2, 2): None}


def load():
    profile = json.loads((CTRL / "datasets/profile.json").read_text())
    catalogue = {d["source_path"]: d for d in json.loads((ROOT / "catalogue/datasets.json").read_text())}
    for rec in profile:
        if rec["source"] == "library":
            cat = catalogue[rec["path"]]
            rec["download_url"], rec["source_url"] = cat["download_url"], cat["source_url"]
    rounds = defaultdict(list)
    for rec in profile:
        rounds[(rec["edition"], rec["round"])].append(rec)
    return profile, rounds


def round_summary(files):
    uniq = [f for f in files if not f.get("duplicate_of")]
    prices = [f for f in files if f["kind"] == "prices"]
    days = sorted({f["day"] for f in prices} or {f["day"] for f in files if f["kind"] == "observations"})
    products = sorted({p for f in prices for p in f.get("products", [])})
    named = any(f.get("counterparties") for f in files if f["kind"] == "trades")
    return {"days": days, "products": products, "named": named, "files": len(files),
            "bytes": sum(f["bytes"] for f in files), "unique_bytes": sum(f["bytes"] for f in uniq),
            "community": all(f["source"] == "community" for f in files)}


def matrix_html(rounds):
    out = ['<div class="ctrl-matrix-wrap"><table class="ctrl-matrix"><caption class="sr-only">Historical data by edition and round</caption>',
           '<thead><tr><th scope="col"><span class="sr-only">Edition</span></th>']
    out += [f'<th scope="col">{"tutorial" if r == 0 else "round " + str(r)}</th>' for r in range(6)]
    out.append("</tr></thead><tbody>")
    for ed in (4, 3, 2, 1):
        name, sub = EDITIONS[ed]
        out.append(f'<tr><th scope="row"><b>P{ed}</b>{sub.split(",")[0]}</th>')
        for r in range(6):
            files = rounds.get((ed, r))
            if not files:
                out.append('<td class="is-empty"><span>not archived</span></td>')
                continue
            s = round_summary(files)
            m = s["unique_bytes"] / 1e6
            lv = 1 if m < 5 else 2 if m < 15 else 3 if m < 40 else 4
            if s["products"]:
                line = f'{len(s["products"])} products' + (", names" if s["named"] else "")
                head = plural(len(s["days"]), "day")
            elif s["named"]:
                head, line = f'{s["files"]} files', "named trades"
            else:
                head, line = plural(len(s["days"]), "day"), "observations"
            cls = f"lv{lv}" + (" is-community" if s["community"] else "")
            label = f'Prosperity {ed} {"tutorial" if r == 0 else "round " + str(r)}: {head}, {line}, {mb(s["bytes"])}'
            out.append(f'<td class="{cls}"><a href="datasets/index.html#p{ed}-r{r}" aria-label="{e(label)}"><b>{head}</b>{line}</a></td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    out.append('<p class="ctrl-legend"><span><i></i>darker = more data</span><span><i class="c"></i>community-hosted</span><span><i class="e"></i>not in the archive</span></p>')
    return "".join(out)


def build_datasets(profile, rounds):
    totals = {"files": len(profile), "bytes": sum(f["bytes"] for f in profile), "rows": sum(f["rows"] for f in profile),
              "unique": sum(f["bytes"] for f in profile if not f.get("duplicate_of"))}
    body = f'''    <header class="ctrl-article-head"><p class="ctrl-path">ctrl/<b>datasets</b></p><h1>Explore historical data.</h1><p class="ctrl-lead">Every Prosperity file we could source, from the first edition to the fourth, profiled one by one: what each round traded, how many days it covers, and the quirks that break a naive loader.</p></header>
    <dl class="ctrl-stats">
      <div><dt>editions</dt><dd>4</dd></div>
      <div><dt>files</dt><dd>{totals["files"]}</dd></div>
      <div><dt>size</dt><dd>{totals["bytes"] / 1e6:.0f} MB</dd></div>
      <div><dt>rows</dt><dd>{totals["rows"] / 1e6:.1f} m</dd></div>
    </dl>
    <section aria-labelledby="quirks-title">
      <h2 id="quirks-title">Read this before you load anything</h2>
      <ul class="ctrl-quirks">
        <li><span>mislabelled</span><span>Prosperity 2 round 2: the three files named <code>prices_round_2_day_*.csv</code> hold ORCHIDS observations in one wide table, not an order book.</span></li>
        <li><span>re-released</span><span>Some days ship twice. Prosperity 3 round 4 day 3 repeats round 3 day 3; round 5 days 2 and 3 repeat round 4 (prices and observations); Prosperity 4 round 4 days 1 and 2 repeat round 3. Count each day once.</span></li>
        <li><span>edition</span><span>The Library catalogue files under “Prosperity guide” are Prosperity 4 round 1 data: they have the same git blob hashes as the round 1 files in a public Prosperity 4 backtester.</span></li>
        <li><span>names</span><span>Buyer and seller names appear in Prosperity 2 round 5 (the <code>_withname</code> files for rounds 1, 3 and 4), Prosperity 3 round 5 and Prosperity 4 round 4. Elsewhere they are blank.</span></li>
        <li><span>separators</span><span>Prices and trades use semicolons. Prosperity 3 observations use commas.</span></li>
        <li><span>empty sides</span><span>A book side can be empty; <code>mid_price</code> then comes from the other side alone. Filter or backfill before using it as a price.</span></li>
        <li><span>community</span><span>Prosperity 4 tutorial and rounds 2 to 5 come from a community backtester repository, pinned to one commit. Their provenance has not been checked against IMC's own downloads.</span></li>
        <li><span>currency</span><span>Trades are quoted in SEASHELLS in Prosperity 1 to 3 and in XIRECS in Prosperity 4.</span></li>
      </ul>
    </section>
    <section aria-labelledby="load-title">
      <h2 id="load-title">Load a day in four lines</h2>
      <figure class="ctrl-code">
        <div class="ctrl-code-head"><span>python, pandas</span><button class="ctrl-copy" type="button" data-copy="loader">Copy</button></div>
<pre id="loader"><code>import pandas as pd
prices = pd.read_csv("prices_round_1_day_0.csv", sep=";")
trades = pd.read_csv("trades_round_1_day_0.csv", sep=";")
book = prices[prices["product"] == "KELP"].set_index("timestamp")</code></pre>
      </figure>
      <div class="ctrl-table-wrap"><table class="ctrl-table">
        <caption class="sr-only">File schemas</caption>
        <thead><tr><th scope="col">file</th><th scope="col">columns</th></tr></thead>
        <tbody>
          <tr><td>prices</td><td><code>day, timestamp, product, bid_price_1..3, bid_volume_1..3, ask_price_1..3, ask_volume_1..3, mid_price, profit_and_loss</code></td></tr>
          <tr><td>trades</td><td><code>timestamp, buyer, seller, symbol, currency, price, quantity</code></td></tr>
          <tr><td>observations, P3</td><td><code>timestamp, bidPrice, askPrice, transportFees, exportTariff, importTariff, sugarPrice, sunlightIndex</code></td></tr>
          <tr><td>observations, P2 round 2</td><td><code>timestamp, ORCHIDS, TRANSPORT_FEES, EXPORT_TARIFF, IMPORT_TARIFF, SUNLIGHT, HUMIDITY, DAY</code></td></tr>
        </tbody></table></div>
      <p class="ctrl-note">Timestamps step by 100 within a day, so one day is 10,000 iterations. Ask volumes in the order book are negative in the trader's <code>OrderDepth</code>, positive in these files.</p>
    </section>
'''
    for ed in (4, 3, 2, 1):
        name, sub = EDITIONS[ed]
        eds = [f for f in profile if f["edition"] == ed]
        src = "community-hosted except round 1" if ed == 4 else "from the Library's source archive"
        body += f'''    <section class="ctrl-edition-block" aria-labelledby="ed-{ed}">
      <header><h2 id="ed-{ed}">{name}</h2><p>{sub}, {len(eds)} files, {mb(sum(f["bytes"] for f in eds))}, {src}</p></header>
'''
        for r in range(6):
            files = sorted(rounds.get((ed, r), []), key=lambda f: (f["kind"], f["file_round"], f["day"]))
            label = "tutorial" if r == 0 else f"round {r}"
            if not files:
                if (ed, r) in MISSING and MISSING[(ed, r)]:
                    body += f'      <details class="ctrl-round" id="p{ed}-r{r}"><summary><b>{label}</b><span>{MISSING[(ed, r)]}</span><small>0 files</small></summary><div class="ctrl-round-body"><p class="ctrl-round-note">If you have this round, the Library\'s <a href="../../publish-data.html">dataset publication guide</a> explains how to add it.</p></div></details>\n'
                continue
            s = round_summary(files)
            if s["products"]:
                summ = f'{plural(len(s["days"]), "day")}, {len(s["products"])} products' + (", named trades" if s["named"] else "")
            elif s["named"]:
                summ = f'named trades for earlier rounds'
            else:
                summ = f'{len(s["days"])} days, observations only'
            body += f'      <details class="ctrl-round" id="p{ed}-r{r}"><summary><b>{label}</b><span>{summ}</span><small>{len(files)} files, {mb(s["bytes"])}</small></summary><div class="ctrl-round-body">\n'
            body += f'        <p class="ctrl-round-note">{e(ROUND_NOTES.get((ed, r), ""))}</p>\n'
            if s["products"]:
                body += '        <ul class="ctrl-products">' + "".join(f"<li>{e(p)}</li>" for p in s["products"]) + "</ul>\n"
            cps = sorted({c for f in files for c in f.get("counterparties", [])})
            if cps:
                body += f'        <p class="ctrl-round-note">Counterparties: {e(", ".join(cps))}.</p>\n'
            body += '        <div class="ctrl-table-wrap"><table class="ctrl-table"><thead><tr><th scope="col">file</th><th scope="col">kind</th><th scope="col" class="num">day</th><th scope="col" class="num">rows</th><th scope="col" class="num">size</th><th scope="col">open</th><th scope="col">note</th></tr></thead><tbody>\n'
            for f in files:
                notes = []
                if f.get("duplicate_of"):
                    notes.append("same file as " + f["duplicate_of"].replace(" · ", ", "))
                if f["source"] == "community":
                    notes.append("community-hosted")
                if f["kind"] == "trades" and f.get("counterparties"):
                    notes.append("named")
                if f["file_round"] != f["round"]:
                    notes.append(f"trades from round {f['file_round']}")
                kind = f["kind"] if not (f["kind"] == "observations" and f["name"].startswith("IMC 2 - prices")) else "observations, named prices_*"
                body += (f'          <tr><td><code>{e(f["name"])}</code></td><td>{kind}</td><td class="num">{f["day"]}</td><td class="num">{num(f["rows"])}</td>'
                         f'<td class="num">{mb(f["bytes"])}</td><td><a href="{e(f["download_url"])}">raw ↗</a> <a href="{e(f["source_url"])}">source ↗</a></td><td>{e("; ".join(notes))}</td></tr>\n')
            body += "        </tbody></table></div>\n      </div></details>\n"
        body += "    </section>\n"
    body += f'''    <section aria-labelledby="provenance-title">
      <h2 id="provenance-title">Where the files come from</h2>
      <div class="ctrl-prose"><p>Prosperity 1 to 3 and Prosperity 4 round 1 are the Library's own copies, pinned to commit <code>79108e33</code> of <a href="{LIB_REPO}">MarkBrezina/Ctrl-Alt-DefeatTheMarket</a>. The Prosperity 2 and 3 round 1 files match, byte for byte, the copies bundled with Jasper van Merle's backtesters. Prosperity 4's other rounds link to <a href="{P4_REPO}">a community backtester</a> at commit <code>40671cab</code>.</p>
      <p>Neither source records reuse terms for the competition data itself, so check before you redistribute it. The profile behind this page is <a href="profile.json">profile.json</a>, produced by <a href="../research/code/ctrl_research.py">ctrl_research.py</a>.</p></div>
    </section>
    <nav class="ctrl-pagination" aria-label="Continue"><a href="../index.html"><span>← back</span>Guide overview</a><a href="../alphas/index.html"><span>next →</span>Known alphas</a></nav>
'''
    page = shell("datasets", "Historical data — CTRL", "Every IMC Prosperity data file from four editions, profiled: products, days, rows, duplicates and quirks, with raw and source links.",
                 "Historical data", body, "datasets/index.html", script=True)
    (CTRL / "datasets/index.html").write_text(page)


# --------------------------------------------------------------------------- alphas
STATUS_CHIP = {"recurring": "is-ready", "edition-specific": "", "mixed evidence": "is-mixed", "recurring until P4": "is-pending"}


def build_alphas():
    data = json.loads((CTRL / "alphas/alphas.json").read_text())
    src = data["sources"]
    items = data["alphas"]
    body = f'''    <header class="ctrl-article-head"><p class="ctrl-path">ctrl/<b>alphas</b></p><h1>Known alphas.</h1><p class="ctrl-lead">{len(items)} patterns that paid in earlier Prosperity editions: where each appeared, how teams traded it, how to test for it on the first day of a round, and how it fails. Each ticker is a name for the pattern, not a product.</p></header>
    <div class="ctrl-prose"><p>None of these is a promise for Prosperity 5. Organisers change generators, and the best-known patterns are the ones most likely to be removed. Treat the list as a checklist of questions to ask the new data. The registry is <a href="alphas.json">alphas.json</a>; add a pattern there and rebuild.</p></div>
    <ul class="ctrl-tickers is-index" aria-label="Index of patterns">
'''
    for a in items:
        body += f'      <li><code><a href="#{a["ticker"].lower()}">{a["ticker"]}</a></code><span>{e(a["name"])}</span>{seen_html(a)}</li>\n'
    body += '    </ul>\n    <div class="ctrl-registry">\n'
    for a in items:
        chip = STATUS_CHIP.get(a["status"], "")
        lists = "".join(f'<div><h3>{h}</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in a[k])}</ul></div>' for h, k in (("how it was traded", "how"), ("test it on day one", "test"), ("how it fails", "fail")))
        sources = ", ".join(f'<a href="{e(src[s]["url"])}">{e(src[s]["label"])}</a>' for s in a["sources"])
        body += f'''      <article class="ctrl-alpha" id="{a["ticker"].lower()}">
        <header><div><code>{a["ticker"]}</code><h2>{e(a["name"])}</h2></div><div class="ctrl-alpha-flags"><span class="ctrl-chip {chip}">{e(a["status"])}</span>{seen_html(a)}</div></header>
        <p class="ctrl-alpha-what">{e(a["what"])}</p>
        <div class="ctrl-alpha-body">{lists}</div>
        <footer>Seen in: {e(seen_text(a))}. Sources: {sources}.</footer>
      </article>
'''
    body += '''    </div>
    <nav class="ctrl-pagination" aria-label="Continue"><a href="../datasets/index.html"><span>← back</span>Historical data</a><a href="../research/index.html"><span>next →</span>Research studies</a></nav>
'''
    page = shell("alphas", "Known alphas — CTRL", "Patterns that paid in earlier IMC Prosperity editions, where they appeared, how to test for them and how they fail.",
                 "Known alphas", body, "alphas/index.html")
    (CTRL / "alphas/index.html").write_text(page)


def seen_html(a):
    cells = []
    for ed in ("P1", "P2", "P3", "P4"):
        v = a["seen"].get(ed, "")
        if a.get("seen_all"):
            cells.append(f'<i class="on" title="{ed}: every edition">{ed}</i>')
        elif v.startswith("not found"):
            cells.append(f'<i class="no" title="{ed}: not found">{ed}</i>')
        elif v:
            cells.append(f'<i class="on" title="{ed}: {e(v)}">{ed}</i>')
        else:
            cells.append(f"<i>{ed}</i>")
    return f'<span class="ctrl-seen" aria-label="{e(seen_text(a))}">' + "".join(cells) + "</span>"


def seen_text(a):
    if a.get("seen_all"):
        return "every edition"
    parts = [f"{ed} {v}" for ed, v in a["seen"].items() if v]
    return "; ".join(parts) if parts else "not yet seen"


# --------------------------------------------------------------------------- research charts
def svg_anchor(anchor):
    """Two ladders: where the best bid and best ask sat, relative to 10,000."""
    panels = [("P1, P2 and P3 (identical books)", anchor["P1 · PEARLS"]), ("P4, EMERALDS", anchor["P4 · EMERALDS"])]
    W, H, top, rh = 860, 420, 46, 20
    out = [f'<svg class="viz" viewBox="0 0 {W} {H}" role="img" aria-labelledby="fig1-t fig1-d"><title id="fig1-t">Where the best quotes sat</title><desc id="fig1-d">Share of snapshots with the best bid and best ask at each price, relative to 10,000. In Prosperity 1 to 3 the best bid was 4 below 10,000 half the time; in Prosperity 4 it was 8 below in 98% of snapshots.</desc>']
    for k, (title, d) in enumerate(panels):
        x0 = 20 + k * (W / 2)
        cx = x0 + W / 4 - 10
        out.append(f'<text class="h" x="{x0}" y="18">{e(title)}</text>')
        out.append(f'<text x="{cx - 34}" y="36" text-anchor="end">best bid</text><text x="{cx + 34}" y="36">best ask</text>')
        for i, off in enumerate(range(8, -9, -1)):
            y = top + i * rh
            price = 10000 + off
            out.append(f'<rect class="row{" z" if off == 0 else ""}" x="{x0}" y="{y}" width="{W / 2 - 50}" height="{rh - 2}"/>')
            out.append(f'<text class="p{" b" if off == 0 else ""}" x="{cx}" y="{y + 14}" text-anchor="middle">{price:,}</text>')
            maxw = W / 4 - 100
            for side, sign in (("best_bid_offsets", -1), ("best_ask_offsets", 1)):
                share = d[side].get(str(off), d[side].get(off, 0))
                if not share:
                    continue
                w = max(2, maxw * share)
                x = cx - 30 - w if sign < 0 else cx + 30
                cls = "bid" if sign < 0 else "ask"
                out.append(f'<rect class="{cls}" x="{x:.1f}" y="{y + 3}" width="{w:.1f}" height="{rh - 8}" rx="2"><title>{"best bid" if sign < 0 else "best ask"} at {price:,}: {share * 100:.1f}% of snapshots</title></rect>')
                if share >= 0.015:
                    tx = x - 6 if sign < 0 else x + w + 6
                    out.append(f'<text class="v" x="{tx:.1f}" y="{y + 14}" text-anchor="{"end" if sign < 0 else "start"}">{share * 100:.1f}%</text>')
    out.append("</svg>")
    return "".join(out)


def svg_baskets(series, stats):
    W, H = 860, 470
    pw, ph = 400, 170
    out = [f'<svg class="viz" viewBox="0 0 {W} {H}" role="img" aria-labelledby="fig2-t fig2-d"><title id="fig2-t">Basket minus synthetic, three days each</title><desc id="fig2-d">Each panel shows a basket price minus the weighted mid prices of its ingredients over three historical days. The spread wanders around a positive premium and keeps crossing it.</desc>']
    for k, (label, days) in enumerate(series.items()):
        col, row = k % 2, k // 2
        x0, y0 = 20 + col * (pw + 40), 30 + row * (ph + 60)
        vals = [v for d in days for v in d]
        lo, hi = min(vals), max(vals)
        pad = (hi - lo) * 0.08
        lo, hi = lo - pad, hi + pad
        n = len(vals)
        X = lambda i: x0 + 46 + i / (n - 1) * (pw - 56)
        Y = lambda v: y0 + 22 + (1 - (v - lo) / (hi - lo)) * (ph - 30)
        s = stats[label]
        out.append(f'<text class="h" x="{x0}" y="{y0 + 6}">{e(label.replace(" · ", " "))}</text>')
        step = nice(hi - lo)
        v = (lo // step + 1) * step
        while v < hi:
            out.append(f'<line class="grid" x1="{x0 + 46}" x2="{x0 + pw - 10}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{x0 + 40}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:,.0f}</text>')
            v += step
        idx = 0
        for d_i, d in enumerate(days):
            if d_i:
                xs = X(idx - 0.5)
                out.append(f'<line class="sep" x1="{xs:.1f}" x2="{xs:.1f}" y1="{y0 + 16}" y2="{y0 + ph - 6}"/>')
            idx += len(d)
        mean = s["premium_mean"]
        out.append(f'<line class="mean" x1="{x0 + 46}" x2="{x0 + pw - 10}" y1="{Y(mean):.1f}" y2="{Y(mean):.1f}"/>')
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        out.append(f'<polyline class="line" points="{pts}"><title>{e(label)}: premium {mean:,.1f} on average, standard deviation {s["premium_sd"]:,.1f}, half-life {s["half_life_iterations"]} iterations</title></polyline>')
        out.append(f'<text class="v halo" x="{x0 + pw - 10}" y="{y0 + 6}" text-anchor="end">mean {mean:,.0f}</text>')
        out.append(f'<text x="{x0 + 46}" y="{y0 + ph + 12}">day 1</text><text x="{x0 + pw - 10}" y="{y0 + ph + 12}" text-anchor="end">day 3</text>')
    out.append("</svg>")
    return "".join(out)


def svg_extremes(dots, summary):
    W = 860
    rows = list(dots.items())
    rh, top, left, right = 46, 40, 210, 96
    H = top + len(rows) * rh + 34
    X = lambda p: left + p * (W - left - right)
    out = [f'<svg class="viz" viewBox="0 0 {W} {H}" role="img" aria-labelledby="fig3-t fig3-d"><title id="fig3-t">Where named traders bought and sold within the day\'s range</title><desc id="fig3-d">Each mark is one trade, placed between the day\'s lowest and highest mid price. Rhianna and Olivia bought at the bottom and sold at the top. A market maker and the most extreme Prosperity 4 trader spread across the range.</desc>']
    out.append(f'<rect class="zone" x="{X(0):.1f}" y="{top - 8}" width="{X(0.05) - X(0):.1f}" height="{len(rows) * rh + 4}"/><rect class="zone" x="{X(0.95):.1f}" y="{top - 8}" width="{X(1) - X(0.95):.1f}" height="{len(rows) * rh + 4}"/>')
    out.append(f'<text x="{X(0):.1f}" y="{top - 16}">day low</text><text x="{X(1):.1f}" y="{top - 16}" text-anchor="end">day high</text><text x="{X(0.5):.1f}" y="{top - 16}" text-anchor="middle">position within the day\'s range</text><text x="{W - 8}" y="{top - 16}" text-anchor="end">at extreme</text>')
    lookup = {(s["edition"], s["trader"], s["product"]): s for s in summary}
    for i, (label, pts) in enumerate(rows):
        ed, trader, product = label.split(" · ")
        s = lookup[(ed, trader, product)]
        y = top + i * rh + rh / 2
        out.append(f'<line class="grid" x1="{X(0):.1f}" x2="{X(1):.1f}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="h" x="16" y="{y - 3:.1f}">{e(ed)} {e(trader)}</text><text x="16" y="{y + 13:.1f}">{e(product)}, {s["trades"]} trades</text>')
        out.append(f'<text class="v" x="{W - 8}" y="{y + 4:.1f}" text-anchor="end">{s["at_extreme"] * 100:.0f}%</text>')
        for p, side in pts:
            x = X(min(1, max(0, p)))
            if side > 0:
                out.append(f'<path class="bid mk" d="M{x:.1f} {y - 7:.1f} l6 10 h-12z"><title>{e(trader)} bought at {p * 100:.1f}% of the range</title></path>')
            else:
                out.append(f'<path class="ask mk" d="M{x:.1f} {y + 7:.1f} l6 -10 h-12z"><title>{e(trader)} sold at {p * 100:.1f}% of the range</title></path>')
    ly = H - 12
    out.append(f'<path class="bid mk" d="M{left:.1f} {ly - 7} l6 10 h-12z"/><text x="{left + 12}" y="{ly + 1}">buy</text><path class="ask mk" d="M{left + 66:.1f} {ly + 5} l6 -10 h-12z"/><text x="{left + 78}" y="{ly + 1}">sell</text><rect class="zone" x="{left + 130}" y="{ly - 9}" width="14" height="12"/><text x="{left + 150}" y="{ly + 1}">bottom and top 5% of the range</text>')
    out.append("</svg>")
    return "".join(out)


def nice(r):
    raw = r / 4
    import math
    p = 10 ** math.floor(math.log10(raw))
    n = raw / p
    return (1 if n < 1.5 else 2 if n < 3.5 else 5 if n < 7.5 else 10) * p


def build_research():
    S = json.loads((CTRL / "research/studies.json").read_text())
    A = S["anchor"]["products"]
    I = S["anchor"]["identity"]
    B = S["basket"]["baskets"]
    X = S["extremes"]
    ext = {(s["edition"], s["trader"], s["product"]): s for s in X["summary"]}
    rh = ext[("P2", "Rhianna", "ROSES")]
    ol_s, ol_c, ol_k = ext[("P3", "Olivia", "SQUID_INK")], ext[("P3", "Olivia", "CROISSANTS")], ext[("P3", "Olivia", "KELP")]
    p4 = X["p4_best"]
    p13 = A["P1 · PEARLS"]
    em = A["P4 · EMERALDS"]
    pct = lambda x: ("−" if x < 0 else "") + f"{abs(x) * 100:.2f}%"
    b_rows = "".join(
        f'<tr><td>{e(k.replace(" · ", " "))}<br><small>{e(" + ".join(f"{w} {p}" for p, w in v["weights"].items()))}</small></td><td class="num">{v["premium_mean"]:,.1f}</td><td class="num">{v["premium_sd"]:,.1f}</td>'
        f'<td class="num">{v["half_life_iterations"]}</td><td class="num">{v["zero_crossings_per_day"]}</td>'
        f'<td class="num">{pct(-v["basket_move_per_unit_dev_10"])}</td><td class="num">{pct(v["synthetic_move_per_unit_dev_10"])}</td></tr>' for k, v in B.items())
    hl = [v["half_life_iterations"] for v in B.values()]
    a_rows = "".join(f'<tr><td>{"bid" if s == "best_bid_offsets" else "ask"}</td><td>{e(lbl)}</td><td>{", ".join(f"{int(o):+d}: {v * 100:.1f}%" for o, v in sorted(d[s].items(), key=lambda t: int(t[0])))}</td></tr>'
                     for lbl, d in (("P1 to P3", p13), ("P4 EMERALDS", em)) for s in ("best_bid_offsets", "best_ask_offsets"))
    x_rows = "".join(f'<tr><td>{s["edition"]}</td><td>{e(s["trader"])}</td><td>{e(s["product"])}</td><td class="num">{s["trades"]}</td><td class="num">{s["buys"]}/{s["sells"]}</td><td class="num">{s["qty_mode"]}</td><td class="num">{s["at_extreme"] * 100:.0f}%</td></tr>'
                     for s in sorted(X["summary"], key=lambda s: -s["at_extreme"])[:14])
    code_href = "code/ctrl_research.py"
    body = f'''    <header class="ctrl-article-head"><p class="ctrl-path">ctrl/<b>research</b></p><h1>Research studies.</h1><p class="ctrl-lead">Short, reproducible studies on the historical Prosperity files. Each states the question, the data, the method and the caveats, and every number on this page comes from one script in the repository.</p></header>
    <ol class="ctrl-logbook" aria-label="Research log">
      <li><div class="meta"><span>study 001</span><span>15 Nov 2026</span><span>book data, P1 to P4</span></div><a href="#study-001">One order book, three editions</a></li>
      <li><div class="meta"><span>study 002</span><span>15 Nov 2026</span><span>baskets, P1 to P3</span></div><a href="#study-002">Basket premiums revert, and the basket does the moving</a></li>
      <li><div class="meta"><span>study 003</span><span>15 Nov 2026</span><span>named trades, P2 to P4</span></div><a href="#study-003">The trader who knew the extremes</a></li>
      <li><div class="meta"><span>notes</span><span>author</span></div><a href="#notes">Round notes and code reviews from Prosperity 1 to 4</a></li>
    </ol>

    <article class="ctrl-study" id="study-001" aria-labelledby="s1-title">
      <header><p class="ctrl-path">study 001</p><h2 id="s1-title">One order book, three editions</h2></header>
      <p class="ctrl-study-q">Every edition opens with a product anchored at 10,000. Is it a new market each time?</p>
      <ul class="ctrl-findings">
        <li><b>{I["rows"]:,} of {I["rows"]:,}</b>round 1 snapshots of PEARLS (P1), AMETHYSTS (P2) and RAINFOREST_RESIN (P3) are identical: every price, volume and timestamp.</li>
        <li><b>{p13["takeable_share"] * 100:.1f}%</b>of those snapshots had a quote on the wrong side of 10,000, about {p13["takeable_per_day"]:,.0f} a day. Free edge for a bot that takes it.</li>
        <li><b>±8</b>Prosperity 4 changed it. EMERALDS sat at 9,992 / 10,008 in {em["best_bid_offsets"].get("-8", 0) * 100:.0f}% of snapshots, and no snapshot offered a mispriced quote.</li>
      </ul>
      <figure class="ctrl-figure">{svg_anchor(A)}
        <figcaption>Share of snapshots with the best bid and best ask at each price. Round 1 days −2 to 0 for P1 to P3, tutorial days −2 and −1 for P4.</figcaption>
        <details><summary>Show the numbers</summary><div class="ctrl-table-wrap"><table class="ctrl-table"><thead><tr><th scope="col">side</th><th scope="col">edition</th><th scope="col">offset from 10,000: share of snapshots</th></tr></thead><tbody>{a_rows}</tbody></table></div></details>
      </figure>
      <div class="ctrl-method">
        <div><h3>Data and method</h3><p>The round 1 price files of Prosperity 1 to 3 and the Prosperity 4 tutorial. After filtering each file to its anchored product, all twelve book columns plus day and timestamp were compared row by row. The trade files are not identical, so only the book repeated.</p></div>
        <div><h3>Why it matters</h3><p>On the first day of a round, test the new data for exact matches against the archive. A matching book means known quoting patterns and a known edge. Prosperity 4 shows the organisers can and do change the generator.</p></div>
        <div><h3>Caveats</h3><p>These are the published historical files. Rounds were scored on fresh simulations, which need not repeat the history exactly.</p></div>
        <div><h3>Related</h3><p><a href="../alphas/index.html#anchor">ANCHOR</a> and <a href="../alphas/index.html#dejavu">DEJAVU</a> in the known alphas.</p></div>
      </div>
    </article>

    <article class="ctrl-study" id="study-002" aria-labelledby="s2-title">
      <header><p class="ctrl-path">study 002</p><h2 id="s2-title">Basket premiums revert, and the basket does the moving</h2></header>
      <p class="ctrl-study-q">How large is the basket premium, how fast does it come back, and which side moves when it does?</p>
      <ul class="ctrl-findings">
        <li><b>{B["P1 · PICNIC_BASKET"]["premium_mean"]:,.0f} and {B["P2 · GIFT_BASKET"]["premium_mean"]:,.0f}</b>average premiums for the Prosperity 1 and 2 baskets; the Prosperity 3 baskets carried {B["P3 · PICNIC_BASKET1"]["premium_mean"]:,.0f} and {B["P3 · PICNIC_BASKET2"]["premium_mean"]:,.0f}.</li>
        <li><b>{min(hl)} to {max(hl)}</b>iterations: the half-life of a deviation, from an AR(1) fit within each day. Fast enough to trade many times a day.</li>
        <li><b>the basket moves</b>After a deviation the basket closes {-B["P2 · GIFT_BASKET"]["basket_move_per_unit_dev_10"] * 100:.1f}% of the gap every 10 iterations in P2. The ingredients close none of it: in every edition they drift up to {max(-v["synthetic_move_per_unit_dev_10"] for v in B.values()) * 100:.1f}% the other way.</li>
      </ul>
      <figure class="ctrl-figure">{svg_baskets(S["basket"]["series"], B)}
        <figcaption>Basket mid minus the weighted ingredient mids, sampled every 25 iterations. Dashed line: the three-day mean.</figcaption>
      </figure>
      <div class="ctrl-table-wrap"><table class="ctrl-table"><caption class="sr-only">Basket statistics</caption><thead><tr><th scope="col">basket and recipe</th><th scope="col" class="num">premium</th><th scope="col" class="num">sd</th><th scope="col" class="num">half-life, its</th><th scope="col" class="num">crossings a day</th><th scope="col" class="num">gap closed: basket</th><th scope="col" class="num">ingredients</th></tr></thead><tbody>{b_rows}</tbody></table></div>
      <div class="ctrl-method is-spaced">
        <div><h3>Data and method</h3><p>Mid prices for each basket and its ingredients over the three days of the round that introduced it. Spread = basket − Σ weight × ingredient. The share of the gap each leg closes is the slope of its 10-iteration price change on the demeaned spread; a negative share means that leg drifted away.</p></div>
        <div><h3>Why it matters</h3><p>Trade the basket toward the synthetic, not the reverse. Hedging with the ingredients cuts variance but adds spread costs without adding expected value, which matches Frankfurt Hedgehogs' account.</p></div>
        <div><h3>Caveats</h3><p>Mids are not tradable prices, so these numbers ignore the cost of crossing the spread. The premium moves between days: Prosperity 1's dropped by about 75 on day 3.</p></div>
        <div><h3>Related</h3><p><a href="../alphas/index.html#basket">BASKET</a> and <a href="../alphas/index.html#pairs">PAIRS</a> in the known alphas.</p></div>
      </div>
    </article>

    <article class="ctrl-study" id="study-003" aria-labelledby="s3-title">
      <header><p class="ctrl-path">study 003</p><h2 id="s3-title">The trader who knew the extremes</h2></header>
      <p class="ctrl-study-q">When trader names were revealed, did anyone buy the day's low and sell the day's high?</p>
      <ul class="ctrl-findings">
        <li><b>{rh["trades"]} of {rh["trades"]}</b>of Rhianna's ROSES trades in Prosperity 2 sat at an extreme: buys on average {rh["buy_pos_mean"] * 100:.1f}% up from the day's low, sells {rh["sell_pos_mean"] * 100:.1f}% of the way to the high.</li>
        <li><b>{ol_s["trades"] + ol_c["trades"]} of {ol_s["trades"] + ol_c["trades"]}</b>of Olivia's SQUID_INK and CROISSANTS trades in Prosperity 3 did the same. Her KELP trades came close without touching the extremes.</li>
        <li><b>0 of {len(X["p4_traders"])}</b>Prosperity 4 round 4 IDs showed the pattern. The closest, {e(p4["trader"])} on {e(p4["product"])}, had {p4["at_extreme"] * 100:.0f}% of trades at an extreme.</li>
      </ul>
      <figure class="ctrl-figure">{svg_extremes(X["dots"], X["summary"])}
        <figcaption>Each mark is one trade. The market maker Charlie on KELP is thinned to 160 random trades for legibility.</figcaption>
        <details><summary>Show the numbers</summary><div class="ctrl-table-wrap"><table class="ctrl-table"><thead><tr><th scope="col">edition</th><th scope="col">trader</th><th scope="col">product</th><th scope="col" class="num">trades</th><th scope="col" class="num">buys/sells</th><th scope="col" class="num">usual size</th><th scope="col" class="num">at an extreme</th></tr></thead><tbody>{x_rows}</tbody></table></div><p class="ctrl-note">Anchored products top this table because their daily range is only a few ticks wide, so any maker trading at its quotes lands near the edge. They are left out of the chart.</p></details>
      </figure>
      <div class="ctrl-method">
        <div><h3>Data and method</h3><p>Named trades from Prosperity 2 round 5 (rounds 1, 3 and 4 re-released), Prosperity 3 round 5 and Prosperity 4 round 4. Each trade is placed between the day's lowest and highest mid for its product. An extreme is a buy in the bottom 5% or a sell in the top 5%.</p></div>
        <div><h3>Why it matters</h3><p>The pattern survived three editions and paid well. Without names, Frankfurt Hedgehogs caught it by flagging trades of a recurring size at a new running daily extreme.</p></div>
        <div><h3>Caveats</h3><p>The day's range is only known at the close, so this is hindsight. A live detector must use the running minimum and maximum, and will see false alarms before the real extreme arrives.</p></div>
        <div><h3>Related</h3><p><a href="../alphas/index.html#extremes">EXTREMES</a> in the known alphas.</p></div>
      </div>
    </article>

    <section class="ctrl-study" id="notes" aria-labelledby="notes-title">
      <h2 id="notes-title">Notes from the author and others</h2>
      <ol class="ctrl-logbook">
        <li><div class="meta"><span>note</span><span>all editions</span></div><a href="{LIB_REPO}research/README.md">Across previous Prosperity editions ↗</a><p>Round by round, what each edition introduced and how teams approached it.</p></li>
        <li><div class="meta"><span>code review</span><span>P1, P2, P3</span></div><a href="{LIB_REPO}research/IMC1/round%201/readme.md">Round 1 strategies compared: Prosperity 1 ↗</a><p>Also for <a href="{LIB_REPO}research/IMC2/round%201/readme.md">Prosperity 2</a> and <a href="{LIB_REPO}research/IMC3/round%201/readme.md">Prosperity 3</a>: how fair value, taking, making and inventory differed between teams.</p></li>
        <li><div class="meta"><span>round notes</span><span>P4</span></div><a href="{LIB_REPO}Round%201/README.md">Prosperity 4, round 1 ↗</a><p>Then <a href="{LIB_REPO}Round%202/README.md">round 2</a> and <a href="{LIB_REPO}Round%203/README.md">round 3</a>: osmium denoising, the access auction, options and a candid post-mortem.</p></li>
        <li><div class="meta"><span>reference</span><span>author</span></div><a href="{LIB_REPO}GLOSSARY.md">Trading glossary ↗</a><p>With <a href="{LIB_REPO}MINDSET.md">a note on the mental side</a> and <a href="{LIB_REPO}RESOURCES.md">a reading list</a>.</p></li>
        <li><div class="meta"><span>paper</span><span>external</span></div><a href="https://arxiv.org/abs/1803.04094">Mean Field Games with Partial Information for Algorithmic Trading ↗</a><p>And <a href="https://arxiv.org/abs/2404.18200">Mean Field Game of High-Frequency Anticipatory Trading</a>. More in the <a href="../../papers.html">Library's papers</a>.</p></li>
      </ol>
    </section>

    <section class="ctrl-study" aria-labelledby="repro-title">
      <h2 id="repro-title">Rerun the studies</h2>
      <figure class="ctrl-code">
        <div class="ctrl-code-head"><span>shell</span><button class="ctrl-copy" type="button" data-copy="rerun">Copy</button></div>
<pre id="rerun"><code>git clone https://github.com/MarkBrezina/Ctrl-Alt-DefeatTheMarket
git clone https://github.com/Xeeshan85/imc-prosperity-4-backtester
python CTRL/research/code/ctrl_research.py \\
  --library Ctrl-Alt-DefeatTheMarket \\
  --p4 imc-prosperity-4-backtester/prosperity4bt/resources --out results/</code></pre>
      </figure>
      <p class="ctrl-note">Check out commits 79108e33 and 40671cab to reproduce these exact numbers. The script is <a href="{code_href}">ctrl_research.py</a>; its output is <a href="studies.json">studies.json</a> and <a href="../datasets/profile.json">profile.json</a>.</p>
    </section>
    <nav class="ctrl-pagination" aria-label="Continue"><a href="../alphas/index.html"><span>← back</span>Known alphas</a><a href="../index.html"><span>next →</span>Guide overview</a></nav>
'''
    page = shell("research", "Research studies — CTRL", "Reproducible studies on historical IMC Prosperity data: a repeated order book, basket premiums and the trader who knew the extremes.",
                 "Research studies", body, "research/index.html", script=True)
    (CTRL / "research/index.html").write_text(page)


# --------------------------------------------------------------------------- landing matrix
def update_matrix(rounds):
    path = CTRL / "index.html"
    html = path.read_text()
    start = html.index("<!-- ctrl:matrix")
    start = html.index("-->", start) + 3
    end = html.index("<!-- /ctrl:matrix -->")
    html = html[:start] + "\n            " + matrix_html(rounds) + "\n            " + html[end:]
    path.write_text(html)


# --------------------------------------------------------------------------- chapters
CHAPTERS = [("data", "01", "Data &amp; research"), ("market-dynamics", "02", "Market dynamics &amp; alpha"),
            ("inventory-risk", "03", "Inventory, portfolio &amp; risk"), ("execution-backtesting", "04", "Execution, orders &amp; backtests")]


def migrate_chapters():
    for slug, no, label in CHAPTERS:
        path = CTRL / slug / "index.html"
        html = path.read_text()
        title = re.search(r"<title>(.*?) \| Tomorrow Library</title>", html).group(1)
        while "&amp;" in title or "&#" in title:
            title = unescape(title)
        desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
        main = re.search(r'<main class="ctrl-article" id="main">(.*?)</main>', html, re.S).group(1)
        main = re.sub(r'\s*<details class="ctrl-mobile-nav">.*?</details>', "", main, flags=re.S)
        main = re.sub(r'<!-- FUTURE RESOURCES:.*?-->\s*<div class="ctrl-future">.*?</div>\s*</div>\s*</div>', "", main, flags=re.S)
        main = re.sub(r'<p class="eyebrow">Chapter (\d\d) / [^<]*</p>', r'<p class="ctrl-path">ctrl/<b>chapter-\1</b></p>', main)
        main = main.replace('<p class="eyebrow">The core question</p>', '<p class="ctrl-path">core question</p>')
        main = re.sub(r'<p class="eyebrow">A worked example to come</p>', '<p class="ctrl-path">worked example, planned</p>', main)
        main = main.replace('class="lead"', 'class="ctrl-lead"')
        main = main.replace('<small>DATA</small>', '<small>data</small>').replace('<small>READING</small>', '<small>reading</small>').replace('<small>METHOD</small>', '<small>method</small>').replace('<small>CODE</small>', '<small>code</small>')
        main = main.replace("<span>← PREVIOUS</span>", "<span>← previous</span>").replace("<span>NEXT CHAPTER →</span>", "<span>next chapter →</span>").replace("<span>CONTINUE →</span>", "<span>continue →</span>")
        main = main.replace("<small>CASE STUDIES</small>", "<small>case studies</small>")
        main = main.strip("\n")
        page = shell(slug, title, unescape_attr(desc), label, "    " + main.strip(), f"{slug}/index.html", mobile_label=f"Browse the guide, chapter {no} of 04")
        path.write_text(page)


def unescape_attr(s):
    return s.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'")


def main():
    profile, rounds = load()
    build_datasets(profile, rounds)
    build_alphas()
    build_research()
    update_matrix(rounds)
    if "--chapters" in sys.argv:
        migrate_chapters()
    print("CTRL: built datasets, alphas, research and the landing matrix" + (" and re-wrapped chapters" if "--chapters" in sys.argv else ""))


if __name__ == "__main__":
    main()
