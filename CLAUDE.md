# CareGraph — Claude Code Project Guide

## What is CareGraph?

CareGraph is a free, open-source, ad-free static website that unifies 100+ publicly available CMS (Centers for Medicare & Medicaid Services) datasets into a single richly interlinked exploration tool. It precomputes cross-dataset joins offline and serves the results as static HTML pages with JSON data manifests. The full product specification lives at `cms-unified-vbc-tool-spec.md`.

## v1 starting entity subset

The first public release covers **4 entity types**: Hospitals, SNFs (Skilled Nursing Facilities), Counties, and ACOs (Accountable Care Organizations). Each has a canonical page at a stable URL (e.g., `/hospital/123456`, `/county/06037`). Remaining entity types (Clinicians, Drugs, Conditions, DRGs, etc.) are v1.x follow-on.

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
│   └── dist/                  # Build output, rsync'd to VPS (gitignored)
└── deploy/
    ├── deploy.sh              # rsync + atomic symlink swap
    └── nginx.conf             # Nginx config for caregraph.org
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

```bash
# Requires .env.deploy with VPS_HOST, VPS_USER, REMOTE_PATH
bash deploy/deploy.sh
```

This rsync's `site/dist/` to the VPS with atomic symlink swap. See `deploy/deploy.sh` for details.

## Key architectural decisions

- **JSON for frontend rendering.** The browser consumes precomputed JSON manifests, one per canonical page. No database queries at runtime.
- **Parquet for downloads only.** Parquet files are ETL build artifacts for researcher download. The browser never reads parquet in v1.
- **Astro static-site mode.** No SSR. HTML pages are pre-rendered at build time from JSON manifests.
- **Leaflet for maps.** Raster tiles, zero API-key cost. (Maps are not yet implemented in M1.)
- **No DuckDB-WASM in v1.** In-browser SQL querying is deferred to v2. v1 Table mode is a client-side data grid.
- **Manual ETL.** No automated scheduling. The maintainer runs `python etl/run.py` on their workstation.
- **Direct rsync deploy.** Built artifacts go workstation → VPS via rsync. GitHub holds only source code.

## Coding conventions

- **Python:** 3.11+, type hints encouraged, ruff for formatting/linting.
- **JavaScript/TypeScript:** Astro components, minimal client-side JS. Prefer Astro's built-in features.
- **Data files:** JSON manifests in `site_data/`, raw downloads in `data/raw/` named `{dataset_id}_{YYYY-MM-DD}.csv`.
- **Join keys:** CCN = 6-char zero-padded string. FIPS = 5-digit zero-padded string. NPI = 10-digit string.

## What to work on next (after M1)

M2 — Four-entity spine (weeks 5–10):
1. Add all remaining datasets for Hospitals, SNFs, Counties, and ACOs (see spec §6.1 for the full list per entity type).
2. Add SNF and ACO entity pages with full dataset joins.
3. Implement year toggle on entity pages (ETL ships all available vintages).
4. Build cross-links between the 4 entity types (neighborhood manifests).
5. Build global search index (precomputed JSON blob).
6. Build Explore browser pages with Table mode (filterable, sortable data grid).
7. Ensure all 10 analytical use cases in spec §9 that are answerable within these 4 entities are reachable via navigation.
