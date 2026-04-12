# CMS Dataset Expansion Plan for CareGraph

> Research date: 2026-04-12. Based on a systematic survey of [data.cms.gov](https://data.cms.gov/), the [Provider Data Catalog](https://data.cms.gov/provider-data/), [Provider Summary by Type of Service](https://data.cms.gov/provider-summary-by-type-of-service), [Summary Statistics on Use and Payments](https://data.cms.gov/summary-statistics-on-use-and-payments), and [CMS Shared Savings Program Data](https://www.cms.gov/medicare/payment/fee-for-service-providers/shared-savings-program-ssp-acos/data).

---

## Current Inventory (11 datasets)

| Internal ID | Provider Data ID | Name | Entity | Join Key |
|---|---|---|---|---|
| `xubh-q36u` | `xubh-q36u` | Hospital General Information | Hospital | CCN |
| `hrrp` | `9n3s-kdb3` | Hospital Readmissions Reduction Program | Hospital | CCN |
| `hvbp-tps` | `ypbt-wvdk` | Hospital VBP Total Performance Score | Hospital | CCN |
| `nh-provider-info` | `4pq5-n9py` | Nursing Home Provider Info | SNF | CCN |
| `nh-quality-mds` | `djen-97ju` | SNF Quality Measures (MDS) | SNF | CCN |
| `mssp-performance` | — | MSSP ACO Performance PY2024 | ACO | ACO ID |
| `geo-var-county` | — | Medicare Geographic Variation by County | County | FIPS |
| `cdc-places` | — | CDC PLACES County-Level Data | County | FIPS |
| `partd-drug-spending` | — | Medicare Part D Spending by Drug | Drug | Generic name |
| `partb-drug-spending` | — | Medicare Part B Spending by Drug | Drug | HCPCS |
| `inpatient-by-drg` | — | Medicare Inpatient Hospitals by Provider & Service | DRG | DRG code + CCN |

The 4 core entity types (Hospital, SNF, County, ACO) plus 3 derived types (Drug, Condition, DRG) are already built.

---

## TIER 1 — Enrich Existing Entity Types

These datasets join directly to entities CareGraph already has via CCN, FIPS, or ACO ID. Highest ROI: just add a download entry and an enrichment step.

### 1A. Hospital Enrichments (join on 6-char CCN)

#### Timely & Effective Care — Hospital

- **Provider Data ID:** `yv7e-xc69`
- **Source:** [data.cms.gov/provider-data/dataset/yv7e-xc69](https://data.cms.gov/provider-data/dataset/yv7e-xc69)
- **API type:** provider-data
- **What it adds:** ~30 process-of-care measures including ED wait times (OP-18, OP-22), stroke care timeliness, sepsis treatment (SEP-1), immunization rates, blood clot prevention, heart attack/heart failure process measures, and preventive care.
- **Row structure:** One row per facility per measure. Pivot into the hospital manifest as a `timely_effective_care` section.
- **Join:** `facility_id` = CCN (6-char zero-padded), exact match to `xubh-q36u`.
- **Companion datasets:** State averages (`apyc-v239`), National averages (`isrn-hqyy`) — useful as benchmark context but not entity-level.

#### Unplanned Hospital Visits — Hospital

- **Provider Data ID:** `632h-zaca`
- **Source:** [data.cms.gov/provider-data/dataset/632h-zaca](https://data.cms.gov/provider-data/dataset/632h-zaca)
- **API type:** provider-data
- **What it adds:** 30-day readmission rates (all-cause hospital-wide, plus condition-specific: AMI, HF, pneumonia, COPD, stroke, CABG, THA/TKA), ED visit rates after discharge, and planned/unplanned return rates. Complements HRRP data with more granular readmission breakdowns.
- **Join:** `facility_id` = CCN.
- **Overlap with HRRP:** HRRP has readmission excess ratios used for payment; this dataset has the actual observed/expected rates and national comparisons. Both are useful — HRRP for the payment penalty story, this for clinical performance.

#### Complications & Deaths — Hospital

- **Provider Data ID:** `ynj2-r877`
- **Source:** [data.cms.gov/provider-data/dataset/ynj2-r877](https://data.cms.gov/provider-data/dataset/ynj2-r877)
- **API type:** provider-data
- **What it adds:** 30-day mortality rates for AMI, heart failure, pneumonia, COPD, stroke, CABG. Hip/knee complication rates. PSI-90 composite and individual Patient Safety Indicators.
- **Join:** `facility_id` = CCN.

#### Healthcare Associated Infections — Hospital

- **Provider Data ID:** `77hc-ibv8`
- **Source:** [data.cms.gov/provider-data/dataset/77hc-ibv8](https://data.cms.gov/provider-data/dataset/77hc-ibv8)
- **API type:** provider-data
- **What it adds:** Standardized Infection Ratios (SIR) for CLABSI (central line bloodstream infections), CAUTI (catheter urinary tract infections), SSI (surgical site infections for colon and hysterectomy), MRSA bacteremia, and C. difficile. Data sourced from CDC NHSN.
- **Join:** `facility_id` = CCN.

#### Patient Survey (HCAHPS) — Hospital

- **Provider Data ID:** `dgck-syfz`
- **Source:** [data.cms.gov/provider-data/dataset/dgck-syfz](https://data.cms.gov/provider-data/dataset/dgck-syfz)
- **API type:** provider-data
- **What it adds:** Patient experience scores across ~10 HCAHPS dimensions: nurse communication, doctor communication, staff responsiveness, pain management, medicine communication, discharge information, care transition, hospital cleanliness, hospital quietness, overall rating (0-10), and willingness to recommend. Reported as top-box percentages and star ratings.
- **Join:** `facility_id` = CCN.

#### Medicare Spending Per Beneficiary — Hospital

- **Provider Data ID:** `5hk7-b79m`
- **Source:** [data.cms.gov/provider-data/dataset/5hk7-b79m](https://data.cms.gov/provider-data/dataset/5hk7-b79m)
- **API type:** provider-data
- **What it adds:** MSPB ratio (hospital episode cost vs. national median). Values > 1.0 mean the hospital's episodes cost more than median. Covers the full episode: 3 days before admission through 30 days post-discharge.
- **Join:** `facility_id` = CCN.
- **Related:** Medicare Hospital Spending by Claim (`nrth-mfg3`) decomposes spending by claim type (inpatient, outpatient, SNF, HH, hospice, carrier, DME) and time period. Same CCN join.

#### CMS PSI-90 Composite — Six-Digit Estimate

- **Provider Data ID:** `muwa-iene`
- **Source:** [data.cms.gov/provider-data/dataset/muwa-iene](https://data.cms.gov/provider-data/dataset/muwa-iene)
- **API type:** provider-data
- **What it adds:** Patient Safety and Adverse Events Composite (PSI-90) plus individual component measures: pressure ulcers, in-hospital falls, perioperative hemorrhage/hematoma, post-op respiratory failure, etc. Six decimal-place precision.
- **Join:** `facility_id` = CCN.
- **Overlap:** Partially overlaps with Complications & Deaths (`ynj2-r877`) which also includes PSI measures. This dataset has the full precision values.

#### Summary: Hospital Enrichment Impact

Adding these 6-7 datasets transforms hospital pages from "basic directory + HRRP/VBP" into a Care Compare-equivalent profile covering:

- **Safety:** HAI, PSI-90, complications, mortality
- **Effectiveness:** Timely/effective care process measures
- **Patient experience:** HCAHPS scores
- **Efficiency:** MSPB spending, readmission rates
- **Payment:** VBP scores (already have), HRRP penalties (already have)

### 1B. SNF / Nursing Home Enrichments (join on 6-char CCN)

#### Penalties

- **Provider Data ID:** `g6vv-u9sr`
- **Source:** [data.cms.gov/provider-data/dataset/g6vv-u9sr](https://data.cms.gov/provider-data/dataset/g6vv-u9sr)
- **API type:** provider-data
- **What it adds:** Fines (civil money penalties) and payment denials received in the last 3 years: penalty amounts, penalty dates, penalty types.
- **Join:** `federal_provider_number` = CCN.

#### Health Deficiencies

- **Provider Data ID:** `r5ix-sfxw`
- **Source:** [data.cms.gov/provider-data/dataset/r5ix-sfxw](https://data.cms.gov/provider-data/dataset/r5ix-sfxw)
- **API type:** provider-data
- **What it adds:** Health inspection citations from the last 3 years: citation tag number, description, scope and severity level (A through L), inspection date, correction date, current status. One row per citation per facility.
- **Join:** `federal_provider_number` = CCN.
- **Related:** Fire Safety Deficiencies (companion dataset, same structure) covers fire safety inspection citations.

#### Ownership

- **Provider Data ID:** `y2hd-n93e`
- **Source:** [data.cms.gov/provider-data/dataset/y2hd-n93e](https://data.cms.gov/provider-data/dataset/y2hd-n93e)
- **API type:** provider-data
- **What it adds:** Multi-level corporate ownership chains: individual owners, organizational owners, managing employees. Critical for identifying multi-facility operators and private equity ownership (a hot policy topic).
- **Join:** `federal_provider_number` = CCN.

#### Survey Summary

- **Provider Data ID:** (part of the nursing homes topic)
- **What it adds:** Inspection dates, total deficiency counts by category (health, fire safety), number of complaint investigations, per-facility summary.
- **Join:** `federal_provider_number` = CCN.

#### Staffing Detail (Payroll-Based Journal)

- **What it adds:** Detailed staffing hours per resident day from CMS Payroll-Based Journal (PBJ) data: RN HPRD, LPN HPRD, CNA HPRD, total nursing HPRD, physical therapist HPRD, weekend staffing averages, staff turnover rates. Already partially in `nh-provider-info` but the dedicated staffing file has more granularity (e.g. adjusted vs. reported, daily vs. averaged).
- **Join:** `federal_provider_number` = CCN.

#### SNF Value-Based Purchasing (VBP)

- **What it adds:** SNF readmission measure (SNF 30-Day All-Cause Readmission Measure, SNFRM), performance score, baseline/performance periods, incentive payment multiplier.
- **Join:** CCN.
- **Note:** This is the SNF analog of the hospital HRRP/HVBP programs. Directly comparable.

### 1C. ACO Enrichments (join on ACO ID)

#### ACO Participants

- **Source:** [data.cms.gov/medicare-shared-savings-program/accountable-care-organization-participants](https://data.cms.gov/medicare-shared-savings-program/accountable-care-organization-participants)
- **API type:** data-api
- **What it adds:** The list of TINs (Taxpayer Identification Numbers) and their associated NPIs/CCNs that participate in each MSSP ACO. Includes provider names, provider types, participation start dates.
- **Join:** ACO ID (primary key) → produces lists of CCNs (hospitals, SNFs) and NPIs (clinicians) per ACO.
- **Why this is critical:** This is the **primary crosswalk** for linking ACOs to hospitals, SNFs, and (eventually) clinicians. Without it, the ACO↔Hospital and ACO↔SNF relationships are geographic-only. With it, they're organizational.

#### ACO SNF Affiliates

- **Source:** [data.cms.gov/medicare-shared-savings-program/accountable-care-organization-skilled-nursing-facility-affiliates](https://data.cms.gov/medicare-shared-savings-program/accountable-care-organization-skilled-nursing-facility-affiliates)
- **API type:** data-api
- **What it adds:** SNF CCNs affiliated with each ACO (the 3-day SNF waiver list). SNF name, CCN, state, start date.
- **Join:** ACO ID → SNF CCN. Enables direct ACO→SNF links on both entity pages.

#### County-Level Expenditure & Risk Score Data on Assignable Beneficiaries

- **Identifier:** `5f9f1216-6fd9-455d-bfbc-0efade687a4e`
- **API type:** data-api
- **What it adds:** Per capita Parts A and B FFS expenditures, average HCC risk scores, total person-years — by county, by enrollment type (ESRD, disabled, aged). For the Shared Savings Program assignable population.
- **Join:** County FIPS. Enriches county pages with ACO-program-specific cost benchmarks.

#### ACO REACH Datasets (5 datasets)

| Dataset | Identifier | What it adds |
|---|---|---|
| ACO REACH Financial & Quality Results | `6c3532b3-...` | Performance data: risk arrangements, stop-loss, capitation, savings rate, quality results |
| ACO REACH Aligned Beneficiaries | `1cd9eded-...` | County-level alignment counts: counties, eligibility months, total aligned benes |
| ACO REACH Eligible Beneficiaries | `54551982-...` | Reference population for comparison: risk scores, eligibility months |
| ACO REACH Providers | `e0eba16f-...` | Participant and preferred providers: NPIs, capitation arrangements, elected waivers |

- **Join:** ACO REACH entity IDs are separate from MSSP ACO IDs, but some organizations participate in both. County FIPS for beneficiary data. NPI for provider data.
- **Note:** ACO REACH is the successor to the Direct Contracting model. Coverage is 2021-2023 only (model may be evolving).

### 1D. County Enrichments (join on FIPS)

#### Medicare Advantage Enrollment by County

- **Source:** [cms.gov MA enrollment data](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-enrollment-contract/plan/state/county)
- **What it adds:** Monthly MA/Part D enrollment counts by contract, plan, state, and county. Enables MA penetration rate calculation per county.
- **Join:** County FIPS (SSA county code with crosswalk to FIPS).
- **Note:** This is on cms.gov, not data.cms.gov. It's a set of monthly CSV files. The SSA→FIPS crosswalk is already partially implemented in CareGraph's `etl/normalize/keys.py`.

#### CMS Program Statistics — Medicare Advantage Utilization (4 datasets)

| Dataset | Identifier | Granularity |
|---|---|---|
| MA — Inpatient Hospital | `f7bc5d11-...` | State-level |
| MA — Outpatient Facility | `bbcffb70-...` | State-level |
| MA — SNF | `81d7cb4c-...` | State-level |
| MA — Physician/Supplier | `900059a0-...` | State-level |

- **Join:** State FIPS (2-digit). These are state-level aggregates, not county-level — limited granularity.
- **Value:** Shows MA vs. FFS utilization differences by state. Could enrich state-level aggregation pages.

---

## TIER 2 — New Entity Types

These require new page builders, templates, URL routes, and cross-link manifests.

### 2A. Home Health Agencies (HHA) — ~11,000 entities

| Dataset | Provider Data ID | What it provides |
|---|---|---|
| Home Health Care Agencies | `6jpm-sxkc` | Directory: name, address, phone, quality measure ratings, star ratings |
| Home Health Care — Zip Codes | `m5eg-upu5` | Service area ZIP codes per agency |
| Home Health Care — National Data | `97z8-de96` | National quality measure averages (benchmark context) |

**Primary key:** CCN (6-character, same format as hospitals/SNFs).

**Joins to existing entities:**

| Target Entity | Join Method |
|---|---|
| County | HHA address → geocode to FIPS (same pattern as hospitals/SNFs) |
| Hospital | Co-location in same county; post-acute referral inference via Medicare Spending by Claim |
| ACO | Via ACO Participants dataset (TIN matching from HHA's organizational TIN) |
| SNF | Post-acute care alternative in same county |

**Additional utilization data:**
- Medicare Home Health Agencies — by Provider (provider-summary-by-type-of-service): episodes, visits, charges, payments per HHA. Joins on CCN.

### 2B. Hospice Providers — ~5,000 entities

| Dataset | Provider Data ID | What it provides |
|---|---|---|
| Hospice — General Information | `yc9t-dgbk` | Directory: name, address, phone, ownership, CCN |
| Hospice — Provider Data | `252m-zfp9` | Quality measures: pain assessment, dyspnea screening, treatment preferences, ED visits in last days |
| Hospice CAHPS — Provider | `gxki-hrr8` | Patient/family experience scores |
| Hospice — Zip Data | `95rg-2usp` | Service area ZIP codes |
| Hospice CAHPS — National | `7cv8-v37d` | National benchmark averages |

**Primary key:** CCN.

**Joins to existing entities:**

| Target Entity | Join Method |
|---|---|
| County | Address → FIPS geocode |
| Hospital | Co-location; hospice referrals from hospital discharge |
| ACO | Via ACO Participants (TIN) |

**Additional utilization data:**
- Medicare Hospice — by Provider (provider-summary-by-type-of-service): hospice days, charges, payments, primary diagnosis mix per hospice. Joins on CCN.

### 2C. Dialysis Facilities — ~7,800 entities

| Dataset | Provider Data ID | What it provides |
|---|---|---|
| Dialysis Facility — Listing by Facility | `23ew-n7w9` | Directory with quality measures and star ratings |
| ICH CAHPS — Facility | `59mq-zhts` | In-center hemodialysis patient experience |
| Dialysis Facility — State Averages | `2fpu-cgbb` | State benchmark context |
| Dialysis Facility — National Averages | `2rkq-ygai` | National benchmark context |

**Primary key:** CCN.

**Joins to existing entities:**

| Target Entity | Join Method |
|---|---|
| County | Address → FIPS |
| Hospital | Co-location; ESRD hospitalizations via DRG data (DRG codes 682-684, 652-653) |
| ACO | Via Kidney Care Choices / REACH model participants; or ACO Participants TIN |
| Drug | ESRD-related Part B drugs (EPO, iron) cross-reference |

**Additional data:**
- Comprehensive ESRD Care Model data (identifier `7bd74bf4-...`) for ESCOs that opted in.

### 2D. Ambulatory Surgical Centers (ASCs) — ~5,700 entities

| Dataset | Provider Data ID | What it provides |
|---|---|---|
| ASC Quality Measures — Facility | `4jcv-atw7` | ASCQR performance: colonoscopy quality, infection prevention |
| OAS CAHPS — ASC Facility | `48nr-hqxx` | Patient experience scores |
| ASC Quality Measures — State | `axe7-s95e` | State benchmark context |
| OAS CAHPS — ASC State | `x663-bwbj` | State benchmark context |
| ASC Quality Measures — National | `wue8-3vwe` | National benchmark context |
| OAS CAHPS — ASC National | `tf3h-mrrs` | National benchmark context |

**Primary key:** CCN.

**Joins to existing entities:**

| Target Entity | Join Method |
|---|---|
| County | Address → FIPS |
| Hospital | Outpatient alternative; HOPDs vs. ASCs for same procedures |

**Note:** ASCs are a smaller entity type with fewer quality measures. Lower priority than HHA/Hospice/Dialysis unless a specific use case demands it.

### 2E. Clinicians / Physicians — ~1.3M entities

The largest potential expansion. Multiple datasets contribute to a clinician profile:

| Dataset | Source Section | What it provides |
|---|---|---|
| Medicare Physician & Other Practitioners — by Provider & Service | provider-summary-by-type-of-service | NPI-level utilization: HCPCS codes, volumes, charges, allowed amounts, payments |
| Medicare Physician — by Provider | provider-summary-by-type-of-service | NPI-level summary: total services, unique beneficiaries, total payments |
| Medicare Physician — by Geography & Service | provider-summary-by-type-of-service | State/national aggregates by HCPCS |
| Medicare Part D Prescribers — by Provider | provider-summary-by-type-of-service | NPI-level prescribing: total Rx count, total drug cost, opioid/antibiotic flags |
| Medicare Part D Prescribers — by Provider & Drug | provider-summary-by-type-of-service | NPI + drug-level prescribing detail |
| Medicare Part D Prescribers — by Geography & Drug | provider-summary-by-type-of-service | State/national prescribing aggregates |
| MIPS Clinician Public Reporting | Provider Data (`a174-a962`) | MIPS final score, quality/PI/IA category scores |
| NPPES NPI Registry | External (npiregistry.cms.hhs.gov) | Clinician name, credentials, specialty taxonomy, practice address |

**Primary key:** NPI (10-digit).

**Joins to existing entities:**

| Target Entity | Join Method |
|---|---|
| Hospital | Facility affiliations: NPI → CCN (via Medicare enrollment data or ACO Participants) |
| SNF | Same as hospital (clinicians practicing at SNFs) |
| ACO | ACO Participants dataset: NPI or TIN → ACO ID |
| County | Practice address → FIPS geocode (from NPPES) |
| Drug | Part D Prescriber data → drug generic name (already a CareGraph entity) |
| DRG | Physician inpatient utilization → DRG codes |
| Condition | Specialty taxonomy → associated conditions (derived mapping) |

**Scale considerations:** At ~1.3M entities, full clinician pages would massively expand site size. Strategies to manage:
1. **Aggregated-only:** Don't build individual clinician pages; instead build "physicians at this hospital" or "top prescribers of this drug" as embedded sections on existing entity pages.
2. **Scoped rollout:** Start with "clinicians affiliated with ACOs" (~300K) or "clinicians at hospitals" to limit scope.
3. **Full build:** Individual clinician pages (like ProPublica's "Prescriber Checkup" or CMS Care Compare's clinician profiles). Large but technically feasible since pages are static.

---

## TIER 3 — Utilization & Spending Summaries (Provider-Level)

These are the **Provider Summary by Type of Service** datasets. They provide utilization and payment data at the individual provider level, broken down by service type. All are available at [data.cms.gov/provider-summary-by-type-of-service](https://data.cms.gov/provider-summary-by-type-of-service).

| Dataset | Granularity | Join Key | What it adds |
|---|---|---|---|
| Medicare Inpatient Hospitals — by Provider & Service | Hospital + DRG | CCN | Discharge counts, avg charges, avg payment per DRG (partially overlaps `inpatient-by-drg`) |
| Medicare Inpatient Hospitals — by Provider | Hospital summary | CCN | Total discharges, charges, payments, case mix index |
| Medicare Inpatient Hospitals — by Geography & Service | State/national + DRG | — | Aggregate benchmarks |
| Medicare Outpatient Hospitals — by Provider & Service | Hospital + APC | CCN | Outpatient service volumes, payments by APC code |
| Medicare Outpatient Hospitals — by Provider | Hospital summary | CCN | Total outpatient services, charges, payments |
| Medicare Skilled Nursing — by Provider | SNF summary | CCN | SNF stays, charges, payments, avg LOS |
| Medicare Home Health — by Provider | HHA summary | CCN | HH episodes, visits, charges, payments |
| Medicare Hospice — by Provider | Hospice summary | CCN | Hospice days, charges, payments, diagnosis mix |
| Medicare DMEPOS — by Referring Provider | Supplier/physician | NPI | DME utilization and payments |
| Medicare DMEPOS — by Supplier | Supplier | NPI | Supplier-level DME sales |

**Value:** These datasets add the "business side" to entity pages — how much Medicare pays, how many patients are served, what the charge-to-payment ratio is. They complement the quality data from the Provider Data Catalog.

---

## TIER 4 — Special Programs & Supplementary Data

### Health Insurance Marketplace / QHP Data

- **Source:** [cms.gov Marketplace Public Use Files](https://www.cms.gov/marketplace/resources/data/public-use-files)
- **What it provides:** Qualified Health Plan premiums, benefit designs, cost sharing, issuer enrollment, metal levels — by county, state, and issuer. Plan years 2014-2026.
- **Join to CareGraph:** County FIPS (coverage area). No direct provider join. Different domain from Medicare provider quality.
- **Assessment:** Interesting for county-level "insurance landscape" but a stretch from CareGraph's Medicare provider focus. Lower priority.

### Medicaid Managed Care

- **Source:** [data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-service-type-reports/medicaid-managed-care](https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-service-type-reports/medicaid-managed-care)
- **What it provides:** State-level Medicaid enrollment in managed care, plan types, enrollment counts.
- **Join:** State FIPS only (very coarse).
- **Assessment:** State-level only. Limited granularity for CareGraph's entity-level approach.

### Medicaid T-MSIS Analytic Files

- **Source:** CMS Research Data Assistance Center (ResDAC)
- **What it provides:** Detailed Medicaid claims and enrollment data.
- **Join:** N/A — requires Data Use Agreement, not a public-access PUF. Not usable for CareGraph.

### Medicare Advantage Enrollment by Contract/Plan/State/County

- **Source:** [cms.gov MA enrollment data](https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-advantagepart-d-contract-and-enrollment-data/monthly-enrollment-contract/plan/state/county)
- **What it provides:** Monthly MA and Part D enrollment by county, contract, and plan.
- **Join:** County FIPS (via SSA-to-FIPS crosswalk).
- **Assessment:** High value for county pages — enables "MA penetration rate" and "plans available" metrics. Moderate ETL complexity due to monthly files and SSA→FIPS mapping.

### AHRQ PSI-11 Measure Rates

- **Identifier:** `7cf9662e-7c5c-4fe0-a8c6-828edf81a23c`
- **What it provides:** Provider-level postoperative respiratory failure rates.
- **Join:** CCN. Temporal coverage is 2015-2016 only — may be stale.

### Ambulatory Specialty Model Participants

- **Identifier:** `175d576d-0568-4ac2-aec5-d77f3ee02205`
- **What it provides:** Clinicians in the new CMS Ambulatory Specialty Model (2026+).
- **Join:** NPI.
- **Assessment:** Very new model, small participant pool. Watch for future data.

### Advance Investment Payment Spend Plans

- **Identifier:** `a3d35ba1-3ff4-48dd-91b4-8e1f9e7a19b7`
- **What it provides:** How new ACOs spend their advance investment payments (spending categories, projected vs. actual).
- **Join:** ACO ID.
- **Assessment:** Niche; useful for ACO deep-dive pages but not high priority.

---

## Datasets That Don't Join Well

| Dataset | Why |
|---|---|
| Medicaid T-MSIS detailed files | Requires DUA, not public |
| Medicare Claims RIF/LDS | Research-only, not public |
| VBP Payment Tables 1-4 (`xrgf-x36b`, `5gv4-jwyv`, `u625-zae7`, `vtqa-m4zn`) | Aggregate distribution histograms, no per-provider key |
| National/State average files (HCAHPS National, HAI State, etc.) | Benchmarks, not entity-level data. Useful as context sidebars, not as page data |
| Footnote Crosswalk (`y9us-9xdf`) | Metadata lookup table |
| CJR Model MSA Data (`62e490c0-...`) | Only ~67 MSAs, model now expired |
| Comprehensive ESRD Care Model (`7bd74bf4-...`) | 2016-2017 only, model concluded |

---

## Recommended Priority Order

### Phase 1 — Hospital Quality Depth (6 datasets)

These transform hospital pages from "directory + HRRP/VBP" into full Care Compare profiles. All join on CCN with no new infrastructure.

1. **Timely & Effective Care** (`yv7e-xc69`) — process quality measures
2. **Complications & Deaths** (`ynj2-r877`) — mortality rates and safety
3. **HCAHPS** (`dgck-syfz`) — patient experience
4. **Healthcare Associated Infections** (`77hc-ibv8`) — infection rates
5. **Unplanned Hospital Visits** (`632h-zaca`) — readmission details
6. **Medicare Spending Per Beneficiary** (`5hk7-b79m`) — cost efficiency

### Phase 2 — SNF Quality Depth (4-5 datasets)

Same pattern as Phase 1 — enrich existing SNF pages.

7. **Penalties** (`g6vv-u9sr`)
8. **Health Deficiencies** (`r5ix-sfxw`)
9. **Ownership** (`y2hd-n93e`)
10. **SNF VBP** (readmission measure + incentive payment)
11. Staffing detail (if not already fully covered by `nh-provider-info`)

### Phase 3 — ACO Cross-Links (2 datasets)

The ACO Participants dataset is the single most important crosswalk for connecting entities.

12. **ACO Participants** (TIN/NPI/CCN crosswalk → enables ACO↔Hospital and ACO↔SNF organizational links)
13. **ACO SNF Affiliates** (direct ACO→SNF link)

### Phase 4 — Post-Acute Care Entity Types (3 entity types, ~24K entities)

14. **Home Health Agencies** (`6jpm-sxkc`) — ~11K entities
15. **Hospice Providers** (`yc9t-dgbk` + `252m-zfp9` + `gxki-hrr8`) — ~5K entities
16. **Dialysis Facilities** (`23ew-n7w9` + `59mq-zhts`) — ~7.8K entities

### Phase 5 — Clinician/Physician Data (high complexity, high value)

17. Part D Prescribers — by Provider (links to Drug entity)
18. Physician Utilization — by Provider (NPI-level)
19. MIPS Clinician Public Reporting (`a174-a962`)
20. NPPES NPI Registry (external)

### Phase 6 — Utilization & Spending Layer

21. Provider Summary files (inpatient, outpatient, SNF, HH, hospice — by provider)
22. MA enrollment by county

---

## External (Non-CMS) Datasets Worth Considering

These are referenced in the product spec (§6) but are not on data.cms.gov:

| Dataset | Source | Entity/Join | What it adds |
|---|---|---|---|
| NPPES NPI Registry | npiregistry.cms.hhs.gov | Clinician / NPI | Names, credentials, specialties, addresses |
| CDC/ATSDR SVI | data.cdc.gov | County/Tract / FIPS | Social Vulnerability Index (4 themes, 16 indicators) |
| AHRQ SDOH Database | ahrq.gov | County/Tract / FIPS | Social determinants: poverty, education, housing, food |
| HRSA Area Health Resources Files | hrsa.gov | County / FIPS | Provider supply, health workforce, hospital beds per capita |
| County Health Rankings | countyhealthrankings.org | County / FIPS | Composite health outcome/factor rankings (Robert Wood Johnson) |
| USDA Food Access Research Atlas | ers.usda.gov | Census Tract / FIPS-11 | Food desert classification, access to healthy food |
| Census ACS | census.gov | County/Tract / FIPS | Demographics, income, insurance coverage, housing |
| Dartmouth Atlas HRR Definitions | dartmouthatlas.org | HRR / ZIP crosswalk | Hospital Referral Region boundaries for geographic analysis |
| Census CBSA Definitions | census.gov | CBSA code | Metropolitan/Micropolitan Statistical Area boundaries |

---

## API Access Notes

CareGraph's ETL already supports three API types. Most new datasets fit into existing patterns:

| API Type | Datasets Using It | Page Size | Auth |
|---|---|---|---|
| `provider-data` | All Provider Data Catalog datasets (hospital quality, SNF, HHA, hospice, dialysis, ASC) | 5,000 rows | None |
| `data-api` | Geographic Variation, MSSP, drug spending, utilization summaries | 5,000 rows | None |
| `soda` | CDC PLACES (on data.cdc.gov) | 50,000 rows | None (app token optional) |

The Provider Data Catalog also offers direct CSV bulk downloads (faster than paginated API). CareGraph's downloader already tries CSV first, then falls back to API — this pattern works for all new Provider Data Catalog additions.

For the Provider Summary by Type of Service datasets, the API type is `data-api` with the same pagination pattern already used for Geographic Variation and MSSP.
