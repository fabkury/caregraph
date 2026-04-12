# Non-CMS Datasets for CareGraph

Research into publicly available datasets **not from data.cms.gov** that could enrich CareGraph's entity pages. Conducted April 2026.

CareGraph already uses or plans to use several non-CMS datasets referenced in the product spec (CDC PLACES, CDC/ATSDR SVI, AHRQ SDOH, HRSA AHRF, Census ACS, County Health Rankings, USDA Food Atlas, NPPES NPI Registry, HUD ZIP-to-tract crosswalk, NBER SSA-to-FIPS crosswalk). This document covers datasets **beyond** those.

---

## Tier 1: High value, direct join key, free bulk download

### 1. CMS Open Payments (Sunshine Act)

- **Source:** `openpaymentsdata.cms.gov`
- **What it adds:** Dollar amounts paid by pharma/device companies to physicians and teaching hospitals. 16M+ records totaling $13B+ (2024 data). Years 2013--2024 available.
- **Entity:** Hospitals (teaching), Clinicians (future)
- **Join key:** `Teaching_Hospital_CCN` (6-char) joins directly to Hospital entity. `Covered_Recipient_NPI` (10-digit) joins to future Clinician entity.
- **Format:** CSV bulk download (annual ZIP archives)
- **License:** Public domain (US government)
- **ETL approach:** New acquirer targeting `openpaymentsdata.cms.gov` bulk download URLs. Aggregate payments per CCN (sum, count, top paying companies). Add `industry_payments` section to hospital page manifests.
- **Limitations:** Only teaching hospitals have CCN in Open Payments. General payment records without a teaching hospital CCN are orphaned until Clinician entity pages exist. Note: while hosted on cms.gov, Open Payments is a distinct program from the Provider Data Catalog on data.cms.gov.

### 2. Community Benefit Insight (IRS 990 Schedule H)

- **Source:** `communitybenefitinsight.org` (RTI International project)
- **What it adds:** For ~2,400 nonprofit hospitals: community benefit spending, financial assistance provided, Medicaid shortfall, comparison of community benefit to tax exemption value ("fair share" analysis).
- **Entity:** Hospitals (nonprofit only)
- **Join key:** CCN (the API explicitly uses CMS Certification Number as its hospital identifier)
- **Format:** JSON API, spreadsheet export
- **License:** Public (RTI International project)
- **Available years:** 2010--2022
- **ETL approach:** Query their public API per CCN. Add `community_benefit` section to hospital page manifests with spending totals, categories, and fair-share ratio.
- **Limitations:** Covers only nonprofit hospitals (~2,400 of ~5,000 total). Government and for-profit hospitals do not file Schedule H. Annual data lags IRS filing cycle by 1--2 years.
- **Unique value:** Only public source for hospital-level community benefit spending vs. tax exemption analysis.

### 3. EPA Air Quality Index by County

- **Source:** `aqs.epa.gov/aqsweb/airdata/download_files.html`
- **Download URL pattern:** `https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_{YEAR}.zip`
- **What it adds:** Annual AQI statistics per county: max AQI, median AQI, number of days in each AQI category (Good/Moderate/Unhealthy for Sensitive Groups/Unhealthy/Very Unhealthy/Hazardous), dominant pollutant.
- **Entity:** Counties
- **Join key:** State Code + County Code columns = 5-digit FIPS. Direct join.
- **Format:** CSV (one ZIP file per year)
- **License:** Public domain (US government)
- **Available years:** 1988--2025
- **Update frequency:** Twice annually
- **ETL approach:** Download annual CSV files. One row per county per year. Add `air_quality` section to county page manifests.
- **Limitations:** Only ~800 counties have air quality monitors (of ~3,200 total). Unmonitored counties will show "—". Provenance tier: Direct (partial).

### 4. HRSA Health Professional Shortage Areas (HPSA)

- **Source:** `data.hrsa.gov/data/download`
- **What it adds:** Whether a county is designated as a Primary Care, Dental, or Mental Health shortage area. Includes HPSA shortage score (1--25), designation type, and status.
- **Entity:** Counties (geographic HPSAs), also facility-level HPSAs
- **Join key:** County FIPS for geographic HPSAs
- **Format:** XLSX, CSV, KML, SHP
- **License:** Public domain (US government)
- **Update frequency:** Updated nightly (complete replacement file)
- **ETL approach:** Download CSV from HRSA data portal. Filter to geographic (county-level) HPSAs. Add `shortage_areas` section to county page manifests with designation type and score per discipline. Could also add a badge/indicator to hospital pages if their county is a shortage area.
- **Limitations:** A county may be partially designated (only certain census tracts). Geographic HPSA designation is county-level but some are sub-county. Facility-level HPSAs apply to specific clinics, not whole counties.

### 5. USDA Rural-Urban Continuum Codes

- **Source:** `ers.usda.gov/data-products/rural-urban-continuum-codes`
- **What it adds:** A 9-level metro/nonmetro classification for every US county. Codes 1--3 are metro (large/medium/small), codes 4--9 are nonmetro (varying urbanization and metro adjacency).
- **Entity:** Counties
- **Join key:** County FIPS. Direct join.
- **Format:** Excel/CSV (single small file)
- **License:** Public domain (USDA)
- **Latest version:** 2023 (updated roughly every 10 years, aligned with Census)
- **ETL approach:** Download single CSV. One code per county. Add `rural_urban_code` and `rural_urban_description` fields to county page manifests. Trivial to implement.
- **Unique value:** Enables rural/urban stratification on every county page. Critical context for interpreting healthcare access, provider supply, and utilization patterns.

### 6. NBER NPI-to-CCN Crosswalk

- **Source:** `nber.org/research/data/national-provider-identifier-npi-medicare-ccn-crosswalk`
- **What it adds:** Bridge table linking NPI (10-digit provider ID) to CCN (6-char facility ID). Enables joining any NPI-keyed dataset to CareGraph's CCN-keyed hospital/SNF pages.
- **Entity:** Infrastructure (bridge table, not a displayed dataset)
- **Join key:** NPI <-> CCN mapping
- **Format:** CSV, Stata, SAS
- **License:** Free/public
- **ETL approach:** Download CSV. Load as a lookup table in `etl/normalize/`. Use when ingesting NPI-keyed datasets (Open Payments, Part D Prescribers, etc.) to resolve facility associations.
- **Limitations:** Based on December 2017 data (CMS stopped providing this linkage in January 2018). Some NPIs will be stale or missing for recently enumerated providers.

---

## Tier 2: Good value, some ETL complexity

### 7. openFDA (Adverse Events, Recalls, Labeling)

- **Source:** `open.fda.gov/apis/` (API) and `open.fda.gov/data/downloads/` (bulk)
- **What it adds:** Drug adverse event reports (FAERS), drug recalls/enforcement actions, drug labeling information, NDC directory.
- **Entity:** Drugs
- **Join key:** Generic drug name or NDC code, matched to CareGraph's Drug entity (currently keyed by generic name from Part D/B spending data).
- **Format:** JSON (API and bulk download)
- **License:** Public domain (US government)
- **Rate limits:** Without key: 240 req/min, 1,000/day. With free key: 240 req/min, 120,000/day.
- **ETL approach:** Use bulk JSON downloads. Match on generic drug name to CareGraph's drug entities. Add `safety_signals` section to drug page manifests with adverse event counts, top reported reactions, and recall history.
- **Limitations:** Adverse event reports are voluntary (MedWatch), not comprehensive. Reports do not prove causation. Provenance tier: Direct (partial). No direct facility or county join — strictly drug-level data.

### 8. EPA EJScreen (Environmental Justice)

- **Source:** `zenodo.org/records/14767363` (2015--2024 archive); originally from EPA
- **What it adds:** Environmental justice indicators: air toxics cancer risk, PM2.5 levels, ozone, traffic proximity, lead paint indicator, Superfund proximity, wastewater discharge proximity. Plus demographic indicators (low income %, minority %, linguistically isolated %).
- **Entity:** Counties (aggregated from block groups/census tracts)
- **Join key:** Block group/tract FIPS -> aggregate to county FIPS (first 5 digits)
- **Format:** CSV and geodatabase (GDB)
- **License:** Public domain (US government, when available)
- **ETL approach:** Download CSV from Zenodo archive. Aggregate tract-level indicators to county means/medians (population-weighted). Add `environmental_justice` section to county page manifests.
- **Limitations:** EPA's future publication status is uncertain post-2024. Zenodo archive ensures historical access. Requires tract-to-county aggregation step. Some indicators are modeled estimates.

### 9. CDC Environmental Public Health Tracking

- **Source:** `ephtracking.cdc.gov/` (data explorer and REST API)
- **API docs:** `ephtracking.cdc.gov/apihelp`
- **What it adds:** 600+ measures spanning air quality, water quality, climate/heat, asthma hospitalizations, cancer incidence, childhood lead poisoning, heart disease, reproductive outcomes.
- **Entity:** Counties
- **Join key:** County FIPS via REST API parameters
- **Format:** JSON (API), CSV/Excel (data explorer)
- **License:** Public domain (US government). Optional free API token available via email to trackingsupport@cdc.gov.
- **ETL approach:** Use REST API to pull a curated subset of high-value measures (e.g., asthma ER visit rate, childhood blood lead levels, drinking water violations, heat-related ER visits). Add `environmental_health` section to county page manifests.
- **Limitations:** Not all measures available for all counties. Update frequency varies by measure. Need to curate which of 600+ measures to include — showing all would overwhelm the county page.

### 10. Dartmouth Atlas Crosswalks (HSA/HRR)

- **Source:** `data.dartmouthatlas.org/supplemental/`
- **ZIP-to-HSA/HRR crosswalk:** `data.dartmouthatlas.org/downloads/geography/ZipHsaHrr19.csv.zip`
- **HRR boundary shapefiles:** `data.dartmouthatlas.org/downloads/geography/HRR_Bdry__AK_HI_unmodified.zip`
- **What it adds:** ZIP-to-HSA (Hospital Service Area) and ZIP-to-HRR (Hospital Referral Region) crosswalks. Defines which hospitals serve which areas, grouping counties into referral networks.
- **Entity:** Hospitals, Counties (adds a geographic layer)
- **Join key:** ZIP code (derivable from hospital/county addresses) -> HSA/HRR codes
- **Format:** CSV (crosswalks), shapefiles (boundaries)
- **License:** Free/public with attribution
- **ETL approach:** Download crosswalk CSV. Look up each hospital's ZIP to find its HSA and HRR. Add `service_area` and `referral_region` fields to hospital manifests. Add `hrr` field to county manifests. Could eventually build HSA/HRR entity pages.
- **Limitations:** Last updated 2019; no future updates planned. Still the standard geographic framework for healthcare market analysis. Historical rates data (through 2019) largely superseded by CMS Geographic Variation.

### 11. Washington Post ARCOS Opioid Shipment Data

- **Source:** `wpinvestigative.github.io/arcos` (R package and API)
- **What it adds:** DEA-tracked opioid pill shipments (oxycodone and hydrocodone) by county, pharmacy, and manufacturer. 2006--2014.
- **Entity:** Counties
- **Join key:** County FIPS
- **Format:** TSV via API, R package
- **License:** Public (obtained via court order in West Virginia opioid litigation, released by Washington Post)
- **ETL approach:** Download county-level aggregates via API. Pills per county per year. Add `opioid_shipments` section to county page manifests showing historical distribution volumes.
- **Limitations:** Historical only (2006--2014). Covers only oxycodone and hydrocodone. Powerful for historical context but frozen in time. Provenance: Direct (complete for covered drugs/years).

### 12. IRS Form 990 via ProPublica Nonprofit Explorer

- **Source:** `projects.propublica.org/nonprofits/api/` (API) and `irs.gov/charities-non-profits/form-990-series-downloads` (bulk XML)
- **What it adds:** Complete financial data for nonprofit hospitals: total revenue, total expenses, executive compensation, net assets, program service revenue, contributions. Schedule H data (community benefit, if parsed from XML).
- **Entity:** Hospitals (nonprofit only)
- **Join key:** EIN (Employer Identification Number) -> CCN via CMS Provider of Services crosswalk or NBER crosswalk
- **Format:** JSON (ProPublica API), XML (IRS bulk)
- **License:** Public domain (IRS data). ProPublica API is free.
- **ETL approach:** Build an EIN-to-CCN mapping from CMS Provider of Services file. Query ProPublica API by EIN for each mapped hospital. Add `financials` section to hospital page manifests with revenue, expenses, assets, and executive compensation.
- **Limitations:** Requires a two-step crosswalk (CCN -> EIN -> 990 data). Government hospitals are exempt from filing 990s. Data lags filing cycle. Parsing Schedule H from raw XML is complex; Community Benefit Insight (#2 above) is a better source for that specific data.

---

## Tier 3: Niche value or requires fuzzy matching

### 13. Joint Commission Quality Data

- **Source:** `jointcommission.org` — "Find Accredited Organizations" search tool and "Quality Data Download" tab
- **What it adds:** Accreditation status (accredited/not), accreditation decision date, performance measure results for ~15,000 healthcare organizations.
- **Entity:** Hospitals, SNFs
- **Join key:** CCN (called "Certification Care Number" in JC terminology). Some facilities have missing/invalid CCNs.
- **Format:** Downloadable files from Quality Data Download tab; no documented bulk API
- **License:** Free for public access
- **ETL approach:** Download quality data files. Join on CCN. Add `accreditation` section to hospital/SNF page manifests.
- **Limitations:** Bulk download completeness is unclear. May need to test what's available in the downloadable files vs. the search tool. Not all facilities are JC-accredited (some use state-only surveys).

### 14. ProPublica Nursing Home Inspect

- **Source:** `projects.propublica.org/nursing-homes/`
- **What it adds:** Nursing home inspection deficiencies with severity levels, dates, and categories. Repackaged and better-organized version of CMS inspection data.
- **Entity:** SNFs
- **Join key:** CMS provider number (CCN, 6-char)
- **Format:** ZIP containing 10 Excel files (one per CMS region)
- **License:** Free under ProPublica's standard terms
- **ETL approach:** Download ZIP. Parse Excel files. Join on CCN. Add `inspection_details` section to SNF page manifests.
- **Limitations:** Underlying data is from CMS (so overlaps with data.cms.gov sources). ProPublica's value-add is better organization and search — the raw data may already be available via CMS. Last updated February 2026.

### 15. Lown Institute Hospital Index (Free Tier)

- **Source:** `lownhospitalsindex.org/rankings/`
- **What it adds:** Rankings and grades across 53 metrics in equity, value, and outcomes for ~3,600 hospitals. Unique "Fair Share Spending" metric. Racial inclusivity index.
- **Entity:** Hospitals
- **Join key:** Hospital name + city + state (no confirmed CCN in free data). Requires fuzzy name matching.
- **Format:** Web interface with downloadable rankings. Historical dataset on `data.world/zendoll27/lown-hospital-index-for-equity-2022`.
- **License:** Free for rankings/grades; paid for detailed data
- **ETL approach:** Download free rankings. Build fuzzy name matcher (hospital name + state) to join to CareGraph hospitals by CCN. Add `equity_index` section to hospital page manifests.
- **Limitations:** Name matching is error-prone. Paid tier would presumably include better identifiers. Equity angle is unique but join quality is uncertain.

### 16. State Hospital Discharge Data

Select states publish free or low-cost discharge data:

- **New York SPARCS:** `health.data.ny.gov` — de-identified discharge records via Socrata API (free). Join on facility name (mappable to CCN via operating certificate crosswalk). Diagnoses, procedures, charges, demographics.
- **Texas PUDF:** `dshs.texas.gov` — free 2006--2019 discharge data. Join on THCIC facility ID (mappable to CCN via facility type files).
- **California HCAI:** `data.chhs.ca.gov` — free aggregate/facility-level data. Explicit HCAI-to-CCN crosswalk available at `data.chhs.ca.gov/dataset/licensed-facility-crosswalk`. Detailed discharge data requires DUA.

**ETL approach:** Build per-state acquirers. Use state-specific facility ID to CCN crosswalks. Aggregate to facility-level utilization summaries. Add state-specific `discharge_data` sections to hospital manifests.

**Limitations:** State-by-state implementation. Different schemas, identifiers, and update frequencies. Coverage is incomplete nationally. Best suited as enrichment for states where data is available, not a universal feature.

### 17. SAMHSA Treatment Facility Directory

- **Source:** `samhsa.gov/data/report/national-directory-of-mental-health-treatment-facilities` and `findtreatment.samhsa.gov`
- **What it adds:** Directory of mental health and substance abuse treatment facilities with addresses, services offered, payment accepted.
- **Entity:** Would require a new entity type, or could be aggregated as a county-level count.
- **Join key:** Facility addresses (geocodable to county FIPS). No FIPS field in source.
- **Format:** PDF, Excel
- **License:** Public domain (US government)
- **ETL approach:** Download Excel. Geocode addresses to county FIPS (using Census geocoder or similar). Aggregate facility counts per county. Add `behavioral_health_facilities` count to county page manifests.
- **Limitations:** Requires geocoding step. Directory may be incomplete. Facility-level pages would be a new entity type not in the current v1 scope.

---

## Not Viable (Paid or Restricted)

| Dataset | Source | Reason |
|---------|--------|--------|
| **Leapfrog Hospital Safety Grades** | hospitalsafetygrade.org | Bulk data costs $5,000+. Individual lookups free but not bulk-downloadable. |
| **AHA Annual Survey** | ahadata.com | Commercial product, $thousands/year license. Academic access via institutional affiliation only. |
| **Definitive Healthcare** | definitivehc.com | Enterprise SaaS, no open data at all. |
| **DEA Controlled Substance Registrations** | deadiversion.usdoj.gov | Restricted to DEA registrants. Annual application required. |
| **HCUP Patient-Level Data** | hcup-us.ahrq.gov | Must be purchased from AHRQ Central Distributor. HCUPnet (free) provides only aggregated national queries, no bulk download. |
| **KFF State Health Facts** | kff.org/state-health-facts | 800+ indicators, but no bulk API. Each indicator must be manually exported as CSV. Not scalable for ETL. |

---

## Recommended Implementation Order

Ranked by effort-to-value ratio (easiest high-value items first):

| Priority | Dataset | Effort | Join | Value Added |
|----------|---------|--------|------|-------------|
| 1 | USDA Rural-Urban Continuum | Trivial (1 small CSV) | FIPS | Rural/urban context for every county |
| 2 | HRSA HPSA | Easy (CSV, FIPS join) | FIPS | Shortage area designations per county |
| 3 | EPA AQI by County | Easy (annual CSV, FIPS join) | FIPS | Air quality stats for ~800 counties |
| 4 | Community Benefit Insight | Moderate (API per CCN) | CCN | Hospital community benefit spending |
| 5 | CMS Open Payments | Moderate (large CSV, CCN join) | CCN + NPI | Industry payments to teaching hospitals |
| 6 | openFDA Adverse Events | Moderate (JSON API, drug name match) | Drug name/NDC | Drug safety signals and recall history |
| 7 | NBER NPI-to-CCN Crosswalk | Infrastructure | NPI <-> CCN | Enables all future NPI-keyed datasets |
| 8 | Dartmouth Atlas Crosswalks | Moderate (CSV, ZIP lookup) | ZIP | Adds HSA/HRR geographic layer |
| 9 | EPA EJScreen | Moderate (tract aggregation) | FIPS (via tract) | Environmental justice indicators |
| 10 | CDC Env. Public Health Tracking | Moderate (API, measure curation) | FIPS | Environmental health outcomes |
| 11 | WaPo ARCOS Opioid Data | Easy (API, FIPS join) | FIPS | Historical opioid distribution volumes |
| 12 | IRS 990 / ProPublica | Complex (EIN-to-CCN crosswalk) | EIN -> CCN | Nonprofit hospital financials |

---

## Licensing Notes

All Tier 1 and Tier 2 datasets are either public domain (US government work) or published under open/free terms. Two datasets warrant attention:

- **County Health Rankings** (already in CareGraph spec): licensed CC BY-NC-SA 4.0. The non-commercial clause may need review depending on CareGraph's terms of use.
- **Lown Institute Hospital Index**: license terms not explicitly documented for the free tier. Contact `index@lowninstitute.org` for clarification before integration.

All other datasets listed here are US government publications and carry no copyright restrictions.
