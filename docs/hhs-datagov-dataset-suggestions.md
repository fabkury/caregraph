# HHS Data.gov Dataset Suggestions for CareGraph

> Research date: 2026-04-12. Based on a systematic survey of [catalog.data.gov/organization/hhs-gov](https://catalog.data.gov/organization/hhs-gov) (19,616 datasets across NIH, SAMHSA, ACF, FDA, CDC, CMS, and HRSA).
>
> **Scope:** This document covers datasets found on the HHS data.gov catalog that are **not already documented** in `cms-dataset-expansion.md` or `non-cms-datasets.md`. Where a dataset partially overlaps with existing plans, the overlap is noted and the new information highlighted.

---

## How This Report Is Organized

Suggestions are grouped by the CareGraph entity type they would enrich, then ranked by feasibility and value within each group. Each entry specifies:

- **Catalog URL** on data.gov
- **Data source** (the actual download endpoint)
- **What it adds** to CareGraph
- **Join key** and linkage strategy
- **Format and update frequency**
- **Limitations and caveats**

---

## 1. Hospital Enrichments (join on CCN)

### 1.1 Hospital Provider Cost Report

- **Catalog:** [catalog.data.gov/dataset/hospital-provider-cost-report](https://catalog.data.gov/dataset/hospital-provider-cost-report)
- **Source:** [data.cms.gov/provider-compliance/cost-reports/hospital-provider-cost-report](https://data.cms.gov/provider-compliance/cost-reports/hospital-provider-cost-report)
- **What it adds:** Annual financial data from CMS Form 2552-10: facility characteristics, utilization (bed count, discharges, patient days), cost and charges by cost center (total and Medicare-specific), Medicare settlement data, net income, operating margins, and financial statement data. This is the single richest source of hospital financial health.
- **Join key:** CMS Certification Number (CCN), exact match to existing hospital entities.
- **Format:** CSV, one file per year. Years 2011--2023 available.
- **Update frequency:** Annual.
- **Linkage strategy:**
  1. Download annual CSV from data.cms.gov.
  2. Join on CCN (column name `Provider_CCN` or `prvdr_num` depending on vintage).
  3. Add `cost_report` section to hospital manifest with key financial metrics: total revenue, total expenses, operating margin, Medicare share of revenue, uncompensated care costs, FTE counts, case mix index.
  4. Multi-year data enables trend display (e.g., margin over time).
- **Unique value:** Only public source for hospital-level financial data (revenue, expenses, margins). Complements the quality/safety data already in CareGraph with the financial viability dimension. Enables questions like "Is this hospital financially stable?" and "What fraction of its revenue comes from Medicare?"
- **Limitations:** Cost report data lags ~18 months. Some fields are complex accounting constructs. Not all hospitals file (critical access hospitals file on CMS Form 2552-96, a different format). Data dictionary PDF available from CMS.

### 1.2 Hospital-Acquired Condition (HAC) Reduction Program

- **Catalog:** [catalog.data.gov/dataset/hospital-acquired-condition-hac-reduction-program](https://catalog.data.gov/dataset/hospital-acquired-condition-hac-reduction-program)
- **Source:** [data.cms.gov/provider-data/dataset/yq43-i98g](https://data.cms.gov/provider-data/dataset/yq43-i98g)
- **What it adds:** Whether a hospital is in the worst-performing quartile for hospital-acquired conditions and receives a 1% payment reduction. Includes Total HAC Score, CMS PSI-90 composite score, and five HAI (Healthcare-Associated Infection) measures. This is a direct financial penalty indicator.
- **Join key:** CCN (`facility_id`), exact match.
- **Format:** CSV via Provider Data API.
- **Update frequency:** Annual (tied to fiscal year).
- **Linkage strategy:**
  1. Add to ETL download list as a provider-data API dataset.
  2. Join on `facility_id` = CCN.
  3. Add `hac_reduction` section to hospital manifest with: Total HAC Score, payment reduction flag (yes/no), component measure scores.
  4. Cross-reference with existing HAI data (`hosp-hai`) for deeper infection rate context.
- **Unique value:** Binary penalty indicator is highly actionable. Pairs with HRRP and VBP penalty data to create a "triple penalty" view: how many CMS payment programs penalize this hospital?
- **Limitations:** Only identifies the worst quartile; hospitals just above the cutoff have similar scores but no penalty.

### 1.3 Provider of Services File -- Hospital & Non-Hospital Facilities

- **Catalog:** [catalog.data.gov/dataset/provider-of-services-file-hospital-non-hospital-facilities-f216f](https://catalog.data.gov/dataset/provider-of-services-file-hospital-non-hospital-facilities-f216f)
- **Source:** [data.cms.gov/provider-compliance/certification-and-compliance/provider-of-services-file-hospital-non-hospital-facilities](https://data.cms.gov/provider-compliance/certification-and-compliance/provider-of-services-file-hospital-non-hospital-facilities)
- **What it adds:** Comprehensive provider directory with certification details not available in Hospital General Information: certification date, termination date (if closed), accreditation organization (Joint Commission, HFAP, DNV, etc.), number of beds by type (medical/surgical, ICU, psychiatric, pediatric, etc.), teaching hospital status, trauma center designation, residency program size, swing bed approval, state licensure number.
- **Join key:** CCN (`prvdr_num`), exact match. Also contains NPI.
- **Format:** CSV.
- **Update frequency:** Quarterly.
- **Linkage strategy:**
  1. Download quarterly CSV.
  2. Join on CCN.
  3. Enrich hospital manifest with: accreditation body, bed breakdown by type (ICU beds, psychiatric beds, etc.), teaching status, residency count, trauma designation, certification/termination dates.
  4. Can also be used as the authoritative source for CCN-to-NPI mapping for hospitals.
- **Unique value:** Fills structural gaps in Hospital General Information: bed-type breakdown, accreditation body, teaching/trauma status. Also provides closed-facility detection (termination dates).
- **Limitations:** Large file (~7,000 rows for hospitals, plus non-hospital providers). Columns vary across vintages.

### 1.4 Medicare Outpatient Hospitals -- by Provider and Service

- **Catalog:** [catalog.data.gov/dataset/medicare-outpatient-hospitals-by-provider-and-service-b164f](https://catalog.data.gov/dataset/medicare-outpatient-hospitals-by-provider-and-service-b164f)
- **Source:** [data.cms.gov/provider-summary-by-type-of-service/medicare-outpatient-hospitals](https://data.cms.gov/provider-summary-by-type-of-service/medicare-outpatient-hospitals)
- **What it adds:** Outpatient service volumes and payments by Ambulatory Payment Classification (APC) code, per hospital. Complements existing inpatient DRG data with the outpatient side: how many outpatient visits, what services are most common, what does Medicare pay.
- **Join key:** CCN (provider identifier). APC codes link to HCPCS service codes.
- **Format:** CSV. Years 2015--2023.
- **Update frequency:** Annual.
- **Linkage strategy:**
  1. Download annual CSV.
  2. Join on CCN for hospital-level data.
  3. Aggregate top APCs per hospital (analogous to existing top-DRGs-per-hospital cross-links).
  4. Add `outpatient_services` section to hospital manifest with top 10 APCs by volume, total outpatient payments, and outpatient-to-inpatient revenue ratio.
- **Unique value:** CareGraph currently shows only the inpatient side (DRGs). Adding outpatient data gives a complete picture of hospital service mix. Many hospitals derive more revenue from outpatient than inpatient.
- **Limitations:** APC codes are less intuitive than DRGs for lay users. May need plain-language APC descriptions.
- **Note:** Partially mentioned in `cms-dataset-expansion.md` Tier 3 but without detailed linkage strategy.

### 1.5 HHS Provider Relief Fund

- **Catalog:** [catalog.data.gov/dataset/hhs-provider-relief-fund](https://catalog.data.gov/dataset/hhs-provider-relief-fund)
- **Source:** [data.cdc.gov/d/kh8y-3es6](https://data.cdc.gov/d/kh8y-3es6)
- **What it adds:** COVID-19 Provider Relief Fund distributions: payment amounts received by healthcare providers from the $175B CARES Act fund. Covers general distributions, targeted distributions, and COVID-19 high-impact payments.
- **Join key:** Provider name + state + city (no CCN or NPI in catalog metadata). Will need fuzzy name matching or a crosswalk.
- **Format:** CSV via SODA API (data.cdc.gov).
- **Update frequency:** Weekly (as of last metadata update).
- **Linkage strategy:**
  1. Download CSV.
  2. Attempt to match provider names to CareGraph hospitals, SNFs, and other entities using name + city + state fuzzy matching.
  3. If a TIN or provider number column exists in the actual data (not documented in metadata), use that for direct join.
  4. Add `covid_relief` section to hospital/SNF manifests with: total PRF received, payment type breakdowns.
- **Unique value:** Shows the financial impact of COVID-19 on individual providers. Contextualizes any quality/utilization changes observed during the pandemic period.
- **Limitations:** Join quality is uncertain without confirmed provider identifiers. Data may contain duplicates or subsidiary-level entries. One-time historical dataset (pandemic era).

---

## 2. SNF / Nursing Home Enrichments (join on CCN)

### 2.1 Skilled Nursing Facility Cost Report

- **Catalog:** [catalog.data.gov/dataset/skilled-nursing-facility-cost-report-cd2b7](https://catalog.data.gov/dataset/skilled-nursing-facility-cost-report-cd2b7)
- **Source:** [data.cms.gov/provider-compliance/cost-reports/skilled-nursing-facility-cost-report](https://data.cms.gov/provider-compliance/cost-reports/skilled-nursing-facility-cost-report)
- **What it adds:** Annual financial data from CMS Form 2540-10: facility revenue, expenses, cost per patient day, Medicare vs. Medicaid payer mix, staffing FTEs, utilization (resident days, admissions), net income, and financial reserves.
- **Join key:** CCN (`prvdr_num`), exact match to existing SNF entities.
- **Format:** CSV, one file per year. Years 2011--2023.
- **Update frequency:** Annual.
- **Linkage strategy:**
  1. Download annual CSV.
  2. Join on CCN.
  3. Add `cost_report` section to SNF manifest with: revenue, expenses, operating margin, Medicare/Medicaid payer mix percentages, cost per patient day, staffing FTEs.
- **Unique value:** Reveals financial health of nursing homes. Combined with existing quality/deficiency/penalty data, enables "is this facility cutting corners due to financial pressure?" analysis. Payer mix (% Medicaid) is a known correlate of quality issues.
- **Limitations:** Same lag and complexity caveats as hospital cost reports. Some small facilities have irregular filing.

### 2.2 Payroll Based Journal (PBJ) Daily Nurse Staffing

- **Catalog:** [catalog.data.gov/dataset/payroll-based-journal-daily-nurse-staffing-94bbe](https://catalog.data.gov/dataset/payroll-based-journal-daily-nurse-staffing-94bbe)
- **Source:** [data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing](https://data.cms.gov/quality-of-care/payroll-based-journal-daily-nurse-staffing)
- **What it adds:** Granular daily staffing hours by category: Director of Nursing, Administrative RN, Registered Nursing, Licensed Practical Nurses, Certified Nurse Aides, Certified Medication Aides, Nurse Aides in Training, plus non-nurse categories (respiratory therapist, occupational therapist, social worker). Also includes daily census from MDS submissions.
- **Join key:** Facility provider number (CCN), exact match.
- **Format:** CSV, quarterly files. Coverage: 2018 Q4 through 2025 Q3.
- **Update frequency:** Quarterly.
- **Linkage strategy:**
  1. Download quarterly CSV files.
  2. Join on facility CCN.
  3. Compute derived metrics: RN hours per resident day (HPRD), total nursing HPRD, weekend vs. weekday staffing ratio, staffing variability (standard deviation of daily hours).
  4. Add `staffing_detail` section to SNF manifest with computed metrics and trend over recent quarters.
- **Unique value:** Much more granular than the summary staffing data already in `nh-provider-info`. Daily data reveals weekend staffing drops, high-variability days, and seasonal patterns. This is the data CMS uses to compute star ratings for staffing.
- **Limitations:** Large dataset (daily rows per facility). Requires aggregation in ETL. Some facilities have data quality issues in early quarters.
- **Note:** Partially referenced in `cms-dataset-expansion.md` but without the detailed daily-level analysis strategy.

### 2.3 Nursing Home Affiliated Entity (Chain) Performance Measures

- **Catalog:** [catalog.data.gov/dataset/nursing-home-affiliated-entity-performance-measures](https://catalog.data.gov/dataset/nursing-home-affiliated-entity-performance-measures)
- **Source:** [data.cms.gov](https://data.cms.gov) (CMS provider data)
- **What it adds:** Quality and performance measures aggregated at the chain/ownership group level: average health star ratings, staffing star ratings, quality star ratings, select enforcement remedies, claims-based measures, MDS measures, and SNF QRP metrics -- all for groups of nursing homes that share common owners.
- **Join key:** Chain/entity identifier to individual facility CCNs (via the existing Nursing Home Ownership dataset, which maps CCNs to organizational owners).
- **Format:** CSV, updated monthly.
- **Update frequency:** Monthly.
- **Linkage strategy:**
  1. Download chain-level performance CSV.
  2. Use the existing `nh-ownership` dataset to map individual SNF CCNs to their parent chain/entity.
  3. Add `chain_performance` section to SNF manifests: chain name, chain average star ratings, how this facility compares to its chain average, chain-wide penalty/deficiency rates.
  4. Optionally, build a new "Chain" entity type as a future expansion (entities would be ownership groups with links to all their SNFs).
- **Unique value:** Ownership chains are a major policy focus. Private equity ownership of nursing homes correlates with quality issues. This dataset lets users see "how does this nursing home's chain perform overall?" -- a context that no individual-facility dataset provides.
- **Limitations:** Chain identification methodology may not perfectly match CareGraph's ownership data. Some facilities are independent (no chain affiliation). Chain entity IDs may not be stable across updates.

### 2.4 CMS COVID-19 Nursing Home Dataset

- **Catalog:** [catalog.data.gov/dataset/cms-covid-19-nursing-home-dataset](https://catalog.data.gov/dataset/cms-covid-19-nursing-home-dataset) (Connecticut portal entry, but data is national)
- **Source:** CDC NHSN (National Healthcare Safety Network) via CMS
- **What it adds:** Weekly facility-level COVID-19 data: resident and staff confirmed cases, resident and staff deaths, staff and resident vaccination rates, PPE supply status, ventilator capacity, testing data. Reported by all Medicare/Medicaid nursing homes.
- **Join key:** Federal Provider Number = CCN, exact match.
- **Format:** CSV.
- **Update frequency:** Weekly during pandemic; cadence may have changed.
- **Linkage strategy:**
  1. Download CSV.
  2. Join on Federal Provider Number = CCN.
  3. Aggregate to facility-level pandemic summary: total resident cases, total resident deaths, peak weekly case rate, current vaccination rates, weeks with supply shortages.
  4. Add `covid_impact` section to SNF manifests.
- **Unique value:** Nursing homes were disproportionately affected by COVID-19. This data tells a story that no other quality metric captures. Combined with staffing data (PBJ) and penalty data, enables analysis of whether understaffed facilities had worse COVID outcomes.
- **Limitations:** Historical/pandemic-era data. Relevance diminishes over time but remains important for retrospective analysis. Data quality issues in early pandemic weeks.

---

## 3. County Enrichments (join on FIPS)

### 3.1 CDC SDOH Measures for County (ACS 2017--2021)

- **Catalog:** [catalog.data.gov/dataset/sdoh-measures-for-county-acs-2017-2021](https://catalog.data.gov/dataset/sdoh-measures-for-county-acs-2017-2021)
- **Source:** [data.cdc.gov/api/views/i6u4-y3g4](https://data.cdc.gov/api/views/i6u4-y3g4) (SODA API)
- **What it adds:** County-level social determinants of health from the American Community Survey: poverty rates, educational attainment, unemployment, health insurance coverage, housing quality, transportation access, and other socioeconomic indicators. Published by CDC's Division of Population Health (same team as PLACES).
- **Join key:** County FIPS, direct join to existing county entities.
- **Format:** CSV, JSON, RDF, XML via SODA API on data.cdc.gov.
- **Update frequency:** Updated with new ACS 5-year releases (roughly annual).
- **Linkage strategy:**
  1. Download via SODA API (same API type as CDC PLACES, already supported by CareGraph's ETL).
  2. Join on county FIPS code.
  3. Add `social_determinants` section to county manifest with key indicators: % below poverty, % uninsured, % with no high school diploma, median household income, % without vehicle, % with disability.
  4. These indicators can also be used as context annotations on hospital and SNF pages ("this facility is in a county where X% are uninsured").
- **Unique value:** Complements CDC PLACES (which covers health outcomes/behaviors) with socioeconomic root causes. Together, PLACES + SDOH give a complete "why is this county's health the way it is?" picture.
- **Limitations:** ACS 5-year estimates are smoothed over time. Small counties may have large margins of error. Not all SDOH indicators are documented in the catalog entry -- full field list requires downloading the data.
- **Note:** The AHRQ SDOH database is referenced in `non-cms-datasets.md` as a separate source. This CDC SDOH dataset is a different product from the same underlying ACS data, curated by CDC for alignment with PLACES.

### 3.2 VSRR Provisional County-Level Drug Overdose Death Counts

- **Catalog:** [catalog.data.gov/dataset/vsrr-provisional-county-level-drug-overdose-death-counts-d154f](https://catalog.data.gov/dataset/vsrr-provisional-county-level-drug-overdose-death-counts-d154f)
- **Source:** [data.cdc.gov/api/views/gb4e-yj24](https://data.cdc.gov/api/views/gb4e-yj24) (SODA API)
- **What it adds:** 12-month rolling provisional counts of drug overdose deaths by county. Based on death certificates flowing through the National Vital Statistics System. Covers all 50 states and DC.
- **Join key:** County FIPS (state + county FIPS code), direct join.
- **Format:** CSV, JSON via SODA API.
- **Update frequency:** Quarterly.
- **Linkage strategy:**
  1. Download via SODA API.
  2. Join on county FIPS code.
  3. Add `overdose_deaths` section to county manifest: annual count, rate per 100K (compute using county population from existing data), trend direction, comparison to state and national averages.
  4. Cross-link to Drug entity pages: counties with high overdose deaths could link to relevant drug pages (opioids), and vice versa.
- **Unique value:** Drug overdose is one of the most urgent public health crises. This is the only county-level, regularly updated mortality dataset specific to overdoses. Enables geographic hotspot identification and pairs with SAMHSA treatment facility data (see Section 7) and opioid prescribing data.
- **Limitations:** Provisional counts are subject to revision. Small counties may have suppressed counts for privacy. Not all states have equally timely death certificate reporting.

### 3.3 Medicare Specific Chronic Conditions -- County Level

- **Catalog:** Not individually listed on data.gov, but available at [data.cms.gov/medicare-chronic-conditions/specific-chronic-conditions](https://data.cms.gov/medicare-chronic-conditions/specific-chronic-conditions)
- **Source:** CMS Chronic Condition Data Warehouse (CCW), derived from 100% Medicare claims.
- **What it adds:** Prevalence, utilization, and per-capita spending for 21 specific chronic conditions (Alzheimer's, cancer, COPD, diabetes, heart failure, depression, etc.) among Medicare FFS beneficiaries, broken down by county and state. Also includes demographic breakdowns (age, sex, race).
- **Join key:** County FIPS (state/county FIPS code in geographic data files).
- **Format:** CSV download files, interactive dashboard.
- **Update frequency:** Annual (data years 2007--2018 in geographic reports; newer years may be available via dashboard).
- **Linkage strategy:**
  1. Download county-level CSV files from data.cms.gov.
  2. Join on county FIPS.
  3. Add `medicare_chronic_conditions` section to county manifests: prevalence rate for each of 21 conditions, per-capita Medicare spending by condition, comparison to state/national average.
  4. Cross-link to existing Condition entities: for each of the 21 conditions, county pages link to the matching CareGraph Condition entity. This strengthens the county-condition relationship beyond CDC PLACES (which measures general population prevalence) with Medicare-specific claims-based prevalence.
- **Unique value:** Claims-based chronic condition data is more precise than survey-based PLACES data for the Medicare population. Spending-per-condition data enables "how much does diabetes cost Medicare in this county?" analysis. The 21 CCW conditions overlap significantly with CareGraph's existing 21 PLACES conditions, enabling direct comparison (survey-estimated vs. claims-confirmed prevalence).
- **Limitations:** FFS-only (excludes Medicare Advantage beneficiaries, who now represent >50% of Medicare enrollment). Geographic reports may lag by 2+ years. County-level data may be suppressed for small populations.

### 3.4 Number of ACO Assigned Beneficiaries by County

- **Catalog:** [catalog.data.gov/dataset/number-of-accountable-care-organization-assigned-beneficiaries-by-county-c511a](https://catalog.data.gov/dataset/number-of-accountable-care-organization-assigned-beneficiaries-by-county-c511a)
- **Source:** [data.cms.gov](https://data.cms.gov) (MSSP data)
- **What it adds:** Aggregate count of MSSP ACO-assigned beneficiaries by county, for each ACO. This is the missing link for precise ACO-to-County relationships.
- **Join key:** ACO ID + County FIPS. Dual join to both ACO and County entities.
- **Format:** CSV (2021--2024), Excel (2016--2020).
- **Update frequency:** Annual.
- **Linkage strategy:**
  1. Download annual CSV.
  2. Parse ACO ID and county FIPS columns.
  3. **For ACO pages:** Replace current state-level county linking (capped at 20 counties per state) with precise county links weighted by beneficiary count. Show top counties by assigned beneficiaries.
  4. **For County pages:** Show which ACOs have assigned beneficiaries in this county, with counts. This is far more precise than the current "all counties in the ACO's state" approach.
  5. Add `aco_coverage` section to county manifest and improve `related` links on both ACO and county pages.
- **Unique value:** This dataset solves a known weakness in CareGraph's current cross-linking: ACO-to-County links are currently state-level approximations. This dataset provides the actual county-level assignment data. High priority.
- **Limitations:** Only covers MSSP ACOs (not ACO REACH or other models). Beneficiary counts may be suppressed for very small counties.

### 3.5 Medicare Monthly Enrollment by County

- **Catalog:** [catalog.data.gov/dataset/medicare-monthly-enrollment](https://catalog.data.gov/dataset/medicare-monthly-enrollment)
- **Source:** [data.cms.gov](https://data.cms.gov) (CMS Program Statistics)
- **What it adds:** Monthly counts of Medicare beneficiaries by county, broken down by: Original Medicare vs. Medicare Advantage, Part D enrollment, and demographic categories. Enables calculation of Medicare Advantage penetration rate per county.
- **Join key:** County FIPS (may use SSA county code requiring crosswalk).
- **Format:** CSV/Excel.
- **Update frequency:** Monthly.
- **Linkage strategy:**
  1. Download monthly or latest annual snapshot.
  2. Map SSA county codes to FIPS using the crosswalk already scaffolded in `etl/normalize/keys.py`.
  3. Add `enrollment` section to county manifest: total Medicare beneficiaries, Original Medicare count, MA count, MA penetration rate (%), Part D enrollment count.
  4. MA penetration rate is an important contextual indicator: counties with high MA penetration have fewer FFS beneficiaries, meaning CareGraph's FFS-based quality metrics cover a smaller share of the Medicare population there.
- **Unique value:** Contextualizes all other county-level Medicare data. A county with 80% MA penetration will have very different FFS utilization patterns than one with 20%. Essential denominator data.
- **Limitations:** Monthly files are large. SSA-to-FIPS crosswalk adds ETL complexity. MA penetration varies significantly by month (open enrollment effects).

### 3.6 Healthy People 2020 Health Disparities Overview

- **Catalog:** [catalog.data.gov/dataset/healthy-people-2020-overview-of-health-disparities-6cc72](https://catalog.data.gov/dataset/healthy-people-2020-overview-of-health-disparities-6cc72)
- **Source:** HHS Office of Disease Prevention and Health Promotion
- **What it adds:** Health disparity indicators tracking progress toward Healthy People 2020 targets across multiple dimensions: race/ethnicity, sex, education, income, disability, and geographic location.
- **Join key:** State or county FIPS (depending on granularity of underlying data).
- **Format:** CSV, JSON.
- **Linkage strategy:**
  1. Download and assess geographic granularity.
  2. If county-level: join on FIPS and add `health_disparities` section to county manifests.
  3. If state-level only: use as contextual data for state-level rollup pages (future entity type).
- **Unique value:** Health equity lens that no other dataset provides in CareGraph. Shows whether health outcomes are improving equitably across populations.
- **Limitations:** Healthy People 2020 cycle ended; Healthy People 2030 may have updated data. Granularity may be state-level only, limiting county-page usefulness. Assess actual data before committing to integration.

---

## 4. ACO Enrichments (join on ACO ID)

### 4.1 ACO Assigned Beneficiaries by County

See Section 3.4 above. This dataset enriches **both** ACO and County entities. It is the single highest-priority dataset for improving ACO cross-links.

### 4.2 Medicare Fee-for-Service Provider Enrollment (PECOS)

- **Catalog:** [catalog.data.gov/dataset/medicare-fee-for-service-public-provider-enrollment-b5fc6](https://catalog.data.gov/dataset/medicare-fee-for-service-public-provider-enrollment-b5fc6)
- **Source:** [data.cms.gov](https://data.cms.gov) (CMS Provider Enrollment, Chain, and Ownership System)
- **What it adds:** All actively enrolled Medicare FFS providers: provider type, specialty, enrollment date, practice location, and (critically) both NPI and organizational identifiers. This serves as a crosswalk between provider types.
- **Join key:** NPI, CCN, TIN (multiple identifiers per record).
- **Format:** CSV, updated quarterly.
- **Linkage strategy:**
  1. Download quarterly CSV.
  2. Use as a multi-key crosswalk: NPI -> CCN (for linking clinician data to facilities), TIN -> CCN (for linking ACO participant TINs to hospital/SNF CCNs), NPI -> practice location (for county assignment).
  3. Enriches ACO pages by resolving ACO Participant TINs to specific hospitals and SNFs.
  4. Also useful for building future Clinician entity pages.
- **Unique value:** Serves as a universal provider crosswalk. More current than the NBER NPI-to-CCN crosswalk (which is frozen at 2017). Updated quarterly.
- **Limitations:** Large dataset. May not include all provider-facility affiliations (a provider enrolled at one facility may practice at others). Data dictionary needed to confirm exact field names.

---

## 5. Drug Enrichments (join on generic name, NDC, or HCPCS)

### 5.1 NADAC (National Average Drug Acquisition Cost)

- **Catalog:** [catalog.data.gov/dataset/nadac-national-average-drug-acquisition-cost-2026](https://catalog.data.gov/dataset/nadac-national-average-drug-acquisition-cost-2026) (also 2013--2025)
- **Source:** [data.cms.gov](https://data.cms.gov) (Medicaid Drug Rebate Program)
- **What it adds:** Weekly pharmacy acquisition costs for drugs: the actual price pharmacies pay to acquire medications. Includes NDC code, drug name, NADAC per unit, pharmacy type (retail, mail order), effective date, and pricing methodology.
- **Join key:** NDC code -> generic drug name (requires NDC-to-generic-name crosswalk). Alternatively, match on drug name directly.
- **Format:** CSV, weekly updates. Available from 2013 to present.
- **Update frequency:** Weekly.
- **Linkage strategy:**
  1. Download latest NADAC CSV.
  2. Match drugs to CareGraph Drug entities using generic drug name (fuzzy match on `ndc_description` or `drug_name` field).
  3. Add `acquisition_cost` section to drug manifest: current NADAC per unit, pharmacy type breakdown, price trend (from historical weekly data), comparison to Medicare Part D spending (how much does Medicare pay vs. what the drug actually costs to acquire?).
- **Unique value:** Enables "acquisition cost vs. Medicare payment" comparison on drug pages. Shows the spread between what pharmacies pay and what Medicare pays -- a key transparency metric. Weekly updates provide near-real-time pricing.
- **Limitations:** Drug name matching can be imprecise (different salt forms, dosage strengths). NADAC covers pharmacy-dispensed drugs only (not physician-administered Part B drugs). Some drugs are excluded from NADAC surveys.

### 5.2 State Drug Utilization Data (Medicaid)

- **Catalog:** [catalog.data.gov/dataset/state-drug-utilization-data-2025](https://catalog.data.gov/dataset/state-drug-utilization-data-2025) (also 2000--2024)
- **Source:** [data.medicaid.gov](https://data.medicaid.gov) (Medicaid Drug Rebate Program)
- **What it adds:** Medicaid drug spending and utilization by state: NDC code, drug name, number of prescriptions, Medicaid reimbursement amount, and units dispensed. Available by state and quarter.
- **Join key:** NDC code -> generic drug name, matched to CareGraph Drug entities.
- **Format:** CSV via SODA API (data.medicaid.gov).
- **Update frequency:** Quarterly, with annual compilations.
- **Linkage strategy:**
  1. Download state-level drug utilization data.
  2. Aggregate by drug (generic name) across states to get national Medicaid totals.
  3. Match to CareGraph Drug entities by generic drug name.
  4. Add `medicaid_spending` section to drug manifest: total Medicaid prescriptions, total Medicaid reimbursement, Medicaid vs. Medicare spending comparison.
- **Unique value:** CareGraph currently shows only Medicare drug spending (Part D and Part B). Adding Medicaid spending gives a more complete public-payer picture. For drugs used heavily in Medicaid (e.g., buprenorphine for opioid use disorder), Medicaid data may be more relevant than Medicare data.
- **Limitations:** State-level granularity only (no county or provider). Drug name matching challenges (same as NADAC). Some states have incomplete reporting.

### 5.3 National Drug Code (NDC) Directory

- **Catalog:** [catalog.data.gov/dataset/national-drug-code-directory](https://catalog.data.gov/dataset/national-drug-code-directory)
- **Source:** FDA (updated daily)
- **What it adds:** Universal product identifier for drugs: NDC code, proprietary name, generic name (nonproprietary name), dosage form, route, labeler name, product type, marketing category, DEA schedule.
- **Join key:** NDC code (bridging key between NADAC, State Drug Utilization, FAERS, and CareGraph's drug entities).
- **Format:** CSV/JSON/XML via openFDA or direct download.
- **Linkage strategy:**
  1. Download NDC directory.
  2. Use as a crosswalk table: NDC -> generic drug name -> CareGraph Drug entity ID.
  3. Store as a lookup table in ETL for resolving NDC codes from other datasets (NADAC, State Drug Utilization) to CareGraph drug entities.
  4. Add metadata to drug pages: dosage forms available, routes of administration, labeler/manufacturer, DEA schedule if controlled.
- **Unique value:** Infrastructure dataset that enables all other NDC-keyed datasets to link to CareGraph. Also enriches drug pages with FDA regulatory metadata.
- **Limitations:** NDC codes change over time (repackaging, relabeling). Multiple NDCs can map to the same generic drug. Requires deduplication logic.

### 5.4 FDA Adverse Event Reporting System (FAERS)

- **Catalog:** [catalog.data.gov/dataset/fda-adverse-event-reporting-system-faers-latest-quartely-data-files](https://catalog.data.gov/dataset/fda-adverse-event-reporting-system-faers-latest-quartely-data-files)
- **Source:** FDA FAERS database
- **What it adds:** Adverse event and medication error reports submitted to FDA. Includes drug name, adverse reaction terms (MedDRA coded), patient outcomes (hospitalization, death, disability), reporter type, and report date.
- **Join key:** Drug generic name, matched to CareGraph Drug entities.
- **Format:** Quarterly ASCII/CSV files from FDA; also accessible via openFDA API.
- **Linkage strategy:**
  1. Download quarterly FAERS files or use openFDA API.
  2. Aggregate reports per drug: total adverse event reports, top 10 reported reactions, serious outcome counts, death reports.
  3. Match to CareGraph Drug entities by generic drug name.
  4. Add `safety_signals` section to drug manifest.
- **Unique value:** Safety dimension for drug pages. Currently CareGraph drug pages show only spending; FAERS adds a safety/risk lens.
- **Limitations:** Voluntary reporting (underreporting). Reports do not prove causation. Reporting rates vary by drug age and media attention.
- **Note:** Also documented in `non-cms-datasets.md` (as openFDA), but the data.gov catalog entry points to the raw quarterly files which are a different access path than the openFDA API.

### 5.5 FDA Orange Book (Therapeutic Equivalence Evaluations)

- **Catalog:** [catalog.data.gov/dataset/approved-drug-products-with-therapuetic-equivalence-evaluations-orange-book](https://catalog.data.gov/dataset/approved-drug-products-with-therapuetic-equivalence-evaluations-orange-book)
- **Source:** FDA
- **What it adds:** For each approved drug: therapeutic equivalence code (A/B rating), patent information, exclusivity dates, approved dosage forms and strengths, application holder (manufacturer). The A/B rating determines whether generic substitution is appropriate.
- **Join key:** Drug generic name + dosage form, matched to CareGraph Drug entities.
- **Format:** CSV/JSON via openFDA or direct download.
- **Linkage strategy:**
  1. Download Orange Book data.
  2. Match to CareGraph Drug entities by generic name.
  3. Add `patent_exclusivity` section to drug manifest: number of approved generics, patent expiration dates, exclusivity end dates, therapeutic equivalence ratings.
- **Unique value:** Explains why some drugs are expensive (patent protection, no generic competition) and predicts when prices may drop (patent cliff dates). Adds a market structure dimension to drug pages.
- **Limitations:** Only covers FDA-approved drugs (not compounded or OTC). Patent data is complex (multiple patents per product, patent challenges).

---

## 6. New Entity Type: HRSA-Funded Health Centers (FQHCs)

### 6.1 Find a Health Center

- **Catalog:** [catalog.data.gov/dataset/find-a-health-center-c0304](https://catalog.data.gov/dataset/find-a-health-center-c0304)
- **Source:** [findahealthcenter.hrsa.gov](https://findahealthcenter.hrsa.gov/) and [data.hrsa.gov](https://data.hrsa.gov)
- **What it adds:** Directory of ~1,400 HRSA-funded Federally Qualified Health Centers (FQHCs) and look-alikes: name, address, phone, services offered, hours of operation, patient capacity.
- **Join key:** No CCN (FQHCs have HRSA grant numbers, not CMS certification numbers). Address can be geocoded to county FIPS for county-level linking.
- **Format:** API (data.hrsa.gov), web tool.
- **Linkage strategy:**
  1. Query data.hrsa.gov API for all health center locations.
  2. Geocode addresses to county FIPS.
  3. **For county pages:** Add `health_centers` section with count of FQHCs in the county, names, and services. This directly addresses healthcare access.
  4. **For future FQHC entity pages:** Build a new entity type keyed by HRSA grant number, with links to county entities.
- **Unique value:** FQHCs are the primary care safety net for underserved communities. Showing their presence/absence on county pages contextualizes healthcare access. A county with 0 FQHCs and a Primary Care HPSA designation is a "healthcare desert."
- **Limitations:** No direct join to hospitals, SNFs, or ACOs. Requires geocoding step. No standard CMS identifier. FQHC entity pages would be a new entity type requiring new templates and builders.

### 6.2 HRSA HPSA & MUA/P by Address

- **Catalog:** [catalog.data.gov/dataset/find-shortage-areas-hpsa-mua-p-by-address](https://catalog.data.gov/dataset/find-shortage-areas-hpsa-mua-p-by-address)
- **Source:** [data.hrsa.gov](https://data.hrsa.gov)
- **What it adds:** Health Professional Shortage Area and Medically Underserved Area/Population designations. Includes shortage discipline (Primary Care, Mental Health, Dental), HPSA score (1--25), designation type (geographic, population, facility), and status.
- **Join key:** County FIPS for geographic HPSAs.
- **Format:** CSV, XLSX, KML, SHP from data.hrsa.gov download page.
- **Linkage strategy:**
  1. Download the full HPSA/MUA file from data.hrsa.gov.
  2. Filter to geographic (county-level) HPSAs.
  3. Join on county FIPS.
  4. Add `shortage_designations` section to county manifests: HPSA type, score, MUA status.
  5. Also add a shortage-area badge to hospital and SNF pages if they're located in a designated shortage area.
- **Unique value:** Directly answers "does this area have enough healthcare providers?" Essential context for county pages.
- **Note:** Already documented in `non-cms-datasets.md` as Tier 1 item #4. Listed here for completeness since it also appears in the HHS data.gov catalog.

---

## 7. New Entity Type: Behavioral Health / Substance Abuse Treatment Facilities

### 7.1 SAMHSA Mental Health Treatment Facilities Locator

- **Catalog:** [catalog.data.gov/dataset/mental-health-treatement-facilities-locator](https://catalog.data.gov/dataset/mental-health-treatement-facilities-locator)
- **Source:** SAMHSA
- **What it adds:** Directory of mental health treatment facilities: name, address, phone, services offered (individual therapy, group therapy, medication management, crisis intervention), treatment approaches, payment accepted, populations served.
- **Join key:** Address -> geocode to county FIPS. No CCN or NPI.
- **Format:** Accessible via SAMHSA's online locator tool. Bulk download availability uncertain.
- **Linkage strategy:**
  1. If bulk download is available: download and geocode to county FIPS.
  2. Aggregate to county level: count of mental health facilities, types of services available, treatment modalities.
  3. Add `mental_health_facilities` section to county manifests.
  4. Cross-link with HPSA Mental Health designation data.
- **Unique value:** Mental health access is a growing concern. Combined with HPSA Mental Health designation data and CDC PLACES mental health prevalence data, creates a complete mental health picture per county: need (prevalence) vs. supply (facilities) vs. designation (shortage status).
- **Limitations:** No standard healthcare identifier. Bulk download may require scraping the locator tool. Directory completeness varies.

### 7.2 SAMHSA Substance Abuse Treatment Facilities Locator

- **Catalog:** [catalog.data.gov/dataset/substance-abuse-treatment-facilities-locator](https://catalog.data.gov/dataset/substance-abuse-treatment-facilities-locator)
- **Source:** SAMHSA
- **What it adds:** Directory of substance abuse treatment facilities: name, address, services (detoxification, residential, outpatient, MAT/medication-assisted treatment), substances treated, payment accepted.
- **Join key:** Address -> geocode to county FIPS.
- **Format:** Same as mental health locator.
- **Linkage strategy:** Same as 7.1. Add `substance_abuse_facilities` section to county manifests.
- **Unique value:** Pairs with county-level drug overdose death data (Section 3.2) to show treatment supply vs. crisis demand. A county with high overdose deaths and few treatment facilities is in acute need.
- **Limitations:** Same as 7.1.

### 7.3 N-SUMHSS (National Substance Use and Mental Health Services Survey)

- **Catalog:** [catalog.data.gov/dataset/national-substance-use-and-mental-health-services-survey-n-sumhss-2021-data-on-substance-u](https://catalog.data.gov/dataset/national-substance-use-and-mental-health-services-survey-n-sumhss-2021-data-on-substance-u)
- **Source:** SAMHSA
- **What it adds:** Facility-level survey data: location, ownership, services, treatment approaches, client counts, staffing, special populations served. More structured and analytical than the locator directories.
- **Join key:** Facility address -> geocode to county FIPS.
- **Format:** Data files (format varies by year).
- **Linkage strategy:** Same geocoding approach. Aggregate to county level for richer facility characterization (average client counts, most common treatment approaches, staffing levels).
- **Unique value:** Adds quantitative depth (client counts, staffing) beyond the directory-level data in the locator tools.
- **Limitations:** 2021 data (most recent year on data.gov). Older N-SSATS versions (2005--2014) also available for historical trends.

### 7.4 Opioid Treatment Program (OTP) Providers

- **Catalog:** [catalog.data.gov/dataset/opioid-treatment-program-providers-9e369](https://catalog.data.gov/dataset/opioid-treatment-program-providers-9e369)
- **Source:** CMS
- **What it adds:** Providers enrolled in Medicare under the Opioid Treatment Program: provider name, NPI, address, phone, enrollment date. These are the facilities authorized to dispense methadone and provide MAT.
- **Join key:** NPI (can resolve to county via address). Also potentially joinable to ACO Participants (if OTP NPIs appear in ACO participant lists).
- **Format:** CSV.
- **Linkage strategy:**
  1. Download CSV.
  2. Geocode addresses to county FIPS.
  3. Add to county `substance_abuse_facilities` section with specific OTP designation.
  4. Optionally, link NPI to ACO or hospital entities via PECOS enrollment data (Section 4.2).
- **Unique value:** OTPs are the most critical infrastructure for opioid crisis response. Knowing which counties have OTPs (and which don't) is actionable for policy.
- **Limitations:** Only Medicare-enrolled OTPs. Some OTPs may operate outside Medicare enrollment.

---

## 8. Telehealth and Emerging Care Models

### 8.1 Medicare Telehealth Trends

- **Catalog:** [catalog.data.gov/dataset/medicare-telemedicine-snapshot](https://catalog.data.gov/dataset/medicare-telemedicine-snapshot)
- **Source:** CMS
- **What it adds:** Telehealth utilization among Medicare beneficiaries: counts of beneficiaries using telehealth, number of telehealth visits, visit types, geographic distribution, time trends from January 2020 through June 2024.
- **Join key:** Geographic level (state, possibly county) -- granularity needs verification.
- **Format:** CSV/JSON.
- **Linkage strategy:**
  1. Download and assess geographic granularity.
  2. If county-level: join on FIPS and add `telehealth` section to county manifests showing telehealth adoption rates.
  3. If state-level only: use as contextual data for state-level views.
- **Unique value:** Telehealth adoption varied dramatically by geography during and after COVID-19. Shows how care delivery is evolving in each area.
- **Limitations:** May be state-level only, limiting county-page usefulness. Data ends June 2024 as of last update. Pandemic-era utilization may not represent steady-state patterns.

---

## 9. Cross-Cutting Infrastructure Datasets

### 9.1 Medicare Provider and Supplier Taxonomy Crosswalk

- **Catalog:** [catalog.data.gov/dataset/medicare-provider-and-supplier-taxonomy-crosswalk](https://catalog.data.gov/dataset/medicare-provider-and-supplier-taxonomy-crosswalk) (listed on CMS page 1)
- **Source:** CMS
- **What it adds:** Maps provider types to healthcare taxonomy codes (NUCC taxonomy). Enables classification of providers by specialty and type across different datasets.
- **Join key:** Taxonomy code -> provider type classification.
- **Format:** CSV.
- **Linkage strategy:** Use as a reference table in ETL to classify providers from PECOS enrollment data and NPPES registry into meaningful categories (primary care, specialist, facility type, etc.).
- **Unique value:** Infrastructure dataset that improves provider classification accuracy across all entity types.

### 9.2 Restructured BETOS Classification System

- **Catalog:** [catalog.data.gov/dataset/restructured-betos-classification-system](https://catalog.data.gov/dataset/restructured-betos-classification-system) (listed on CMS page 1)
- **Source:** CMS
- **What it adds:** Taxonomy for grouping HCPCS codes into clinically meaningful categories: evaluation & management, procedures, imaging, tests, DME, other. Updated from the original Berenson-Eggers system.
- **Join key:** HCPCS code -> BETOS category.
- **Format:** CSV.
- **Linkage strategy:** Use as a lookup table to categorize outpatient services (from Medicare Outpatient Hospitals dataset, Section 1.4) and physician services into human-readable groups. Instead of showing "APC 5072" on a hospital page, show "Level 2 Musculoskeletal Procedures."
- **Unique value:** Makes APC and HCPCS codes understandable to non-clinical users. Essential for any future HCPCS entity type.

---

## 10. Summary: Recommended Priority Order

Ranked by linkage quality, implementation effort, and value to CareGraph users.

### Tier A: Direct join, high value, straightforward ETL

| # | Dataset | Entity | Join | Key Value |
|---|---------|--------|------|-----------|
| 1 | **ACO Beneficiaries by County** (3.4) | ACO + County | ACO ID + FIPS | Fixes the weakest cross-link in CareGraph |
| 2 | **Hospital Cost Report** (1.1) | Hospital | CCN | Only source for hospital financials |
| 3 | **SNF Cost Report** (2.1) | SNF | CCN | Only source for SNF financials |
| 4 | **HAC Reduction Program** (1.2) | Hospital | CCN | Third payment penalty (completes HRRP + VBP + HAC) |
| 5 | **CDC SDOH Measures** (3.1) | County | FIPS | Social determinants complement PLACES |
| 6 | **Medicare Chronic Conditions** (3.3) | County | FIPS | Claims-based condition prevalence + spending |
| 7 | **NADAC Drug Pricing** (5.1) | Drug | Drug name | Acquisition cost vs. Medicare payment |
| 8 | **NDC Directory** (5.3) | Drug (infra) | NDC | Enables all NDC-keyed drug datasets |

### Tier B: Direct join, moderate complexity

| # | Dataset | Entity | Join | Key Value |
|---|---------|--------|------|-----------|
| 9 | **Provider of Services File** (1.3) | Hospital | CCN | Bed breakdown, accreditation, teaching status |
| 10 | **PBJ Daily Staffing** (2.2) | SNF | CCN | Granular daily staffing trends |
| 11 | **Nursing Home Chain Performance** (2.3) | SNF | CCN (via ownership) | Chain-level quality context |
| 12 | **Medicare Monthly Enrollment** (3.5) | County | FIPS (via SSA) | MA penetration rate, enrollment counts |
| 13 | **Outpatient Hospitals by Provider** (1.4) | Hospital | CCN | Outpatient service volume complement |
| 14 | **PECOS Provider Enrollment** (4.2) | All (infra) | NPI/CCN/TIN | Universal provider crosswalk |
| 15 | **State Drug Utilization** (5.2) | Drug | Drug name | Medicaid spending complement |
| 16 | **Drug Overdose Deaths** (3.2) | County | FIPS | Overdose mortality hotspots |

### Tier C: Requires geocoding, new entity types, or uncertain data availability

| # | Dataset | Entity | Join | Key Value |
|---|---------|--------|------|-----------|
| 17 | **FAERS Adverse Events** (5.4) | Drug | Drug name | Drug safety signals |
| 18 | **FDA Orange Book** (5.5) | Drug | Drug name | Patent/generic competition data |
| 19 | **COVID-19 Nursing Home** (2.4) | SNF | CCN | Pandemic impact history |
| 20 | **Provider Relief Fund** (1.5) | Hospital + SNF | Fuzzy name | COVID financial support received |
| 21 | **FQHC Directory** (6.1) | County (new) | Geocode -> FIPS | Safety-net provider access |
| 22 | **SAMHSA Facility Locators** (7.1--7.4) | County (new) | Geocode -> FIPS | Behavioral health access |
| 23 | **Medicare Telehealth Trends** (8.1) | County | FIPS (if available) | Telehealth adoption |
| 24 | **Health Disparities** (3.6) | County | FIPS (if county-level) | Equity indicators |

### Infrastructure (no user-facing output, enables other datasets)

| # | Dataset | Purpose |
|---|---------|---------|
| 25 | **Taxonomy Crosswalk** (9.1) | Provider type classification |
| 26 | **BETOS Classification** (9.2) | Service code categorization |

---

## Appendix: Join Key Reference

| Join Key | Format | Entities Using It | Normalization |
|----------|--------|-------------------|---------------|
| CCN | 6-char zero-padded alphanumeric | Hospital, SNF, HHA, Hospice, Dialysis, ASC | `normalize_ccn()` in `etl/normalize/keys.py` |
| FIPS (county) | 5-digit zero-padded | County | `normalize_fips()` in `etl/normalize/keys.py` |
| ACO ID | Alphanumeric (e.g., `A1001`) | ACO | `normalize_aco_id()` in `etl/normalize/keys.py` |
| NPI | 10-digit | Clinicians, some facilities | Not yet normalized; scaffold exists |
| NDC | 10-digit (4-4-2 or 5-3-2 or 5-4-1) | Drug | Needs new normalizer; variable segment lengths |
| SSA County Code | 5-digit | Some CMS enrollment files | `load_ssa_to_fips_crosswalk()` scaffold exists |
| Drug generic name | Free text | Drug | Fuzzy match to existing drug entities |

---

## Appendix: Datasets Investigated but Not Recommended

| Dataset | Reason for Exclusion |
|---------|---------------------|
| NIH PubChem datasets (8,900+ on data.gov) | Chemical/molecular data, no healthcare provider or geographic join key |
| SAMHSA NSDUH survey microdata | Restricted access, not public-use at county level |
| ACF TANF/Child Welfare data | Different policy domain (welfare, not healthcare delivery) |
| HCUP NIS/NEDS/SID | Restricted access files requiring purchase from AHRQ |
| HCUPnet | Online query tool only, no bulk download |
| CDC WONDER Mortality (non-overdose) | Broad mortality statistics, overlaps with county health data already available |
| FDA Food/Pet Food Recalls | Not healthcare delivery related |
| FDA Medical Device Recalls | No join to CareGraph entities (device-level, not facility-level) |
| Medicare Claims RIF/LDS | Research-restricted, not public |
