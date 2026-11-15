# Ctrl+Alt+DefeatTheMarket

The HTML/CSS foundation for Tomorrow Library's IMC Prosperity guide.

## Install this package

Copy the contents of the ZIP into the root of `tomorrowlibrary.github.io`, preserving the folder structure. Merge the files with the existing repository; this is an addition to the site, not a complete replacement. The pages use the existing `assets/site.css` and `assets/wave-mark.svg`.

The generated HTML is ready to serve. No build is necessary to view it. The included catalogue, search index, sitemap and build/check updates keep this addition integrated with the existing site.

When these files are published through your existing GitHub Pages workflow, the route will be:

**Homepage → Compete → IMC Prosperity → `/CTRL/`**

Both the IMC Prosperity heading and its Preparation guide link open CTRL. The existing `/ctrl.html` redirects to `/CTRL/` and includes a visible fallback link. GitHub Pages accepts `/CTRL` and redirects to `/CTRL/`.

| Page | File to edit | Public path |
| --- | --- | --- |
| Main guide | `CTRL/index.html` | `/CTRL/` |
| Data and research | `CTRL/data/index.html` | `/CTRL/data/` |
| Market dynamics and alpha | `CTRL/market-dynamics/index.html` | `/CTRL/market-dynamics/` |
| Inventory, portfolio and risk | `CTRL/inventory-risk/index.html` | `/CTRL/inventory-risk/` |
| Execution, orders and backtests | `CTRL/execution-backtesting/index.html` | `/CTRL/execution-backtesting/` |
| Shared guide styles | `assets/ctrl.css` | — |

## Scope of this version

- A landing page, basic competition overview and four chapter outlines.
- Desktop and mobile navigation, breadcrumbs, previous/next chapter links and native HTML expandable topics.
- Links to relevant resources already available in Tomorrow Library.
- Text-only notices for future books, videos, visual explanations and Python practice material. There are no dummy download links.
- A clearly labelled Prosperity 5 getting-started notice. Edition-specific setup, dates, products, limits and submission instructions are intentionally deferred.

The new guide requires no JavaScript, framework, package installation or server-side code. The Python changes are limited to the site's existing build and link-check utilities; they are not trading code or notebooks. The existing homepage and shared styles are unchanged.

## Continue authoring

Edit the five HTML files directly. They are hand-authored static pages and are not overwritten by `tools/build.py`. HTML comments identify chapter content, practice and future resource areas. Keep titles and descriptions up to date: the build reads them when adding these pages to search and the sitemap.

Use a consistent header and navigation when adding chapters. For future resource cards, record the author or creator, a real source URL and the purpose of the reference. Add notebook download links only when the files exist, and identify the relevant dataset and historical edition. Add text alternatives and reduced-motion behaviour when visual explanations are implemented.

The `#prosperity-5` section on `CTRL/index.html` is the current place to replace or extend when the next competition starts. No getting-started chapter is claimed to be available yet.

## Existing-site integration

| File | Change |
| --- | --- |
| `catalogue/competitions.json` | Points IMC Prosperity to `CTRL/`. |
| `tools/build.py` | Links local competition headings to their guides; discovers CTRL HTML pages for search and the sitemap. |
| `tools/check_site.py` | Checks nested CTRL pages and resolves directory links to `index.html`. |
| `competitions.html` | Ready-to-serve updated IMC listing. |
| `assets/search-index.js` | Adds the five guide pages and points the IMC search result to CTRL. |
| `sitemap.xml` | Adds the five canonical CTRL paths. |
| `ctrl.html` | Replaces the previously empty file with a redirect and fallback. |

After content changes, run the repository's normal build:

```sh
python tools/build.py
python tools/check_site.py
```

To preview the merged repository locally:

```sh
python -m http.server 8000
```

Then open `http://localhost:8000/CTRL/`. Serve the repository root so the existing resource links and shared styles resolve correctly.

## Verification

Prepared against main commit `37f9d4aa936a61037b98acbbca790fc1fd4457e2` on 15 November 2026.

- The build completes and discovers all five CTRL pages.
- The new pages, competition links, local assets, fragment targets and IDs pass the repository's checks.
- The homepage → Compete → IMC Prosperity route, all four chapter pages, expandable topics, mobile chapter menu and search integration were checked in a browser.
- Desktop, 375px mobile and 768px tablet layouts were inspected; the mobile and tablet pages had no horizontal overflow.
- The full-site checker still reports 13 pre-existing missing assets or links in the unrelated `approach.html`. Compared with the original checkout, this change introduces no additional errors and fixes the previously blank `ctrl.html` page.

## Competition overview source

The short orientation describes the general structure of prior editions. It links to [IMC's official Prosperity page](https://prosperity.imc.com/), checked on 15 November 2026. It does not treat prior-edition rules as Prosperity 5 rules.
