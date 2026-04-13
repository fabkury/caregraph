# CareGraph — Claude Code Project Guide

## What is CareGraph?

CareGraph is a free, open-source, ad-free static website that unifies 30 publicly available CMS (Centers for Medicare & Medicaid Services) and CDC datasets into a single richly interlinked exploration tool. It precomputes cross-dataset joins offline and serves the results as static HTML pages with JSON data manifests. The full product specification lives at `docs/cms-unified-vbc-tool-spec.md`.

## Entity types

The site covers **7 entity types**: Hospitals, SNFs (Skilled Nursing Facilities), Counties, ACOs (Accountable Care Organizations), Drugs, Conditions, and DRGs. Each has a canonical page at a stable URL (e.g., `/hospital/123456`, `/county/06037`, `/drug/metformin`).

## Directory layout

```
caregraph/
├── README.md
├── LICENSE                    # MIT
├── CLAUDE.md                  # This file
├── .gitignore
├── pyproject.toml             # Python deps: httpx, duckdb, pydantic
├── cms-unified-vbc-tool-spec.md  # Full product specification (authoritative)
├── etl/
│   ├── run.py                 # Top-level ETL orchestrator
│   ├── acquire/               # Download scripts (data.cms.gov API)
│   │   └── download.py
│   ├── normalize/             # Join-key normalization (CCN, FIPS, SSA-to-FIPS)
│   │   └── keys.py
│   ├── build/                 # Entity table + page manifest builders
│   │   ├── build_hospitals.py
│   │   └── build_counties.py
│   ├── validate/              # Schema validation (pydantic)
│   │   └── schemas.py
│   ├── provenance/            # Provenance envelope construction
│   │   └── envelope.py
│   └── editorial/             # AI editorial pipeline (stub in M1)
│       └── README.md
├── data/
│   ├── raw/                   # Content-addressable downloads (gitignored)
│   └── interim/               # Work artifacts (gitignored)
├── site_data/                 # ETL output fed to Astro build (gitignored)
├── site/                      # Astro frontend (static-site mode)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── dist/                  # Build output, committed and deployed via GitHub Pages
├── deploy/
│   ├── deploy.sh              # Legacy VPS deploy (deprecated)
│   └── nginx.conf             # Legacy Nginx config (deprecated)
└── .github/
    └── workflows/
        └── deploy.yml         # GitHub Pages deployment workflow
```

## How to run the ETL

```bash
# From repo root. Requires Python 3.11+.
pip install -e .
python etl/run.py
```

This downloads CMS datasets into `data/raw/`, normalizes join keys, builds JSON page manifests, validates them, and writes output to `site_data/`. Downloads are content-addressable (`{dataset_id}_{YYYY-MM-DD}.csv`) so re-running doesn't overwrite previous vintages.

## How to build the site

```bash
cd site
npm install    # First time only
npm run build  # Produces site/dist/
```

The Astro build reads JSON manifests from `site_data/` and produces static HTML pages.

## How to deploy

The site is deployed to GitHub Pages. After building, commit `site/dist/` and push to `main`:

```bash
git add site/dist/
git commit -m "Rebuild site"
git push
```

A GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically deploys the contents of `site/dist/` to GitHub Pages on every push to `main`. The custom domain `caregraph.org` is configured via the `site/public/CNAME` file.

## Key architectural decisions

- **JSON for frontend rendering.** The browser consumes precomputed JSON manifests, one per canonical page. No database queries at runtime.
- **Parquet for downloads only.** Parquet files are ETL build artifacts for researcher download. The browser never reads parquet in v1.
- **Astro static-site mode.** No SSR. HTML pages are pre-rendered at build time from JSON manifests.
- **Leaflet for maps.** Raster tiles, zero API-key cost. (Maps are not yet implemented in M1.)
- **No DuckDB-WASM in v1.** In-browser SQL querying is deferred to v2. v1 Table mode is a client-side data grid.
- **Manual ETL.** No automated scheduling. The maintainer runs `python etl/run.py` on their workstation.
- **GitHub Pages deploy.** Built artifacts (`site/dist/`) are committed to the repo and deployed to GitHub Pages via GitHub Actions. The custom domain `caregraph.org` points to GitHub Pages.

## Coding conventions

- **Python:** 3.11+, type hints encouraged, ruff for formatting/linting.
- **JavaScript/TypeScript:** Astro components, minimal client-side JS. Prefer Astro's built-in features.
- **Data files:** JSON manifests in `site_data/`, raw downloads in `data/raw/` named `{dataset_id}_{YYYY-MM-DD}.csv`.
- **Join keys:** CCN = 6-char zero-padded string. FIPS = 5-digit zero-padded string. NPI = 10-digit string.

## What to work on next

Potential future work:
1. Add more CMS datasets to existing entity types.
2. Add new entity types.
3. Implement year toggle on entity pages (ETL ships all available vintages).
4. Add DuckDB-WASM for in-browser SQL querying (v2).
5. Add Leaflet-based maps.
