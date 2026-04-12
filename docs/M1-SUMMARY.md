# M1 Skeleton — Build Summary

**Date:** 2026-04-11
**Branch:** `base`
**Commit:** Initial commit (37 files, 9,290 insertions)

---

## What was built

| Component | Key files | Status |
|---|---|---|
| **Repo scaffolding** | `README.md`, `LICENSE` (MIT), `.gitignore`, `CLAUDE.md`, `pyproject.toml` | Done |
| **ETL pipeline** | `etl/run.py` orchestrator, `etl/acquire/download.py`, `etl/normalize/keys.py`, `etl/build/build_hospitals.py`, `etl/build/build_counties.py`, `etl/validate/schemas.py`, `etl/provenance/envelope.py` | Done |
| **Editorial stub** | `etl/editorial/README.md` explaining future M3 work | Done |
| **Astro frontend** | `site/` with BaseLayout, Home page, `/hospital/[ccn]`, `/county/[fips]` | Done |
| **Deploy pipeline** | `deploy/deploy.sh` (rsync + atomic symlink), `deploy/nginx.conf` | Done |
| **Git** | Initialized, initial commit on `base` branch | Done |

---

## ETL results

- **5,426 hospital manifests** from Hospital General Information dataset
- **3,198 county manifests** from Medicare Geographic Variation (2023 vintage, county-level, all ages)
- **8,625 static HTML pages** built by Astro (hospitals + counties + home)
- **ETL runtime:** ~10 seconds (downloads cached after first run)
- **Astro build time:** ~25 seconds for all 8,625 pages

---

## Pages include

- **Explore mode**: Overview cards, key metrics, star ratings (hospitals), metric grid (counties)
- **Table mode**: Full field-by-field data table with sortable columns
- **CSV export**: Download button with all page data
- **Methodology stub**: Dataset provenance (source, vintage, download date, row count)
- **"Report an error" link**: GitHub Issue link in footer
- **Responsive layout**: Global nav with all spec nav items (placeholder links for future pages)
- **Mode toggle is sticky**: Stored in localStorage, persists across pages

---

## Datasets used

| Dataset | ID | Source | Rows | Entity count |
|---|---|---|---|---|
| Hospital General Information | `xubh-q36u` | Provider Data API / direct CSV | 5,426 | 5,426 hospitals |
| Medicare Geographic Variation | `geo-var-county` (UUID: `6219697b-8f6c-4164-bed4-cd9317c58ebc`) | CMS Data API / direct CSV | 33,639 total (3,198 county-level for 2023) | 3,198 counties |

---

## Decisions not in the spec

### 1. CMS API migration

The old SODA API (`https://data.cms.gov/resource/{id}.csv`) returns **410 Gone** for both datasets. CMS has retired this endpoint. The ETL now uses:

- **Direct CSV bulk download URLs** (preferred, most reliable)
- **Provider Data API** fallback: `https://data.cms.gov/provider-data/api/1/datastore/query/{id}/0` (for Hospital Compare datasets)
- **CMS Data API** fallback: `https://data.cms.gov/data-api/v1/dataset/{uuid}/data` (for spending/geographic datasets)

The direct CSV URLs may change when CMS publishes new vintages. When adding new datasets, always verify the current download URL.

### 2. Geographic Variation dataset ID

The spec mentioned `bqf5-pjmq` which is dead (404/410). The ETL uses `geo-var-county` as a local identifier, with the actual UUID `6219697b-8f6c-4164-bed4-cd9317c58ebc` for API access and a direct CSV URL pointing to the 2014-2023 public use file.

### 3. County data filtering

The Geographic Variation CSV contains rows at national, state, and county levels across 10 years (2014-2023) and multiple age groupings. The ETL filters to:
- `BENE_GEO_LVL == 'County'`
- `BENE_AGE_LVL == 'All'`
- Latest year only (2023)

This yields 3,198 county-level rows.

### 4. County name parsing

County names are parsed from the `BENE_GEO_DESC` column, which uses the format `"ST-County Name"` (e.g., `"CA-Los Angeles"`). The ETL splits on the first hyphen to extract state abbreviation and county name.

### 5. Column name handling

- **Hospital CSV**: Uses human-readable column names with spaces (e.g., `"Facility ID"`, `"Hospital overall rating"`)
- **County CSV**: Uses uppercase abbreviated column names (e.g., `BENE_GEO_CD`, `TOT_MDCR_STDZD_PYMT_PC`)

### 6. .gitignore `build/` pattern

The original `.gitignore` had a bare `build/` entry that matched `etl/build/`. Fixed to `/dist/` (root-only) so the ETL build module is properly tracked.

---

## How to reproduce

```bash
# 1. Install Python dependencies (Python 3.11+)
cd D:\Dropbox\PC\F\Estudo\Tecnologia\CareGraph\repo
pip install -e .

# 2. Run ETL (downloads ~40MB of CMS data, builds JSON manifests)
python etl/run.py

# 3. Build the Astro site (generates 8,625 static HTML pages)
cd site
npm install
npm run build

# 4. Preview locally
npm run preview
```

---

## Sample pages to test

- **Home**: `http://localhost:4321/`
- **Hospital** (Southeast Health Medical Center, AL): `http://localhost:4321/hospital/010001/`
- **County** (Los Angeles, CA): `http://localhost:4321/county/06037/`
- **County** (Cook County, IL — Chicago): `http://localhost:4321/county/17031/`
- **Hospital** (Cleveland Clinic): `http://localhost:4321/hospital/360180/`

---

## What's next (M2)

Per spec §18:

1. Add all remaining datasets for Hospitals, SNFs, Counties, and ACOs
2. Add SNF and ACO entity pages with full dataset joins
3. Implement year toggle on entity pages
4. Build cross-links between the 4 entity types (neighborhood manifests)
5. Build global search index (precomputed JSON blob)
6. Build Explore browser pages with Table mode (filterable, sortable data grid)
7. Ensure all 10 analytical use cases in spec §9 that are answerable within these 4 entities are reachable via navigation
