/* Ctrl+Alt+DefeatTheMarket — interactive pieces for the CTRL guide.
   1. The hero film: a small simulated exchange that runs one Prosperity-style
      timestep loop (makers quote, takers trade, your bot takes and quotes,
      more takers arrive, the book clears). Synthetic order flow, no real data.
   2. Keycaps that react to the real Ctrl and Alt keys, and a one-off wordmark decode.
   3. Copy buttons for code blocks.
   Everything degrades to static content without JavaScript, and motion is
   skipped when the reader prefers reduced motion. */
(() => {
  'use strict';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------------- keycaps + wordmark ---------------- */
  const keyEls = { Control: $('[data-key="ctrl"]'), Alt: $('[data-key="alt"]') };
  const setKey = (name, down) => { const el = keyEls[name]; if (el) el.classList.toggle('is-down', down); };
  window.addEventListener('keydown', (e) => setKey(e.key, true));
  window.addEventListener('keyup', (e) => setKey(e.key, false));
  window.addEventListener('blur', () => { setKey('Control', false); setKey('Alt', false); });

  const word = $('[data-decode]');
  if (word && !reduceMotion && 'IntersectionObserver' in window) {
    const finalText = word.textContent;
    const glyphs = '0123456789$%#&@<>/=+';
    let played = false;
    const play = () => {
      played = true;
      const box = word.getBoundingClientRect();
      word.style.display = 'inline-block';
      word.style.minWidth = Math.ceil(box.width) + 'px';
      const steps = [[0, () => setKey('Control', true)], [170, () => setKey('Alt', true)]];
      steps.forEach(([t, fn]) => setTimeout(fn, t));
      const start = performance.now() + 320;
      const dur = 900;
      const frame = (now) => {
        const p = Math.max(0, Math.min(1, (now - start) / dur));
        const revealed = Math.floor(p * finalText.length);
        let html = '';
        for (let i = 0; i < finalText.length; i++) {
          if (i < revealed) html += finalText[i];
          else html += '<span class="scramble">' + glyphs[(Math.random() * glyphs.length) | 0] + '</span>';
        }
        word.innerHTML = html;
        if (p < 1) requestAnimationFrame(frame);
        else {
          word.textContent = finalText;
          word.style.minWidth = '';
          setTimeout(() => { setKey('Control', false); setKey('Alt', false); }, 140);
        }
      };
      requestAnimationFrame(frame);
    };
    const io = new IntersectionObserver((entries) => {
      if (!played && entries.some((en) => en.isIntersecting)) { io.disconnect(); setTimeout(play, 150); }
    }, { threshold: 0.6 });
    io.observe(word);
  }

  /* ---------------- copy buttons ---------------- */
  $$('[data-copy]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const target = document.getElementById(btn.getAttribute('data-copy'));
      if (!target) return;
      const label = btn.textContent;
      try {
        await navigator.clipboard.writeText(target.innerText);
        btn.textContent = 'Copied';
      } catch (err) {
        btn.textContent = 'Select and copy';
      }
      setTimeout(() => { btn.textContent = label; }, 1600);
    });
  });

  /* ---------------- the film ---------------- */
  const film = $('[data-film]');
  if (!film) return;
  const canvas = $('[data-film-canvas]', film);
  const ctx = canvas.getContext('2d');
  const ui = {
    cmd: $('[data-film-cmd]', film), clock: $('[data-film-clock]', film), log: $('[data-film-log]', film),
    tape: $('[data-film-tape]', film), progress: $('[data-film-progress]', film), time: $('[data-film-time]', film),
    toggle: $('[data-film-toggle]', film), phases: $$('[data-phase]', film), channels: $$('[data-channel]', film),
    pos: $('[data-stat="pos"]', film), pnl: $('[data-stat="pnl"]', film), fills: $('[data-stat="fills"]', film), edge: $('[data-stat="edge"]', film),
  };
  const css = getComputedStyle(film);
  const C = {
    text: css.getPropertyValue('--text').trim() || '#dce8f8', text2: css.getPropertyValue('--text-2').trim() || '#9db2ce',
    text3: css.getPropertyValue('--text-3').trim() || '#7189ab', rule: css.getPropertyValue('--rule').trim() || '#1b2c4a',
    bid: css.getPropertyValue('--bid').trim() || '#0fa3a6', ask: css.getPropertyValue('--ask').trim() || '#ea5079',
    fill: css.getPropertyValue('--fill').trim() || '#bd8b17', ours: css.getPropertyValue('--ours').trim() || '#5b7cf0',
    oursInk: css.getPropertyValue('--ours-ink').trim() || '#a6b9ff', bg: '#081224',
  };
  const MONO = "'IBM Plex Mono', ui-monospace, Menlo, monospace";

  const CHANNELS = [
    { key: 'fixed-fair-value', fair: 10000, kind: 'fixed', takerRate: 0.62, qtyMax: 5, tickMs: 1150 },
    { key: 'slow-drift', fair: 2025.4, kind: 'drift', sigma: 0.34, takerRate: 0.66, qtyMax: 6, tickMs: 1050 },
    { key: 'shock-and-revert', fair: 1968.6, kind: 'shock', sigma: 0.6, jumpP: 0.035, kappa: 0.05, takerRate: 0.7, qtyMax: 6, tickMs: 1050 },
  ];
  const LIMIT = 50;
  const HIST = 64;
  const REEL_MS = 42000;
  const PHASES = [0, 0.16, 0.3, 0.52, 0.86];

  const rnd = (a, b) => a + Math.random() * (b - a);
  const rint = (a, b) => Math.floor(rnd(a, b + 1));
  const gauss = () => { let u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const fmt = (n) => n.toLocaleString('en-GB', { maximumFractionDigits: 0 });
  const signed = (n) => (n > 0 ? '+' : n < 0 ? '−' : '') + fmt(Math.abs(n));

  let ch = 0, S = null, running = !reduceMotion, visible = true, autoCycle = true;
  let reelStart = 0, reelElapsed = 0, lastNow = 0, tickStart = 0, nextPhase = 0;
  let centre = 0, yLo = 0, yHi = 0;
  const logQueue = [], logDone = [];
  let typing = null;

  function reset(index) {
    ch = index;
    const c = CHANNELS[ch];
    S = { t: 0, fair: c.fair, anchor: c.fair, est: c.fair, pos: 0, cash: 0, fills: 0, edgeSum: 0, edgeN: 0, shockLeft: 0,
      bids: [], asks: [], ourBid: null, ourAsk: null, hist: [], flashes: [], cur: null };
    centre = Math.round(c.fair);
    yLo = c.fair - 8; yHi = c.fair + 8;
    logQueue.length = 0; logDone.length = 0; typing = null;
    if (ui.tape) ui.tape.innerHTML = '';
    if (ui.cmd) ui.cmd.innerHTML = 'python trader.py --sim <b>' + c.key + '</b>';
    ui.channels.forEach((b, i) => b.setAttribute('aria-pressed', String(i === ch)));
    reelElapsed = 0;
    pushLog('t-dim', 'loading ' + c.key + ' · limit ' + LIMIT + ' · orders live for one timestep');
    updateStats();
  }

  /* ---- exchange: one timestep, split into phases ---- */
  function makersQuote() {
    const c = CHANNELS[ch];
    S.t += 1;
    if (c.kind === 'drift') S.fair += gauss() * c.sigma;
    if (c.kind === 'shock') {
      S.anchor += gauss() * 0.12;
      S.fair += c.kappa * (S.anchor - S.fair) + gauss() * c.sigma;
      if (Math.random() < c.jumpP) { S.fair += (Math.random() < 0.5 ? -1 : 1) * rnd(8, 17); S.shockLeft = 4; }
    }
    const bids = [], asks = [];
    if (c.kind === 'fixed') {
      bids.push({ p: 9995, v: rint(20, 30) }); asks.push({ p: 10005, v: rint(20, 30) });
      if (Math.random() < 0.5) bids.push({ p: 9996, v: rint(1, 4) });
      if (Math.random() < 0.5) asks.push({ p: 10004, v: rint(1, 4) });
      const misBid = Math.random() < 0.09, misAsk = !misBid && Math.random() < 0.09;
      if (misBid) bids.push({ p: 10002, v: rint(1, 4) });
      else if (Math.random() < 0.14) asks.push({ p: 10002, v: rint(1, 5) });
      if (misAsk) asks.push({ p: 9998, v: rint(1, 4) });
      else if (Math.random() < 0.14) bids.push({ p: 9998, v: rint(1, 5) });
    } else {
      const w = S.shockLeft > 0 ? 3 : 1.5;
      if (S.shockLeft > 0) S.shockLeft -= 1;
      const bw = Math.floor(S.fair - w), aw = Math.ceil(S.fair + w);
      bids.push({ p: bw, v: rint(20, 30) }); asks.push({ p: aw === bw ? aw + 1 : aw, v: rint(20, 30) });
      if (Math.random() < 0.22) bids.push({ p: bw - 1, v: rint(18, 28) });
      if (Math.random() < 0.22) asks.push({ p: aw + 1, v: rint(18, 28) });
      // occasionally a small order sits on the wrong side of fair: free edge for a taker
      const misAsk = Math.floor(S.fair) - 1, misBid = Math.ceil(S.fair) + 1;
      if (Math.random() < 0.07 && misAsk > bw) asks.push({ p: misAsk, v: rint(1, 4) });
      else if (Math.random() < 0.07 && misBid < aw) bids.push({ p: misBid, v: rint(1, 4) });
    }
    S.bids = merge(bids, -1); S.asks = merge(asks, 1);
    S.ourBid = S.ourAsk = null;
    S.cur = { t: S.t, fair: S.fair, buys: [], sells: [], mkt: [] };
  }
  function merge(levels, dir) {
    const m = new Map();
    levels.forEach((l) => m.set(l.p, (m.get(l.p) || 0) + l.v));
    return Array.from(m, ([p, v]) => ({ p, v })).sort((a, b) => dir * (a.p - b.p));
  }
  function wallMid() {
    const wb = S.bids.reduce((a, b) => (b.v > a.v ? b : a), S.bids[0]);
    const wa = S.asks.reduce((a, b) => (b.v > a.v ? b : a), S.asks[0]);
    return wb && wa ? (wb.p + wa.p) / 2 : S.fair;
  }
  function trade(side, qty, price, you) {
    S.cur.mkt.push(price);
    addTape(side, qty, price, you);
  }
  function earlyTakers() {
    if (Math.random() < 0.28) {
      const buy = Math.random() < 0.5;
      const book = buy ? S.asks : S.bids;
      if (book.length) { const q = Math.min(book[0].v, rint(1, 3)); book[0].v -= q; trade(buy ? 'b' : 's', q, book[0].p, false); flash(book[0].p, C.fill); if (!book[0].v) book.shift(); }
    }
  }
  function botActs() {
    const c = CHANNELS[ch];
    S.est = c.kind === 'fixed' ? 10000 : wallMid();
    const est = S.est;
    let took = false;
    while (S.asks.length && S.asks[0].p < est && S.pos < LIMIT) {
      const l = S.asks[0]; const q = Math.min(l.v, LIMIT - S.pos);
      fillUs(+1, q, l.p, est, 'take'); l.v -= q; took = true; if (!l.v) S.asks.shift();
    }
    while (S.bids.length && S.bids[0].p > est && S.pos > -LIMIT) {
      const l = S.bids[0]; const q = Math.min(l.v, LIMIT + S.pos);
      fillUs(-1, q, l.p, est, 'take'); l.v -= q; took = true; if (!l.v) S.bids.shift();
    }
    const bb = S.bids.length ? S.bids[0].p : Math.floor(est) - 3;
    const ba = S.asks.length ? S.asks[0].p : Math.ceil(est) + 3;
    let bid = Math.min(bb + 1, Math.ceil(est) - 1);
    let ask = Math.max(ba - 1, Math.floor(est) + 1);
    let note = '';
    if (S.pos > 15) { bid -= 1; note = ' skew −1'; }
    if (S.pos < -15) { ask += 1; note = ' skew +1'; }
    if (S.pos > 32) { ask = Math.ceil(est); note = ' flatten at fair'; }
    if (S.pos < -32) { bid = Math.floor(est); note = ' flatten at fair'; }
    const bq = Math.max(0, Math.min(10, LIMIT - S.pos)), aq = Math.max(0, Math.min(10, LIMIT + S.pos));
    S.ourBid = bq ? { p: bid, v: bq } : null;
    S.ourAsk = aq ? { p: ask, v: aq } : null;
    const fairTxt = c.kind === 'fixed' ? 'anchor 10000' : 'wall_mid ' + est.toFixed(1);
    if (!took) pushLog('t-quote', 'QUOTE ' + fairTxt + ' → bid ' + (S.ourBid ? S.ourBid.v + '@' + bid : '—') + '  ask ' + (S.ourAsk ? S.ourAsk.v + '@' + ask : '—') + note);
    if (Math.abs(S.pos) > 32) pushLog('t-risk', 'RISK  position ' + signed(S.pos) + ' near limit ' + LIMIT + ' → quote at fair to unwind');
  }
  function lateTakers() {
    const c = CHANNELS[ch];
    let n = Math.random() < c.takerRate ? 1 : 0;
    if (Math.random() < c.takerRate / 3) n += 1;
    for (let k = 0; k < n; k++) {
      const lean = Math.max(-0.25, Math.min(0.25, (S.fair - S.est) * 0.08));
      const buy = Math.random() < 0.5 + lean;
      let q = rint(1, c.qtyMax);
      const limitPx = buy ? Math.ceil(S.fair) + 6 : Math.floor(S.fair) - 6;
      for (let guard = 0; guard < 3 && q > 0; guard++) {
        const ours = buy ? S.ourAsk : S.ourBid;
        const book = buy ? S.asks : S.bids;
        const best = book[0];
        const oursBetter = ours && ours.v > 0 && (!best || (buy ? ours.p < best.p : ours.p > best.p));
        const lvl = oursBetter ? ours : best;
        if (!lvl || (buy ? lvl.p > limitPx : lvl.p < limitPx)) break;
        const take = Math.min(q, lvl.v);
        if (oursBetter) fillUs(buy ? -1 : +1, take, lvl.p, S.est, 'fill');
        else { trade(buy ? 'b' : 's', take, lvl.p, false); flash(lvl.p, C.fill); }
        lvl.v -= take; q -= take;
        if (!oursBetter && !lvl.v) book.shift();
      }
    }
  }
  function fillUs(dir, qty, price, est, why) {
    S.pos += dir * qty; S.cash -= dir * qty * price; S.fills += 1;
    const edge = dir > 0 ? est - price : price - est;
    S.edgeSum += edge * qty; S.edgeN += qty;
    (dir > 0 ? S.cur.buys : S.cur.sells).push(price);
    addTape(dir > 0 ? 'b' : 's', qty, price, true);
    flash(price, C.fill, true);
    const verb = dir > 0 ? 'bought' : 'sold';
    if (why === 'take') pushLog('t-take', 'TAKE  ' + verb + ' ' + qty + ' @ ' + price + '  (' + (dir > 0 ? 'ask below' : 'bid above') + ' fair, edge ' + signed(edge) + ')');
    else pushLog('t-fill', 'FILL  ' + verb + ' ' + qty + ' @ ' + price + '  edge ' + signed(edge) + '  pos ' + signed(S.pos));
  }
  function clearBook() {
    const bb = S.bids.length ? S.bids[0].p : null, ba = S.asks.length ? S.asks[0].p : null;
    S.hist.push({ t: S.t, bb, ba, fair: S.fair, ob: S.ourBid ? S.ourBid.p : null, oa: S.ourAsk ? S.ourAsk.p : null, buys: S.cur.buys, sells: S.cur.sells, mkt: S.cur.mkt });
    if (S.hist.length > HIST + 2) S.hist.shift();
    updateStats();
  }
  function flash(price, color, strong) { S.flashes.push({ p: price, color, born: performance.now(), strong: !!strong }); }

  /* ---- side panels ---- */
  function addTape(side, qty, price, you) {
    if (!ui.tape) return;
    const li = document.createElement('li');
    li.innerHTML = '<span class="' + side + '">' + (side === 'b' ? '▲' : '▼') + '</span><span>' + qty + ' @ ' + fmt(price) + '</span><span class="' + (you ? 'you' : 'who') + '">' + (you ? 'you' : 'mkt') + '</span>';
    ui.tape.prepend(li);
    while (ui.tape.children.length > 11) ui.tape.lastChild.remove();
  }
  function updateStats() {
    if (!S) return;
    const pnl = S.cash + S.pos * S.fair;
    if (ui.pos) ui.pos.textContent = signed(S.pos);
    if (ui.pnl) ui.pnl.textContent = signed(Math.round(pnl));
    if (ui.fills) ui.fills.textContent = fmt(S.fills);
    if (ui.edge) ui.edge.textContent = S.edgeN ? (S.edgeSum / S.edgeN).toFixed(2) : '—';
    if (ui.clock) ui.clock.textContent = 'tick ' + String(S.t).padStart(4, '0') + ' / ts ' + String(S.t * 100).padStart(6, '0');
  }
  function pushLog(cls, text) {
    const line = '[' + String(S ? S.t : 0).padStart(4, '0') + '] ' + text;
    logQueue.push({ cls, text: line });
    while (logQueue.length > 5) logQueue.shift();
  }
  function renderLog(instant) {
    if (!ui.log) return;
    if (instant) { while (logQueue.length) logDone.push(logQueue.shift()); typing = null; }
    else {
      if (!typing && logQueue.length) typing = { ...logQueue.shift(), n: 0 };
      if (typing) {
        const backlog = logQueue.reduce((a, l) => a + l.text.length, 0);
        typing.n += Math.max(2, Math.ceil(backlog / 40));
        if (typing.n >= typing.text.length) { logDone.push(typing); typing = null; }
      }
    }
    while (logDone.length > 4) logDone.shift();
    const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    let html = logDone.map((l) => '<span class="' + l.cls + '">' + esc(l.text) + '</span>').join('\n');
    if (typing) html += (html ? '\n' : '') + '<span class="' + typing.cls + '">' + esc(typing.text.slice(0, typing.n)) + '</span><span class="caret"></span>';
    else if (!instant) html += '<span class="caret"></span>';
    ui.log.innerHTML = html;
  }

  /* ---- drawing ---- */
  let W = 0, H = 0, dpr = 1;
  function resize() {
    const r = canvas.getBoundingClientRect();
    dpr = Math.min(2, window.devicePixelRatio || 1);
    W = Math.max(280, r.width); H = Math.max(220, r.height);
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function draw(now, frac) {
    ctx.clearRect(0, 0, W, H);
    const narrow = W < 560;
    const ladderW = narrow ? Math.round(W * 0.56) : Math.min(380, Math.max(270, Math.round(W * 0.36)));
    drawLadder(now, 0, 0, ladderW, H, narrow);
    drawChart(frac, ladderW, 0, W - ladderW, H, narrow);
  }
  function drawLadder(now, x0, y0, w, h, narrow) {
    let rows = Math.max(11, Math.min(17, Math.floor((h - 40) / 20.5)));
    if (rows % 2 === 0) rows -= 1;
    const half = (rows - 1) / 2;
    const target = CHANNELS[ch].kind === 'fixed' ? 10000 : Math.round(S.est);
    if (Math.abs(target - centre) > 2) centre += Math.sign(target - centre);
    const top = 30, rh = (h - top - 10) / rows;
    const pw = narrow ? 58 : 76;
    const cx = x0 + w / 2;
    ctx.font = '11px ' + MONO; ctx.fillStyle = C.text3; ctx.textBaseline = 'middle';
    ctx.textAlign = 'right'; ctx.fillText('bid', cx - pw / 2 - 8, 15);
    ctx.textAlign = 'center'; ctx.fillText('price', cx, 15);
    ctx.textAlign = 'left'; ctx.fillText('ask', cx + pw / 2 + 8, 15);
    const vmax = 34, barW = (w - pw) / 2 - (narrow ? 34 : 30);
    const bidMap = new Map(S.bids.map((l) => [l.p, l.v])), askMap = new Map(S.asks.map((l) => [l.p, l.v]));
    for (let i = 0; i < rows; i++) {
      const price = centre + half - i;
      const y = top + i * rh;
      const yc = y + rh / 2;
      ctx.fillStyle = i % 2 ? 'rgba(255,255,255,0.012)' : 'rgba(255,255,255,0.028)';
      ctx.fillRect(x0 + 6, y + 1, w - 12, rh - 2);
      S.flashes.forEach((f) => {
        if (f.p !== price) return;
        const a = 1 - (now - f.born) / (f.strong ? 900 : 650);
        if (a > 0) { ctx.fillStyle = hexA(f.color, (f.strong ? 0.34 : 0.2) * a); ctx.fillRect(x0 + 6, y + 1, w - 12, rh - 2); }
      });
      const bv = bidMap.get(price), av = askMap.get(price);
      // when your order joins a maker level, push the maker's bar outward so both stay visible
      const bo = S.ourBid && S.ourBid.v > 0 && S.ourBid.p === price ? 50 : 0;
      const ao = S.ourAsk && S.ourAsk.v > 0 && S.ourAsk.p === price ? 50 : 0;
      if (bv) { const bw = Math.max(3, (barW - bo) * Math.min(1, bv / vmax)); ctx.fillStyle = hexA(C.bid, 0.55); ctx.fillRect(cx - pw / 2 - 6 - bo - bw, y + 4, bw, rh - 8); ctx.fillStyle = C.text; ctx.textAlign = 'right'; ctx.font = '12px ' + MONO; ctx.fillText(String(bv), cx - pw / 2 - 10 - bo - bw, yc); }
      if (av) { const aw = Math.max(3, (barW - ao) * Math.min(1, av / vmax)); ctx.fillStyle = hexA(C.ask, 0.55); ctx.fillRect(cx + pw / 2 + 6 + ao, y + 4, aw, rh - 8); ctx.fillStyle = C.text; ctx.textAlign = 'left'; ctx.font = '12px ' + MONO; ctx.fillText(String(av), cx + pw / 2 + 10 + ao + aw, yc); }
      ['ourBid', 'ourAsk'].forEach((k) => {
        const o = S[k]; if (!o || o.p !== price || o.v <= 0) return;
        const left = k === 'ourBid';
        const bx = left ? cx - pw / 2 - 6 - 46 : cx + pw / 2 + 6;
        ctx.strokeStyle = C.ours; ctx.lineWidth = 1.5; ctx.setLineDash([]);
        ctx.strokeRect(bx + 0.5, y + 3.5, 46, rh - 7);
        ctx.fillStyle = C.oursInk; ctx.textAlign = 'center'; ctx.font = '11px ' + MONO;
        ctx.fillText('you ' + o.v, bx + 23, yc);
      });
      ctx.textAlign = 'center'; ctx.font = (price === Math.round(S.est) ? '500 ' : '') + '12.5px ' + MONO;
      ctx.fillStyle = bv ? C.text : av ? C.text : C.text3;
      ctx.fillText(fmt(price), cx, yc);
    }
    const fy = top + (centre + half - S.fair) * rh + rh / 2;
    if (fy > top && fy < h - 8) {
      ctx.strokeStyle = 'rgba(220,232,248,0.55)'; ctx.lineWidth = 1; ctx.setLineDash([3, 4]);
      ctx.beginPath();
      ctx.moveTo(x0 + 6, fy); ctx.lineTo(cx - pw / 2 + 4, fy);
      ctx.moveTo(cx + pw / 2 - 4, fy); ctx.lineTo(x0 + w - 34, fy);
      ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = C.text2; ctx.font = '10.5px ' + MONO; ctx.textAlign = 'right'; ctx.fillText('fair', x0 + w - 6, fy);
    }
    S.flashes = S.flashes.filter((f) => now - f.born < 1000);
    ctx.strokeStyle = C.rule; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x0 + w - 0.5, 0); ctx.lineTo(x0 + w - 0.5, h); ctx.stroke();
  }
  function drawChart(frac, x0, y0, w, h, narrow) {
    const pad = { l: 14, r: narrow ? 46 : 58, t: 34, b: 18 };
    const span = narrow ? 30 : HIST;
    const pts = S.hist.slice(-(span + 2));
    if (!pts.length) return;
    let lo = Infinity, hi = -Infinity;
    pts.slice(-span).forEach((p) => { [p.bb, p.ba, p.fair].forEach((v) => { if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); } }); });
    if (CHANNELS[ch].kind === 'fixed') { lo = 9993; hi = 10007; } else { lo -= 2; hi += 2; if (hi - lo < 12) { const m = (hi + lo) / 2; lo = m - 6; hi = m + 6; } }
    yLo += (lo - yLo) * 0.08; yHi += (hi - yHi) * 0.08;
    const X = (i) => x0 + pad.l + ((i + 1 - frac) / span) * (w - pad.l - pad.r);
    const Y = (v) => y0 + pad.t + (1 - (v - yLo) / (yHi - yLo)) * (h - pad.t - pad.b);
    const off = span - pts.length;
    ctx.save();
    ctx.beginPath(); ctx.rect(x0 + pad.l, y0 + pad.t - 6, w - pad.l - pad.r, h - pad.t - pad.b + 12); ctx.clip();
    const step = niceStep(yHi - yLo);
    ctx.strokeStyle = 'rgba(121,176,255,0.07)'; ctx.lineWidth = 1;
    for (let v = Math.ceil(yLo / step) * step; v <= yHi; v += step) { const y = Math.round(Y(v)) + 0.5; ctx.beginPath(); ctx.moveTo(x0 + pad.l, y); ctx.lineTo(x0 + w - pad.r, y); ctx.stroke(); }
    const slot = (w - pad.l - pad.r) / span;
    // shaded spread: one rectangle per timestep between best bid and best ask
    ctx.fillStyle = 'rgba(157,178,206,0.09)';
    pts.forEach((p, i) => { if (p.bb == null || p.ba == null) return; const x = X(i + off) - slot / 2; ctx.fillRect(x, Y(p.ba), slot + 0.5, Y(p.bb) - Y(p.ba)); });
    const line = (key, color, dash, width, stepped) => {
      ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.beginPath();
      let s = false, py = 0;
      pts.forEach((p, i) => {
        const v = p[key]; if (v == null) { s = false; return; }
        const x = X(i + off), y = Y(v);
        if (!s) { ctx.moveTo(x - (stepped ? slot / 2 : 0), y); s = true; }
        else if (stepped) { ctx.lineTo(x - slot / 2, py); ctx.lineTo(x - slot / 2, y); }
        else ctx.lineTo(x, y);
        if (stepped) ctx.lineTo(x + slot / 2, y);
        py = y;
      });
      ctx.stroke(); ctx.setLineDash([]);
    };
    line('bb', C.bid, [], 2, true); line('ba', C.ask, [], 2, true); line('fair', 'rgba(220,232,248,0.6)', [3, 4], 1, false);
    ctx.strokeStyle = C.ours; ctx.lineWidth = 2;
    pts.forEach((p, i) => { const x = X(i + off); [p.ob, p.oa].forEach((v) => { if (v == null) return; ctx.beginPath(); ctx.moveTo(x - 3, Y(v)); ctx.lineTo(x + 3, Y(v)); ctx.stroke(); }); });
    pts.forEach((p, i) => { const x = X(i + off); p.mkt.forEach((v) => { ctx.fillStyle = C.fill; ctx.beginPath(); ctx.arc(x, Y(v), 2.2, 0, Math.PI * 2); ctx.fill(); }); });
    pts.forEach((p, i) => {
      const x = X(i + off);
      p.buys.forEach((v) => tri(x, Y(v), true));
      p.sells.forEach((v) => tri(x, Y(v), false));
    });
    ctx.restore();
    ctx.font = '11px ' + MONO; ctx.fillStyle = C.text3; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    for (let v = Math.ceil(yLo / step) * step; v <= yHi; v += step) { const y = Y(v); if (y > pad.t - 4 && y < h - pad.b + 4) ctx.fillText(fmt(v), x0 + w - pad.r + 8, y); }
    legend(x0 + pad.l, 15, narrow, x0 + w - 8);
  }
  function tri(x, y, up) {
    ctx.beginPath();
    if (up) { ctx.moveTo(x, y - 6); ctx.lineTo(x + 5.5, y + 4); ctx.lineTo(x - 5.5, y + 4); }
    else { ctx.moveTo(x, y + 6); ctx.lineTo(x + 5.5, y - 4); ctx.lineTo(x - 5.5, y - 4); }
    ctx.closePath(); ctx.lineWidth = 2; ctx.strokeStyle = C.bg; ctx.stroke();
    ctx.fillStyle = up ? C.bid : C.ask; ctx.fill();
  }
  function legend(x, y, narrow, maxX) {
    const items = narrow
      ? [['l', C.bid, 'bid'], ['l', C.ask, 'ask']]
      : [['l', C.bid, 'best bid'], ['l', C.ask, 'best ask'], ['d', 'rgba(220,232,248,0.7)', 'fair'], ['q', C.ours, 'your quotes'], ['t', C.bid, 'your fills'], ['o', C.fill, 'trades']];
    ctx.font = '11px ' + MONO; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    let full = false;
    items.forEach(([k, col, label]) => {
      const markW = k === 't' ? 25 : k === 'o' ? 10 : k === 'q' ? 13 : 19;
      if (full || x + markW + ctx.measureText(label).width > maxX) { full = true; return; }
      if (k === 'l' || k === 'd' || k === 'q') { ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.setLineDash(k === 'd' ? [3, 3] : []); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (k === 'q' ? 8 : 14), y); ctx.stroke(); ctx.setLineDash([]); x += k === 'q' ? 13 : 19; }
      if (k === 't') { tri(x + 4, y + 1, true); tri(x + 15, y - 1, false); x += 25; }
      if (k === 'o') { ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x + 3, y, 2.4, 0, Math.PI * 2); ctx.fill(); x += 10; }
      ctx.fillStyle = C.text2; ctx.fillText(label, x, y); x += ctx.measureText(label).width + 16;
    });
  }
  function niceStep(range) { const raw = range / 4; const p = Math.pow(10, Math.floor(Math.log10(raw))); const n = raw / p; return (n < 1.5 ? 1 : n < 3.5 ? 2 : n < 7.5 ? 5 : 10) * p; }
  function hexA(hex, a) { const h = hex.replace('#', ''); const n = parseInt(h.length === 3 ? h.replace(/./g, '$&$&') : h, 16); return 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + a.toFixed(3) + ')'; }

  /* ---- clock ---- */
  const actions = [makersQuote, earlyTakers, botActs, lateTakers, clearBook];
  function setPhase(i) { ui.phases.forEach((li, k) => li.classList.toggle('is-active', k === i)); }
  function stepSync(n) { for (let k = 0; k < n; k++) actions.forEach((fn) => fn()); }
  // The chart scrolls continuously: one slot per timestep, measured from the moment
  // the book clears (the last phase), so a new point never makes the series jump.
  const CLEAR = PHASES[PHASES.length - 1];
  const scrollOf = (frac) => ((frac - CLEAR) + 1) % 1;
  let rafId = 0, lastFrac = CLEAR;
  function loop(now) {
    rafId = 0;
    if (!running || !visible || document.hidden) { lastNow = 0; return; }
    const c = CHANNELS[ch];
    if (!lastNow) { lastNow = now; tickStart = now - lastFrac * c.tickMs; }
    const dt = Math.min(100, now - lastNow); lastNow = now;
    reelElapsed += dt;
    let frac = (now - tickStart) / c.tickMs;
    if (frac >= 1) {
      while (nextPhase < PHASES.length) { actions[nextPhase](); nextPhase += 1; }
      tickStart = now; frac = 0; nextPhase = 0;
    }
    while (nextPhase < PHASES.length && frac >= PHASES[nextPhase]) { actions[nextPhase](); setPhase(nextPhase); nextPhase += 1; }
    lastFrac = frac;
    renderLog(false);
    draw(now, scrollOf(frac));
    if (ui.progress) ui.progress.style.width = Math.min(100, (reelElapsed / REEL_MS) * 100).toFixed(2) + '%';
    if (ui.time) { const s = Math.floor(reelElapsed / 1000); ui.time.textContent = String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
    if (reelElapsed >= REEL_MS) { if (autoCycle) switchTo((ch + 1) % CHANNELS.length, false); else reelElapsed = 0; }
    rafId = requestAnimationFrame(loop);
  }
  function start() { if (!running || rafId) return; lastNow = 0; rafId = requestAnimationFrame(loop); }
  function warm() { stepSync(HIST); S.flashes = []; renderLog(true); draw(performance.now(), 0); setPhase(4); }
  function switchTo(i, byUser) {
    if (byUser) autoCycle = false;
    reset(i); warm();
    tickStart = performance.now() - CLEAR * CHANNELS[ch].tickMs; nextPhase = PHASES.length; lastFrac = CLEAR;
    if (!running) { renderLog(true); draw(performance.now(), 0); }
  }
  function setRunning(on) {
    running = on;
    film.classList.toggle('is-static', !on);
    if (ui.toggle) {
      ui.toggle.setAttribute('aria-label', on ? 'Pause the simulation' : 'Play the simulation');
      ui.toggle.innerHTML = on ? '<svg viewBox="0 0 14 14" aria-hidden="true"><rect x="2" y="1" width="3.6" height="12" rx="1"/><rect x="8.4" y="1" width="3.6" height="12" rx="1"/></svg>' : '<svg viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1.2v11.6c0 .6.6.9 1.1.6l9-5.8c.5-.3.5-.9 0-1.2l-9-5.8C3.6.3 3 .6 3 1.2z"/></svg>';
    }
    if (on) start();
  }

  ui.toggle && ui.toggle.addEventListener('click', () => setRunning(!running));
  ui.channels.forEach((b, i) => b.addEventListener('click', () => switchTo(i, true)));
  if ('ResizeObserver' in window) new ResizeObserver(() => { resize(); if (!running) draw(performance.now(), 0); }).observe(canvas);
  window.addEventListener('resize', () => { resize(); if (!running) draw(performance.now(), 0); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((entries) => { const was = visible; visible = entries[0].isIntersecting; if (visible && !was) start(); }, { threshold: 0.04 }).observe(film);
  }
  document.addEventListener('visibilitychange', () => { if (!document.hidden) start(); });

  resize();
  switchTo(0, false);
  setRunning(running);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => { resize(); if (!running) draw(performance.now(), 0); });
})();
