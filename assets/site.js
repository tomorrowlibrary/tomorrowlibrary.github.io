(() => {
  const menu = document.querySelector('[data-menu]');
  const sidebar = document.querySelector('.sidebar');
  menu?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('is-open');
    menu.setAttribute('aria-expanded', String(open));
    menu.textContent = open ? 'Close' : 'Browse';
  });
  const dialog = document.querySelector('#library-search');
  const field = document.querySelector('#search-query');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  const search = () => {
    const terms = field.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const entries = window.LIBRARY_SEARCH || [];
    const matches = terms.length ? entries.map(item => {
      const title = item.title.toLowerCase(), haystack = `${title} ${item.category} ${item.text}`.toLowerCase();
      return {item, score:terms.every(t => haystack.includes(t)) ? terms.reduce((s,t) => s+(title.includes(t)?10:1),0) : 0};
    }).filter(x => x.score).sort((a,b) => b.score-a.score).map(x => x.item) : entries.slice(0,8);
    results.replaceChildren();
    status.textContent = terms.length ? `${matches.length} matching entries` : 'Suggested starting points';
    matches.slice(0,35).forEach(item => {
      const a = document.createElement('a'); a.className = 'search-result'; a.href = item.url;
      const title = document.createElement('strong'); title.textContent = item.title;
      const desc = document.createElement('small'); desc.textContent = `${item.category} · ${item.text.slice(0,130)}`;
      a.append(title,desc); results.append(a);
    });
    if (!matches.length) { const p = document.createElement('p'); p.textContent='No matches. Try “risk”, “features”, “Prosperity” or a repository name.'; results.append(p); }
  };
  const openSearch = () => { if (!dialog) return; dialog.showModal(); search(); field.focus(); };
  document.querySelectorAll('[data-search]').forEach(b => b.addEventListener('click', openSearch));
  document.querySelector('[data-search-close]')?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', event => { if (event.target === dialog) {const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();} });
  field?.addEventListener('input', search);
  document.addEventListener('keydown', event => {
    if (event.key==='/' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName) && !document.activeElement?.isContentEditable && !event.ctrlKey && !event.metaKey) {event.preventDefault();openSearch();}
  });
  document.querySelectorAll('[data-catalogue]').forEach(root => {
    const query = root.querySelector('[data-filter-query]');
    const category = root.querySelector('[data-filter-category]');
    const count = root.querySelector('[data-filter-count]');
    const empty = root.querySelector('[data-filter-empty]');
    const rows = [...root.querySelectorAll('[data-entry]')];
    const update = () => {
      const terms = (query?.value || '').toLowerCase().trim().split(/\s+/).filter(Boolean);
      let total = 0;
      rows.forEach(row => { const show = (!category?.value || row.dataset.category===category.value) && terms.every(t => row.dataset.search.includes(t)); row.hidden=!show;if(show)total++; });
      if(count)count.textContent=`${total} of ${rows.length} entries`;
      if(empty)empty.hidden=Boolean(total);
    };
    query?.addEventListener('input',update);category?.addEventListener('change',update);update();
  });
  const lab = document.querySelector('[data-spread-lab]');
  if(lab){ const update=()=>{const bid=Number(lab.querySelector('#lab-bid').value),ask=Number(lab.querySelector('#lab-ask').value),fee=Number(lab.querySelector('#lab-fee').value);const out=lab.querySelector('output');if(!Number.isFinite(bid)||!Number.isFinite(ask)||!Number.isFinite(fee)||bid<=0||ask<bid||fee<0){out.textContent='Enter positive prices, ask ≥ bid, and a non-negative fee.';return;}const loss=(ask-bid)+(ask+bid)*fee/10000;out.textContent=`Spread: ${(ask-bid).toFixed(4)} · Immediate round-trip loss: ${(loss/ask*100).toFixed(4)}%`;};lab.addEventListener('input',update);update();}
})();
