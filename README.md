# Blue design update — October 2026

The homepage now uses a wider company-style introduction and soft-to-mid blue surfaces. Lesson and catalogue pages retain the reading navigation. The shared wave mark, blue links, masthead and typography connect the Library to Capital Research and Markets.

The canonical authoring template is tools/build.py. Its rebuilt pages, search index and workbench download are included; future rebuilds preserve this design. The build now creates the download directory if absent.

# Tomorrow Library

An open quantitative reading room connecting foundations, research procedures, code, data, papers and competition work.

Published destination: https://tomorrowlibrary.github.io/

Connected projects: https://tomorrowcapitalresearch.github.io/ and https://tomorrowmarkets.github.io/

## Publish

The root index.html and other generated pages are ready for GitHub Pages. Publish the repository root. No visitor-side Python or backend is required.

For local inspection:

    python -m http.server 8000

Open http://localhost:8000/ in your browser.

## Edit and rebuild

Edited lesson bodies live in content/. Their titles, summaries and categories live in catalogue/lessons.json.

The remaining JSON catalogues are repositories.json, code.json, datasets.json, papers.json, competitions.json, solutions.json and resources.json. site.json contains site-wide metadata.

After an edit:

    python tools/build.py
    python tools/check_site.py

Commit the edited source files and the regenerated HTML, search index, sitemap and workbench ZIP. The build uses the Python standard library. Site styles and interactions are in assets/site.css and assets/site.js.

### Add a lesson

Create content/your-topic.html with the article's body (no page wrapper) and add a corresponding slug, title, category, summary and level to catalogue/lessons.json. Rebuild. The new page is included in global search and the sitemap; add an explicit link from a learning route or relevant lesson.

### Add code

Add an entry to catalogue/code.json with title, category, description, status, source_url and guide_url. Document dependencies, input units, timing assumptions, original attribution and tests. Place a local example under workbench/ only if it belongs to that maintained reference package.

### Add a dataset

Use the on-site publish-data.html guide. An active entry requires a real source_url and download_url, a unique id, title, category and actual licence/reuse terms. Include size_bytes, schema, time_coverage, quality notes, source version and sha256 when verified. A Git-hosted original can additionally record source_commit and blob_sha.

The initial catalogue records original competition and legacy-export files. It does not mirror the larger historical BTC/ETH/XRP collections. Existing data entries have no invented row counts, coverage or reuse permissions.

### Add research

Use catalogue/papers.json. Include source_url, status, a concise description and pdf_url if a shareable PDF exists. Preserve author attribution and distinguish working papers, conjectures and tested empirical results.

### Add a competition or solution

Use competitions.json or solutions.json. Record the official organiser link and edition. A solution should identify whether it is the actual submitted code, a later improvement, a guide or a post-mortem. Only publish a placement when supported by its source. Do not list a podium placement as first place.

## Source collections

The six source repositories are catalogued at their inspected revisions. This is a curated snapshot: it does not automatically publish every later file from those repositories.

The source collections contain historical notes, drafts, third-party references and prototypes. New workbench code is licensed separately under workbench/LICENSE; that licence does not cover external datasets, books, papers or other authors' code.

The original Quant Archive foreword is preserved on foreword.html. The recovery ZIP in the parent delivery package contains the untouched original source.

## Workbench

Download downloads/tomorrow-quant-workbench.zip or open workbench/README.md. It uses numpy/pandas and runs locally. The CLI account simulator is single asset; portfolio helpers are separate building blocks.

The deterministic installation fixture is synthetic. The competition adapter uses midpoint proxies, not exchange fills. Read the package's timing, cost and modelling assumptions before interpreting a result.
