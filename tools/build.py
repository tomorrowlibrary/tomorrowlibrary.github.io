"""Build a dependency-free GitHub Pages site from edited content and JSON catalogues."""
import json, re, zipfile
from pathlib import Path
from html import escape,unescape
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def read(name): return json.loads((ROOT/"catalogue"/(name+".json")).read_text())
def esc(value): return escape(str(value),quote=True)
def url(value):
    if not isinstance(value,str) or not value or value.startswith("//") or "\\" in value or any(ord(c)<32 for c in value):
        raise ValueError("Invalid URL: "+repr(value))
    parsed=urlsplit(value)
    if parsed.scheme and parsed.scheme not in {"http","https","mailto"}:
        raise ValueError("Unsupported URL scheme: "+value)
    return esc(value)
def a(href,label,cls=""):return f'<a href="{url(href)}"'+(f' class="{esc(cls)}"' if cls else '')+f'>{esc(label)}</a>'
site=read("site")
lessons=read("lessons")
catalogues={key:read(key) for key in ["repositories","code","datasets","papers","competitions","solutions","resources"]}
for key,items in catalogues.items():
    for item in items:
        for field in ["url","source_url","download_url","pdf_url","local_url","guide_url"]:
            if item.get(field):url(item[field])
        if key=="datasets" and not all(item.get(x) for x in ["id","title","source_url","download_url","licence"]):
            raise ValueError("Dataset is missing required metadata.")
groups=[
("Orientation",[("index","The reading room"),("guide","Learning routes"),("repositories","Repository map")]),
("Learn",[("research-process","Research process"),("mathematics","Mathematical foundations"),("stochastic-calculus","Stochastic calculus"),("microstructure","Market microstructure"),("portfolio-risk","Portfolio & risk"),("machine-learning","Models & features"),("backtesting","Backtesting"),("research-engineering","Research engineering")]),
("Build & explore",[("code","Code library"),("workbench","Research workbench"),("data","Data catalogue"),("papers","Papers & research"),("competitions","Competition directory"),("competition-guide","How to compete"),("solutions","Solutions & write-ups"),("resources","Resources")])
]
search_entries=[]
pages=[]
def shell(slug,title,description,body):
    nav=""
    for name,links in groups:
        nav+=f'<div><p class="nav-group">{esc(name)}</p>'
        for path,label in links:
            current=' aria-current="page"' if path==slug else ''
            nav+=f'<a href="{path}.html"{current}>{esc(label)}</a>'
        nav+='</div>'
    nav+='<div class="practice"><p class="nav-group">Put it into practice</p><a href="markets-lab.html">Tomorrow Markets lab ↗</a><a href="contribute.html">Contribute to the Library</a><a href="about.html">About this project</a></div>'
    base=site["base_url"]
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | Tomorrow Library</title><meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(base+('' if slug=='index' else slug+'.html'))}">
<meta property="og:title" content="{esc(title)} | Tomorrow Library"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website">
<link rel="icon" href="assets/logo.png"><link rel="stylesheet" href="assets/site.css">
<script defer src="assets/search-index.js"></script><script defer src="assets/site.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<div class="network"><span class="network-label">A TOMORROW CAPITAL RESEARCH PROJECT</span><nav aria-label="Tomorrow projects"><a href="https://tomorrowcapitalresearch.github.io/">Capital Research</a><a href="index.html" aria-current="page">Library</a><a href="https://tomorrowmarkets.github.io/">Markets ↗</a></nav></div>
<header class="site-head"><a class="brand" href="index.html"><img src="assets/logo.png" alt="" width="34" height="34"><span class="brand-name">Tomorrow Library<small>The quantitative reading room</small></span></a>
<nav class="head-links" aria-label="Quick links"><a href="code.html">Code</a><a href="data.html">Data</a><a href="competitions.html" class="optional">Competitions</a><button type="button" class="search-open" data-search aria-haspopup="dialog">Search the Library <span class="key">/</span></button><button type="button" class="menu-button" data-menu aria-controls="sidebar" aria-expanded="false">Browse</button></nav></header>
<div class="layout"><aside class="sidebar" id="sidebar" aria-label="Library navigation"><nav class="sidebar-inner">{nav}</nav></aside><main class="main" id="main">{body}</main></div>
<footer class="footer"><span>Tomorrow Library · Developed by Tomorrow Capital Research</span><nav aria-label="Footer"><a href="about.html">About</a><a href="contribute.html">Contribute</a><a href="https://github.com/tomorrowlibrary/tomorrowlibrary.github.io">GitHub ↗</a><a href="https://tomorrowmarkets.github.io/">Markets ↗</a></nav></footer>
<dialog id="library-search" class="search-dialog" aria-labelledby="search-title"><div class="search-top"><h2 id="search-title">Find your next reference.</h2><button type="button" class="close-search" data-search-close aria-label="Close search">Close · Esc</button></div><label for="search-query" class="eyebrow">Topics, repositories, code or datasets</label><input id="search-query" type="search" autocomplete="off" placeholder="Try risk, features or Prosperity"><p id="search-status" class="result-count" role="status"></p><div id="search-results" class="search-results"></div></dialog>
</body></html>'''
def save(slug,title,desc,body,category="Library",index=True):
    (ROOT/(slug+".html")).write_text(shell(slug,title,desc,body))
    pages.append(slug)
    if index:
        text=unescape(re.sub(r"\s+"," ",re.sub("<[^>]+>"," ",body))).strip()
        search_entries.append({"title":title,"category":category,"url":slug+".html","text":desc+" "+text[:8000]})
def article_head(category,title,summary,level=None):
    return '<header class="article-head"><p class="eyebrow">'+esc(category)+'</p><h1>'+esc(title)+'</h1><p class="lead">'+esc(summary)+'</p>'+(f'<div class="meta"><span>{esc(level)}</span><span>Tomorrow Library</span></div>' if level else '')+'</header>'

repo_count=len(catalogues["repositories"])
data_count=len(catalogues["datasets"])
home=f'''<section class="hero"><div><p class="eyebrow">An open library for quantitative research</p><h1>For the curious.<br>For the <em>quantitative.</em></h1><p class="lead">Understand the mathematics. Build the tools. Test the idea. A home for quantitative finance, from first principles to reproducible research.</p><div class="actions"><a class="button" href="guide.html">Find your starting point <span>→</span></a><a class="text-link" href="workbench.html">Run a research example →</a></div><div class="meta"><span>{repo_count} connected repositories</span><span>{data_count} original data files</span><span>Open learning & implementation</span></div></div>
<aside class="reading-card"><span class="shelf-label">On the workbench / 001</span><h2>One idea.<br>A complete experiment.</h2><p>Load data, build features, fit a baseline, simulate execution and inspect the risk. Follow the whole research loop in Python.</p><a href="workbench.html">Open the research workbench →</a></aside></section>
<section class="section"><div class="section-heading"><h2>Explore the shelves.</h2><a href="repositories.html">View the source map ↗</a></div><div class="shelves">'''
for i,(title,desc,path) in enumerate([
("Learn","Mathematics, market structure and the habits of careful research.","guide"),
("Code","Reusable pieces for data, features, models, portfolios and risk.","code"),
("Data","Original price, trade and observation files with source links.","data"),
("Research","Frameworks, papers, open questions and working drafts.","papers"),
("Compete","How to prepare, where to compete and what solutions teach.","competitions"),
("Practise","Take a concept into the market and portfolio simulator.","markets-lab")],1):
    home+=f'<a class="shelf" href="{path}.html"><span class="number">0{i}</span><span class="arrow" aria-hidden="true">↗</span><h3>{title}</h3><p>{desc}</p></a>'
home+='</div></section><section class="section"><div class="section-heading"><h2>Start with a question.</h2><a href="research-process.html">The research process →</a></div>'
for i,(title,desc,path) in enumerate([
("What is available at the decision time?","Learn to distinguish observations, forecasts, labels and future information.","data-guide"),
("Does the idea beat a simple baseline?","Build a chronological comparison and account for selection and uncertainty.","research-process"),
("What changes when it has to trade?","Follow positions, fills, fees and the cash/share account.","backtesting")],1):
    home+=f'<div class="list-row"><span class="row-no">0{i}</span><div><h3><a href="{path}.html">{title}</a></h3><p>{desc}</p></div><span class="tag">Read the lesson</span></div>'
home+='</section><section class="section"><div class="section-heading"><h2>Learn from the challenge.</h2><a href="solutions.html">Solutions & write-ups →</a></div><div class="feature-strip"><div><h3>Prepare to compete.</h3><p>Build a valid submission, investigate the market, control inventory and preserve a reproducible result.</p><a class="text-link" href="competition-guide.html">Read the competition handbook →</a></div><div><h3>Study how others solved it.</h3><p>Explore Tomorrow’s round analyses alongside attributed winning and public solutions.</p><a class="text-link" href="solutions.html">Browse the solution collection →</a></div></div></section>'
save("index","The quantitative reading room",site["description"],home)

for lesson in lessons:
    slug=lesson["slug"]
    body=(ROOT/"content"/(slug+".html")).read_text()
    headings=[]
    def add_id(match):
        title=match.group(1)
        anchor=re.sub(r"[^a-z0-9]+","-",re.sub("<[^>]+>","",title).lower()).strip("-")
        if any(x[0]==anchor for x in headings):anchor+=f"-{len(headings)}"
        headings.append((anchor,title))
        return f'<h2 id="{anchor}">{title}</h2>'
    body=re.sub(r"<h2>(.*?)</h2>",add_id,body)
    toc='<aside class="toc" aria-label="On this page"><span>ON THIS PAGE</span>'+''.join(a("#"+key,re.sub("<[^>]+>","",title)) for key,title in headings)+'</aside>'
    tail='<nav class="next-reading" aria-label="Continue reading"><a href="guide.html">← Learning routes</a><a href="workbench.html">Research workbench →</a></nav>'
    save(slug,lesson["title"],lesson["summary"],article_head(lesson["category"],lesson["title"],lesson["summary"],lesson["level"])+f'<div class="article-grid"><article class="prose">{body}{tail}</article>{toc}</div>',lesson["category"])

intro={
"repositories":("Six repositories. One source map.","The source collections retain their own histories. The Library gives each an entry point, a topic and a clear maturity label."),
"code":("Code you can inspect.","Start with the runnable workbench, then explore earlier source implementations in their original context."),
"papers":("Research, with its status attached.","Read the framework, inspect the assumptions and distinguish provisional conjectures from established results."),
"competitions":("Find a challenge. Build the skills.","A directory of organisers and historical practice material. Check each organiser for dates, eligibility and current rules."),
"solutions":("Study the reasoning behind the result.","Tomorrow’s guides and round analyses, published winning write-ups, and attributed public submissions."),
"resources":("A collection worth returning to.","Reading lists, lectures, code references and the original archive’s community directory.")
}
for name in intro:
    title,summary=intro[name]
    items=catalogues[name]
    categories=sorted({str(x.get("category","Source collection")) for x in items})
    body=article_head(name.replace("-"," ").title(),title,summary)
    if name=="code":body+='<div class="actions"><a class="button" href="downloads/tomorrow-quant-workbench.zip" download>Download the workbench ↓</a><a class="text-link" href="workbench.html">Installation & documentation →</a></div>'
    if name=="solutions":body+='<div class="callout">The author’s published material in the linked snapshot contains guides and round analyses. Final submitted bot files are not catalogued here yet. The external first-place entries are explicitly labelled; podium and other public solutions are listed separately.</div>'
    if name=="papers":body+='<p class="section-intro">Tomorrow’s framework is under development. Draft labels describe its status and do not claim peer review or empirical confirmation.</p>'
    if name=="competitions":body+='<div class="actions"><a class="button" href="competition-guide.html">How to compete →</a><a class="text-link" href="solutions.html">Solutions & write-ups →</a></div>'
    body+='<section data-catalogue><div class="filters"><label>Search this collection<input type="search" data-filter-query placeholder="Topic, title or source"></label>'
    if len(categories)>1:body+='<label>Collection<select data-filter-category><option value="">All collections</option>'+''.join(f'<option>{esc(c)}</option>' for c in categories)+'</select></label>'
    body+='</div><p class="result-count" data-filter-count></p>'
    for item in items:
        cat=str(item.get("category","Source collection"))
        title=item.get("title",item.get("name",""))
        desc=item["description"]
        status=item.get("status","Source")
        tags=" ".join(item.get("tags",[]))
        search=" ".join(str(item.get(k,"")) for k in ["title","name","description","category","detail","status"])+" "+tags
        body+=f'<article class="catalogue-item" data-entry data-category="{esc(cat)}" data-search="{esc(search.lower())}"><span class="tag'+(' draft' if 'draft' in status.lower() else ' source' if 'Historical' in status else '')+'">'+esc(status)+'</span><h2>'+esc(title)+'</h2><p>'+esc(desc)+'</p>'
        if item.get("detail"):body+='<p class="data-file">'+esc(item["detail"])+'</p>'
        body+='<div class="item-links">'
        body+=a(item.get("source_url",item.get("url")),"Open source ↗")
        if item.get("pdf_url"):body+=a(item["pdf_url"],"Original PDF ↗")
        if item.get("guide_url"):body+=a(item["guide_url"],"Read the guide →")
        if item.get("local_url"):body+=a(item["local_url"],"Preparation guide →")
        body+='</div>'
        if name=="repositories":body+='<div class="meta"><span>'+esc(tags)+'</span><span>Snapshot '+esc(item["snapshot_date"])+' · '+esc(item["commit"][:8])+'</span></div>'
        if item.get("attribution"):body+='<p class="index-note">'+esc(item["attribution"])+'</p>'
        body+='</article>'
        search_entries.append({"title":title,"category":name.title(),"url":item.get("source_url",item.get("url")),"text":desc+" "+search})
    body+='<p class="empty" data-filter-empty hidden>No entries match those filters. Try another term or collection.</p></section>'
    save(name,intro[name][0],summary,body,category="Catalogue",index=False)

datasets=catalogues["datasets"]
categories=sorted({x["category"] for x in datasets})
body=article_head("Data catalogue","Data for the next experiment.",f'{len(datasets)} original public CSV files, linked to captured source revisions. Browse by edition or file type, inspect the source and open the raw file.')
body+='<div class="actions"><a class="button" href="data-guide.html">Read the data guide →</a><a class="text-link" href="publish-data.html">Add a dataset →</a><a class="text-link" href="catalogue/datasets.json">Download the catalogue JSON ↓</a></div><div class="callout">Source-file links preserve the original archive. Dataset reuse terms are not recorded there; check the source before redistributing. File sizes come from the repository snapshot. Coverage, row counts and quality checks are only stated when verified.</div>'
body+='<section data-catalogue><div class="filters"><label>Find a file<input type="search" data-filter-query placeholder="Round, edition, prices or trades"></label><label>Collection<select data-filter-category><option value="">All collections</option>'+''.join(f'<option>{esc(c)}</option>' for c in categories)+'</select></label></div><p class="result-count" data-filter-count></p><div class="table-wrap"><table class="data-table"><thead><tr><th scope="col">Original file</th><th scope="col">Collection / type</th><th scope="col">Size</th><th scope="col">Access</th></tr></thead><tbody>'
for d in datasets:
    fields=" ".join(str(d.get(k,"")) for k in ["title","category","kind","source_repo","source_path","quality"])
    body+=f'<tr data-entry data-category="{esc(d["category"])}" data-search="{esc(fields.lower())}"><td><strong class="data-file">{esc(d["title"])}</strong><br><small>{esc(d["source_repo"])} · {esc(d.get("source_commit","")[:8])}</small>'
    if d["category"]=="Legacy market exports":body+='<br><span class="tag draft">Legacy export</span>'
    body+='</td><td>'+esc(d["category"])+'<br><small>'+esc(d["kind"])+'</small></td><td>'+f'{d["size_bytes"]/1024/1024:.2f} MB'+'</td><td>'+a(d["download_url"],"Raw CSV ↗")+'<br>'+a(d["source_url"],"Source & file history ↗")+'</td></tr>'
    search_entries.append({"title":d["title"],"category":"Dataset","url":d["source_url"],"text":fields})
body+='</tbody></table></div><p class="empty" data-filter-empty hidden>No files match. Try another edition or a shorter name.</p></section><section class="section"><h2>Bring a larger collection.</h2><p class="section-intro">The longer historical market collections can be added as versioned downloads, with a schema, provenance and reuse terms. The catalogue supports remote dataset files, so the website does not need to contain the whole collection.</p><a class="text-link" href="publish-data.html">Follow the dataset publication guide →</a></section>'
save("data","Data for the next experiment.","Original competition and legacy market-data files with captured source revisions, sizes and raw-file access.",body,"Data",index=False)

# Preserve the original author-provided foreword as an explicitly historical page.
foreword=ROOT/"content/foreword.html"
if foreword.exists():
    save("foreword","The original foreword.","A personal essay preserved from Tomorrow Quant Archive.",article_head("Historical archive","The original foreword.","A personal essay preserved from Tomorrow Quant Archive, separate from the edited learning material.")+'<article class="prose">'+foreword.read_text()+'</article>',"Historical essay",index=False)
save("404","That page is not on this shelf.","Find a lesson, catalogue or repository.",article_head("404","That page is not on this shelf.","Browse the learning routes or search the Library.")+'<div class="actions"><a class="button" href="index.html">Back to the reading room →</a><a class="text-link" href="guide.html">Learning routes →</a></div>',index=False)
# Global search also indexes catalogue pages themselves.
for slug in list(intro)+["data"]:
    search_entries.insert(0,{"title":intro[slug][0] if slug in intro else "Data catalogue","category":"Catalogue","url":slug+".html","text":intro[slug][1] if slug in intro else "Download original prices trades observations datasets"})
(ROOT/"assets/search-index.js").write_text("window.LIBRARY_SEARCH = "+json.dumps(search_entries,ensure_ascii=False).replace("<",r"\u003c")+";\n")
(ROOT/".nojekyll").write_text("")
(ROOT/"robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: "+site["base_url"]+"sitemap.xml\n")
(ROOT/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+esc(site["base_url"]+('' if slug=='index' else slug+'.html'))+'</loc></url>' for slug in pages if slug!="404")+'</urlset>\n')
(ROOT/"workbench/data-catalogue.json").write_text(json.dumps(datasets,indent=2,ensure_ascii=False)+"\n")
with zipfile.ZipFile(ROOT/"downloads/tomorrow-quant-workbench.zip","w",zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((ROOT/"workbench").rglob("*")):
        if path.is_file() and not any(part in {"__pycache__","results",".venv","data"} for part in path.relative_to(ROOT/"workbench").parts) and path.suffix!=".pyc":
            archive.write(path,Path("tomorrow-quant-workbench")/path.relative_to(ROOT/"workbench"))
print(f"Built {len(pages)} pages, {len(search_entries)} search entries and the workbench download.")
