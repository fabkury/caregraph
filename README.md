# CareGraph

[![Status: Pre-Alpha](https://img.shields.io/badge/status-pre--alpha-orange)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Public CMS Data**

CareGraph is a free, open-source, ad-free website that unifies 30 publicly available CMS and CDC datasets into a single richly interlinked exploration tool. It serves value-based care leaders, researchers, journalists, and clinicians who need scorecards, benchmarks, filterable tables, full methodology, and downloadable data -- all cross-linked through the identifiers (CCN, NPI, TIN, FIPS) that tie Medicare's data ecosystem together.

## How it works

All heavy lifting runs offline via a manual ETL on the maintainer's workstation. The site is static HTML served by GitHub Pages. The browser renders precomputed JSON manifests through a lightweight data grid.

```
ETL (Python + DuckDB)  -->  site_data/ (JSON manifests)
                               |
                         Astro build  -->  site/dist/ (static HTML)
                               |
                         git push  -->  GitHub Pages  -->  caregraph.org
```

## Current scope

- **Hospitals** -- Hospital General Information, HVBP, HRRP, HAC, HCAHPS, MSPB, Cost Reports
- **SNFs / Nursing Homes** -- Provider Info, MDS Quality, Penalties, Deficiencies, Ownership, Cost Reports
- **Counties** -- Geographic Variation, Chronic Conditions, CDC PLACES, SDOH
- **ACOs** -- MSSP Performance, Participants, SNF Affiliates, Beneficiary by County
- **Drugs** -- Part D Spending, Part B Spending, Part B Discarded Units, NADAC
- **Conditions** -- CDC PLACES county-level prevalence
- **DRGs** -- Medicare Inpatient by Provider and Service

## Quick start

```bash
# 1. Install Python dependencies
pip install -e .

# 2. Run ETL (downloads data, builds manifests)
python etl/run.py

# 3. Build the static site
cd site && npm install && npm run build

# 4. Deploy (commit site/dist/ and push to main)
git add site/dist/ && git commit -m "Rebuild site" && git push
```

## How to cite

> CareGraph. (2026). *CareGraph: Unified CMS data exploration tool.* https://caregraph.org. Source code: https://github.com/fabkury/caregraph.

## License

MIT. See [LICENSE](LICENSE).

Data content is sourced from publicly available CMS, CDC, AHRQ, HRSA, Census, and USDA datasets. Per-source licenses are documented in the Methodology Hub.
