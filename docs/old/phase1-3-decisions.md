# Phase 1-3 Implementation Decisions

> Implementation date: 2026-04-12

## Overview

Added 11 new CMS datasets across 3 phases:
- **Phase 1:** 6 hospital quality enrichment datasets
- **Phase 2:** 3 SNF enrichment datasets
- **Phase 3:** 2 ACO cross-link datasets

Total registered datasets went from 12 to 23.

---

## Phase 1: Hospital Enrichments

### Datasets Added

| Internal ID | Provider Data ID | Name |
|---|---|---|
| `hosp-timely-care` | `yv7e-xc69` | Timely and Effective Care — Hospital |
| `hosp-complications` | `ynj2-r877` | Complications and Deaths — Hospital |
| `hosp-hcahps` | `dgck-syfz` | Patient Survey (HCAHPS) — Hospital |
| `hosp-hai` | `77hc-ibv8` | Healthcare Associated Infections — Hospital |
| `hosp-unplanned-visits` | `632h-zaca` | Unplanned Hospital Visits — Hospital |
| `hosp-mspb` | `5hk7-b79m` | Medicare Spending Per Beneficiary — Hospital |

### Decision: Generic measure loader vs. per-dataset loaders

**Chose: Generic `_load_measures_by_ccn()` loader.** All 5 multi-row datasets (all except MSPB) share the same Provider Data CSV structure: one row per facility per measure, with a `Facility ID` column and a `Measure ID` column. Rather than writing 5 separate loader functions (like the existing `_load_hrrp` and `_load_hvbp`), a single generic loader handles all of them.

MSPB is different — it has one row per hospital (not per-measure) — so it gets its own `_load_mspb()` function.

### Decision: Manifest data structure for measures

**Chose: Store as list of row dicts under `manifest.data.*`.** Each new dataset is stored as `manifest.data.timely_effective_care`, `.complications_deaths`, `.hcahps`, `.hai`, `.unplanned_visits` — all as arrays of row objects preserving original CMS column names. This is consistent with how the frontend renders them (iterating rows in a `<table>`).

MSPB is stored as a single dict at `manifest.data.mspb` since it's one record per hospital.

### Decision: CSV URLs

**Chose: `csv_url: None` (API-only) for all new datasets.** The direct CSV download URLs for Provider Data Catalog datasets change when CMS refreshes the data (they embed a hash in the filename). Rather than hard-coding URLs that will break, we use the paginated API endpoint which is stable. The existing downloader already handles the API→CSV fallback pattern.

### Decision: Keyword-only arguments for new enrichment paths

**Chose: `*` separator in `enrich_hospitals()` signature.** The 6 new CSV paths are keyword-only arguments with `None` defaults. This means the existing call signature is fully backward-compatible — callers that don't pass the new arguments get the existing HRRP/HVBP/FIPS behavior, with the new enrichments gracefully skipped. No changes needed in existing code that calls `enrich_hospitals()`.

### Decision: Frontend rendering approach

**Chose: Condition-aware data tables.** Each new dataset section in the hospital template checks for data existence (`{hcahps && hcahps.length > 0 && (...)}`) before rendering. Tables use the CMS column names directly as field lookups with multiple fallback keys (e.g., `row['Measure ID'] || row['Measure Name']`), making the rendering robust to minor column name variations between CMS data refreshes.

The Timely & Effective Care table is limited to 30 rows in Explore mode (this dataset can have 30+ measures per hospital). Full data is available in Table mode.

---

## Phase 2: SNF Enrichments

### Datasets Added

| Internal ID | Provider Data ID | Name |
|---|---|---|
| `nh-penalties` | `g6vv-u9sr` | Nursing Home Penalties |
| `nh-deficiencies` | `r5ix-sfxw` | Nursing Home Health Deficiencies |
| `nh-ownership` | `y2hd-n93e` | Nursing Home Ownership |

### Decision: New `enrich_snfs.py` module

**Chose: Separate module rather than extending an existing one.** There was no existing SNF enrichment module (unlike hospitals which had `enrich_hospitals.py`). Created `etl/build/enrich_snfs.py` with the same pattern as the hospital enricher: load CSVs into per-CCN dicts, iterate manifests, join data, add provenance.

### Decision: Deficiency display limit

**Chose: Show 50 deficiencies max in Explore view.** Some SNFs have 100+ deficiency citations over 3 years. Showing all of them would make the page very long. The Explore view shows the first 50 with a "Showing X of Y" message, while the Table mode shows all raw data.

### Decision: Ownership data structure

**Chose: Array of owner objects.** The CMS Ownership dataset has multiple rows per facility (one per owner/officer). We store all owners as a list, letting the frontend render a table showing the ownership chain. This naturally handles multi-level corporate ownership.

---

## Phase 3: ACO Cross-Links

### Datasets Added

| Internal ID | DCAT Identifier | Name |
|---|---|---|
| `aco-participants` | `9767cb68-...` | ACO Participants |
| `aco-snf-affiliates` | `5b227bd9-...` | ACO SNF Affiliates |

### Decision: Bidirectional cross-links

**Chose: Write links in both directions.** When we process ACO Participants, we:
1. Add the participant list to the ACO manifest at `manifest.data.participants`
2. Build a reverse index (CCN→ACO ID) and write ACO links onto hospital and SNF manifests in their `related` arrays

This means hospital pages show "participates in ACO X" and ACO pages show "includes Hospital Y" — without requiring the cross-links module to know about ACO participants.

### Decision: Enrichment ordering

**Chose: ACO enrichment runs after SNF enrichment but before cross-links.** The enrichment order in `run.py` is:
1. Step 9: Enrich hospitals (HRRP, HVBP, FIPS, Phase 1 datasets)
2. Step 9b: Enrich SNFs (penalties, deficiencies, ownership)
3. Step 9c: Enrich ACOs (participants, SNF affiliates — writes reverse links)
4. Step 10: Enrich counties (CDC PLACES)
5. Step 11: Build cross-links (geographic co-location links)

ACO enrichment writes reverse links onto hospital/SNF manifests, so it must run after those entities are built. The geographic cross-links step runs after everything, adding co-location links that complement the organizational ACO links.

### Decision: ACO→Hospital link via CCN in participant data

**Chose: Link ACO participants to hospitals only when a CCN is present.** The ACO Participants dataset includes both institutional providers (with CCNs — hospitals, SNFs) and individual practitioners (with NPIs — clinicians). Since CareGraph doesn't yet have clinician pages, we only create links for participants that have a CCN. The participant data is still stored in full on the ACO manifest for future use when clinician pages are added.

### Decision: API type for ACO datasets

**Chose: `data-api` (not `provider-data`).** The ACO Participants and SNF Affiliates datasets are part of the Medicare Shared Savings Program section on data.cms.gov, not the Provider Data Catalog. They use the CMS Data API (JSON pagination) rather than the Provider Data API. The existing downloader handles both API types.

---

## Files Changed

### New files
- `etl/build/enrich_snfs.py` — SNF enrichment module
- `etl/build/enrich_acos.py` — ACO enrichment module

### Modified files
- `etl/acquire/download.py` — Added 11 dataset entries to DATASETS dict
- `etl/build/enrich_hospitals.py` — Added generic measure loader, MSPB loader, extended `enrich_hospitals()` with 6 new keyword-only CSV path params
- `etl/run.py` — Added imports for new modules, added Steps 9b/9c, updated manifest index metadata and summary output
- `site/src/pages/hospital/[ccn].astro` — Added 6 new data sections (Complications, HCAHPS, HAI, Timely Care, Unplanned Visits, MSPB)
- `site/src/pages/snf/[ccn].astro` — Added 3 new data sections (Penalties, Deficiencies, Ownership), updated methodology section
- `site/src/pages/aco/[id].astro` — Added 2 new data sections (Network Participants, SNF Affiliates)

### Validation
- All Python imports pass (`python -c "from etl.build.enrich_* import ..."`)
- All 23 datasets registered in DATASETS dict
- Ruff lint passes on all new/modified Python files
- Astro build succeeds: 26,337 pages built with zero errors
