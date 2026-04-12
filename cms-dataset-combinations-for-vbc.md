# Strategic Dataset Combinations for Value-Based Care Organizations

**Prepared:** April 2026  
**Source Portal:** [data.cms.gov](https://data.cms.gov/) (388+ datasets) plus key external public data sources  
**Audience:** Leaders at Accountable Care Organizations and other value-based care entities

---

## Table of Contents

1. [Post-Acute Care Network Optimization](#1-post-acute-care-network-optimization)
2. [Population Risk Stratification Using Community-Level SDOH](#2-population-risk-stratification-using-community-level-sdoh)
3. [Physician Network Performance Profiling](#3-physician-network-performance-profiling)
4. [Readmission Root-Cause Analysis Across the Care Continuum](#4-readmission-root-cause-analysis-across-the-care-continuum)
5. [ACO Competitive Benchmarking and Market Intelligence](#5-aco-competitive-benchmarking-and-market-intelligence)
6. [Health Equity Gap Analysis](#6-health-equity-gap-analysis)
7. [Drug Spending Optimization](#7-drug-spending-optimization)
8. [Workforce Gap Analysis for Network Adequacy](#8-workforce-gap-analysis-for-network-adequacy)
9. [Episode-Level Spending Decomposition](#9-episode-level-spending-decomposition)
10. [Chronic Disease Burden Mapping for Care Management Targeting](#10-chronic-disease-burden-mapping-for-care-management-targeting)
11. [Appendix A: CMS Dataset Catalog](#appendix-a-cms-dataset-catalog)
12. [Appendix B: External Datasets for Linkage](#appendix-b-external-datasets-for-linkage)
13. [Appendix C: Technical Linking Notes](#appendix-c-technical-linking-notes)

---

## 1. Post-Acute Care Network Optimization

**Strategic rationale:** Post-acute care (especially SNF) is the single largest controllable cost lever for ACOs. Combining datasets lets you build a data-driven preferred SNF/HHA network.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **SNF VBP Facility-Level Dataset** | data.cms.gov (Provider Data) | CCN (facility ID) |
| **Nursing Home Five-Star Ratings / MDS Quality Measures** | data.cms.gov (Provider Data) | CCN |
| **Medicare Claims Quality Measures for Nursing Homes** (rehospitalization, ED visits, successful community discharge) | data.cms.gov (Provider Data) | CCN |
| **Payroll-Based Journal Staffing Data** (actual daily nurse staffing hours per resident day) | data.cms.gov | CCN |
| **Nursing Home Penalties & Deficiencies** | data.cms.gov (Provider Data) | CCN |
| **ACO SNF Affiliates** | data.cms.gov (MSSP) | CCN + ACO ID |
| **Medicare Post-Acute Care Utilization - SNF** (payments, LOS, case-mix) | data.cms.gov | CCN |

### What This Unlocks

A composite SNF scorecard combining quality outcomes (readmission rates from claims data), process quality (staffing adequacy from PBJ), regulatory risk (penalties/deficiencies), cost efficiency (PAC utilization payments), and VBP performance -- all at the individual facility level. You can rank every SNF in your market and steer discharges to the highest-value partners. Replicate the same pattern for Home Health using HHA quality, HHCAHPS, and HHVBP datasets.

---

## 2. Population Risk Stratification Using Community-Level SDOH

**Strategic rationale:** Clinical risk scores (HCC) miss social determinants. Layering community SDOH data onto your attributed population reveals why certain geographies have worse outcomes despite similar clinical profiles.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **MSSP County-Level Expenditure and Risk Score Data** | data.cms.gov | County FIPS |
| **Medicare Geographic Variation (County)** | data.cms.gov | County FIPS |
| **CDC PLACES** (chronic disease prevalence at census tract level) | data.cdc.gov | Census tract FIPS |
| **CDC/ATSDR Social Vulnerability Index** | CDC | Census tract FIPS |
| **USDA Food Access Research Atlas** (food desert flags) | USDA | Census tract FIPS |
| **AHRQ SDOH Database** (income, transportation, broadband, insurance) | AHRQ | County/Tract/ZIP |

### Linking Approach

Use the **HUD-USPS ZIP-to-Census Tract crosswalk** to map beneficiary ZIPs to tracts. CMS data uses SSA county codes -- apply the **NBER SSA-to-FIPS crosswalk** first.

### What This Unlocks

You can identify census tracts in your service area where (a) diabetes prevalence is 2x the county average (PLACES), (b) residents live in food deserts (USDA), (c) social vulnerability is high (SVI), and (d) Medicare spending per capita exceeds the benchmark (Geographic Variation). These are the tracts where community health worker programs, medically-tailored meals, and transportation assistance will yield the highest return on investment.

---

## 3. Physician Network Performance Profiling

**Strategic rationale:** Combining utilization data with quality data at the individual NPI level reveals which providers are high-cost/low-quality vs. high-value.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **Medicare Physician & Other Practitioners - by Provider** (total charges, payments, beneficiary count, HCC risk scores) | data.cms.gov | NPI |
| **Medicare Physician & Other Practitioners - by Provider and Service** (HCPCS-level detail) | data.cms.gov | NPI |
| **MIPS Clinician Public Reporting - Overall Performance** (final MIPS score, category scores) | data.cms.gov (Provider Data) | NPI |
| **MIPS Clinician Public Reporting - Measures and Attestations** (individual quality measure performance) | data.cms.gov (Provider Data) | NPI |
| **Medicare Part D Prescribers - by Provider** (prescribing volume, opioid/antibiotic flags, beneficiary risk) | data.cms.gov | NPI |
| **ACO Participants** (TIN-to-ACO mapping) | data.cms.gov (MSSP) | TIN |
| **Facility Affiliation Data** (clinician-to-hospital links) | data.cms.gov (Provider Data) | NPI |

### What This Unlocks

For every clinician in your ACO, you have: total cost profile (utilization data), risk-adjusted panel complexity (HCC scores from the provider file), quality performance (MIPS scores), prescribing patterns (Part D data), and which facilities they practice at. This enables provider-level variation analysis -- e.g., finding internists whose per-beneficiary costs are 30% above risk-adjusted peers but whose MIPS quality scores are below average. These are actionable coaching opportunities.

---

## 4. Readmission Root-Cause Analysis Across the Care Continuum

**Strategic rationale:** Readmissions are a quality gate in MSSP. By linking hospital, SNF, home health, and community data, you can identify the full chain of failure.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **Hospital Readmissions Reduction Program** (excess readmission ratios by condition) | data.cms.gov | CCN |
| **Unplanned Hospital Visits - Hospital** (EDAC days, readmission rates) | data.cms.gov | CCN |
| **Medicare Hospital Spending by Claim** (spending breakdown: during stay vs. 1-30 days post-discharge) | data.cms.gov | CCN |
| **Nursing Home Claims Quality Measures** (rehospitalization from SNF) | data.cms.gov | CCN |
| **Home Health Quality** (acute care hospitalization rate, ED use) | data.cms.gov | CCN |
| **Chronic Conditions - Specific** (readmission rate by condition, by county) | data.cms.gov | County FIPS |
| **HCAHPS Patient Survey** (discharge information domain) | data.cms.gov | CCN |

### What This Unlocks

For a given hospital with high heart failure readmissions, you can trace whether the problem is: (a) inadequate discharge planning (low HCAHPS discharge information scores), (b) high post-discharge spending suggesting complications (MSPB claim breakdown), (c) poor SNF care downstream (SNF rehospitalization rates), or (d) community-level factors (county-level HF readmission rates from Chronic Conditions data). Each root cause implies a different intervention.

---

## 5. ACO Competitive Benchmarking and Market Intelligence

**Strategic rationale:** Every MSSP ACO's financial and quality results are public. Combining these with participant rosters and market data reveals competitor strategies.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **MSSP Performance Year Financial and Quality Results** (savings/losses, quality scores, benchmarks) | data.cms.gov | ACO ID |
| **ACO Participants** (TIN/NPI rosters per ACO) | data.cms.gov | ACO ID + TIN |
| **Accountable Care Organizations** (track/level, size, agreement dates) | data.cms.gov | ACO ID |
| **ACO Beneficiary Counts by County** | data.cms.gov | ACO ID + County FIPS |
| **ACO REACH Financial and Quality Results** | data.cms.gov | ACO ID |
| **Market Saturation & Utilization - County** | data.cms.gov | County FIPS |
| **Medicare Monthly Enrollment** (county-level beneficiary counts) | data.cms.gov | County FIPS |

### What This Unlocks

You can map every competing ACO's attributed lives by county, see which providers they include, track their savings rate over time, and compare their quality scores to yours. Overlay county-level market saturation data to find underserved counties with significant FFS beneficiary populations -- these are growth opportunities. Track which ACOs moved from BASIC to ENHANCED risk tracks (and whether they succeeded), informing your own risk-track decisions.

---

## 6. Health Equity Gap Analysis

**Strategic rationale:** CMS is building health equity into ACO benchmarking. Proactively identifying and addressing disparities positions your ACO for both better outcomes and favorable adjustment.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **Mapping Medicare Disparities - by Population** (outcomes by race, dual status, age, chronic conditions) | data.cms.gov (tool) | County/State |
| **Health Equity - Hospital** (dual-eligible %, disability %, racial composition) | data.cms.gov (Provider Data) | CCN |
| **MSSP County-Level Expenditure Data** (expenditure by enrollment type: dual vs. non-dual, ESRD, disabled) | data.cms.gov | County FIPS |
| **CDC SVI** (vulnerability by theme: socioeconomic, household composition, minority status, housing/transport) | CDC | Census tract FIPS |
| **ACS 5-Year Estimates** (poverty, education, language, insurance by race/ethnicity) | Census Bureau | Census tract FIPS |
| **County Health Rankings** (premature death, poor health days, income inequality, social associations) | UW-PHI | County FIPS |
| **Chronic Conditions - Specific** (prevalence by race/ethnicity and dual status) | data.cms.gov | County FIPS |

### What This Unlocks

Identify specific disparities in your attributed population -- e.g., Black/African American beneficiaries in County X have 2x the diabetes prevalence and 1.5x the readmission rate vs. non-Hispanic White beneficiaries, and the tracts where they live score in the 90th percentile on SVI. This enables targeted health equity interventions (culturally competent care management, CHW deployment) and documentation for CMS health equity adjustment consideration.

---

## 7. Drug Spending Optimization

**Strategic rationale:** Combining provider-level prescribing data with drug spending trends and specialty information reveals high-value pharmacy interventions.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **Medicare Part D Prescribers - by Provider and Drug** (NPI x drug: claims, costs, beneficiary count) | data.cms.gov | NPI + Drug name |
| **Medicare Part D Spending by Drug** (total national spending, avg cost, YoY trends) | data.cms.gov | Drug name |
| **Medicare Part D Opioid Prescribing Rates - by Geography** | data.cms.gov | County/ZIP |
| **Medicare Part B Spending by Drug** (physician-administered drugs) | data.cms.gov | Drug name |
| **Medicare Part B Discarded Drug Units** (waste from single-use vials) | data.cms.gov | Drug name |

### What This Unlocks

Identify your ACO's highest-spending drugs, find providers prescribing brand when generics/biosimilars exist, flag opioid prescribing outliers by geography, and quantify Part B drug waste. For example: if Provider X prescribes Brand Drug Y for 200 beneficiaries at $X/claim while the national average is shifting to Generic Z at 60% lower cost, that's a pharmacy management conversation worth having.

---

## 8. Workforce Gap Analysis for Network Adequacy

**Strategic rationale:** Combining provider supply data with utilization and enrollment data reveals where your network has gaps that drive avoidable spending.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **HRSA Area Health Resources Files** (physicians by specialty, NPs, PAs per county) | HRSA | County FIPS |
| **Medicare Monthly Enrollment** (beneficiary count by county) | data.cms.gov | County FIPS |
| **Medicare Geographic Variation - County** (per capita spending, utilization by service type) | data.cms.gov | County FIPS |
| **Market Saturation & Utilization - County** | data.cms.gov | County FIPS |
| **Clinician National Downloadable File** (active clinicians by specialty and location) | data.cms.gov (Provider Data) | NPI, ZIP |
| **Medicare Telehealth Trends** | data.cms.gov | National |

### What This Unlocks

Counties where your ACO has attributed lives but low PCP-to-beneficiary ratios (AHRF + Enrollment) correlate with higher ED utilization and spending (Geographic Variation). These are candidates for telehealth expansion, advanced practice provider recruitment, or FQHC partnerships. The Market Saturation data flags where services are over/under-utilized relative to capacity.

---

## 9. Episode-Level Spending Decomposition

**Strategic rationale:** Understanding *where* spending happens during a care episode (pre-admission, inpatient, post-acute, follow-up) reveals the most actionable cost levers.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **Medicare Hospital Spending by Claim** (spending by claim type and episode period) | data.cms.gov | CCN |
| **Medicare Inpatient Hospitals - by Provider and Service** (DRG-level discharges, payments) | data.cms.gov | CCN + DRG |
| **Medicare Spending Per Beneficiary - Hospital** (MSPB ratio vs. national median) | data.cms.gov | CCN |
| **Hospital Cost Reports** (cost-to-charge ratios, case mix, margins) | data.cms.gov | CCN |
| **HVBP Efficiency Scores** (MSPB performance) | data.cms.gov | CCN |

### What This Unlocks

For Hospital A, the MSPB ratio is 1.08 (8% above national median). The spending-by-claim breakdown shows the overage is concentrated in SNF claims 4-30 days post-discharge, not the inpatient stay itself. The DRG-level data shows it's driven by joint replacement and COPD cases. This points to a post-acute care management intervention (preferred SNF network, transitional care programs) rather than inpatient length-of-stay reduction.

---

## 10. Chronic Disease Burden Mapping for Care Management Targeting

**Strategic rationale:** Overlaying CMS chronic condition prevalence data with community health data identifies exactly which conditions, in which geographies, with which social barriers, need intervention.

### Datasets to Combine

| Dataset | Source | Join Key |
|---|---|---|
| **Specific Chronic Conditions** (prevalence, spending, readmissions, ED visits by condition -- county level, with race/dual breakdowns) | data.cms.gov | County FIPS |
| **Multiple Chronic Conditions** (co-occurring condition patterns, spending multipliers) | data.cms.gov | County FIPS |
| **CDC PLACES** (census tract-level prevalence of diabetes, COPD, CHF, depression, etc.) | data.cdc.gov | Tract FIPS |
| **USDA Food Access Research Atlas** (food deserts) | USDA | Tract FIPS |
| **Medicare Part D Prescribers - by Geography** (medication patterns by area) | data.cms.gov | State/County |
| **Opioid Prescribing Rates by Geography** | data.cms.gov | County/ZIP |

### What This Unlocks

In your service area, County Y has diabetes prevalence 4 points above the state average (CMS Chronic Conditions). Drilling into PLACES data, this is concentrated in 6 census tracts that are all classified as food deserts (USDA). The county's opioid prescribing rate is in the 80th percentile nationally. This tells you: deploy a diabetes care management program with integrated nutrition support in those 6 tracts, and launch a concurrent opioid stewardship initiative county-wide.

---

## Appendix A: CMS Dataset Catalog

### A.1 ACO / Medicare Shared Savings Program (MSSP)

| Dataset | Contents | Granularity | Update Frequency |
|---------|----------|-------------|------------------|
| Performance Year Financial and Quality Results | Savings/losses, quality scores, benchmark expenditures, assigned beneficiaries, risk scores for each MSSP ACO | ACO-level | Annual |
| Accountable Care Organizations | ACO name, track/risk arrangement, years in program, number of assigned beneficiaries | ACO-level | Annual |
| Accountable Care Organization Participants | Participating TINs/providers in each ACO, track status | Provider-level within ACO | Annual |
| ACO SNF Affiliates | SNF affiliates of each ACO | Facility-level | Annual |
| County-level Aggregate Expenditure and Risk Score Data on Assignable Beneficiaries | Per capita Parts A&B FFS expenditures, CMS-HCC risk scores, person-years by enrollment type | County-level | Annual |
| Number of ACO Assigned Beneficiaries by County | Count of beneficiaries assigned to MSSP ACOs by county | County-level | Annual |
| Advance Investment Payment Spend Plan | AIP spending categories, projected vs actual spend for low-revenue ACOs | ACO-level | Annual |

**URL base:** `https://data.cms.gov/medicare-shared-savings-program/`

### A.2 ACO REACH / Innovation Center Models

| Dataset | Contents | Granularity | Update Frequency |
|---------|----------|-------------|------------------|
| ACO REACH Financial and Quality Results | Risk arrangement, stop loss, capitation, savings rate, quality results | ACO-level | Annual |
| ACO REACH Aligned Beneficiaries | Counties, eligibility months, total aligned beneficiaries | County/beneficiary | Annual |
| ACO REACH Eligible Beneficiaries | Reference population, average risk scores | Beneficiary-related | Annual |
| ACO REACH Providers | Participant and preferred providers, capitation arrangements | Provider-level | Annual |
| REACH ACOs | Directory of participating REACH ACOs | ACO-level | Annual |
| Next Generation ACO Model Data | Financial and quality results for Next Gen ACOs (predecessor) | ACO-level | Annual |
| Pioneer ACO Model | Results from the original Pioneer ACO program | ACO-level | Historical |
| Medicare Alternative Payment Model Adoption | Tracks APM adoption rates across Medicare | National/state | Annual |

### A.3 Hospital Quality Measures & Value-Based Programs

#### Hospital Value-Based Purchasing (HVBP)

| Dataset | Dataset ID | Contents |
|---------|-----------|----------|
| HVBP Total Performance Score | ypbt-wvdk | Domain scores and TPS for each hospital |
| HVBP Clinical Outcomes Domain Scores | pudb-wetr | Mortality, complications for AMI, HF, pneumonia, COPD, CABG, THA/TKA |
| HVBP Efficiency Scores | su9h-3pvj | MSPB performance |
| HVBP Person & Community Engagement | avtz-f2ge | HCAHPS dimension scores |
| HVBP Safety | dgmq-aat3 | PSI, HAI, MRSA, SSI, CLABSI, CAUTI, C. diff |
| FY2024 VBP Payment Impact Tables (4 datasets) | 5gv4-jwyv / xrgf-x36b / u625-zae7 / vtqa-m4zn | Net payment changes, incentive amounts |

#### Hospital Readmissions & Unplanned Visits

| Dataset | Dataset ID | Contents | Granularity |
|---------|-----------|----------|-------------|
| Hospital Readmissions Reduction Program | 9n3s-kdb3 | Readmission ratios for AMI, HF, pneumonia, COPD, THA/TKA, CABG | Provider-level |
| Unplanned Hospital Visits | 632h-zaca (hospital) / cvcs-xecj (national) / 4gkm-5ypv (state) | EDAC, readmissions, outpatient surgery visits | Hospital/National/State |

#### Hospital-Acquired Conditions & Safety

| Dataset | Dataset ID | Contents |
|---------|-----------|----------|
| HAC Reduction Program | yq43-i98g | Total HAC scores, PSI, infection measures |
| Healthcare Associated Infections | 77hc-ibv8 (hospital) / yd3s-jyhd (national) / k2ze-bqvw (state) | MRSA, C. diff, CLABSI, CAUTI, SSI |
| CMS Medicare PSI-90 | muwa-iene | Patient safety composite and component measures |

#### Mortality & Complications

| Dataset | Dataset ID | Contents |
|---------|-----------|----------|
| Complications and Deaths | ynj2-r877 (hospital) / qqw3-t4ie (national) / bs2r-24vh (state) | 30-day mortality rates, hip/knee complications, PSI |

#### Patient Experience

| Dataset | Dataset ID | Contents |
|---------|-----------|----------|
| HCAHPS Patient Survey | dgck-syfz (hospital) / 99ue-w85f (national) / 84jm-wiui (state) | Nurse/doctor communication, responsiveness, pain management, cleanliness, discharge info, overall rating |
| OAS CAHPS | yizn-abxn (facility) / s5pj-hua3 (national) / 6pfg-whmx (state) | Outpatient surgery patient experience |

#### Other Hospital Quality

| Dataset | Contents |
|---------|----------|
| Timely and Effective Care (Hospital/National/State) | ED throughput, preventive care, immunization |
| Outpatient Imaging Efficiency (Hospital/National/State) | Appropriate use of CT, MRI |
| Promoting Interoperability | Hospital EHR adoption |
| Maternal Health Measures | Structural measures for obstetric care |
| Hospital General Information (xubh-q36u) | Addresses, type, overall star rating |

### A.4 Medicare Spending & Cost

| Dataset | Contents | Granularity | Update Frequency |
|---------|----------|-------------|------------------|
| Medicare Spending Per Beneficiary (MSPB) | Whether Medicare spends more/less than expected per episode | Hospital, National, State | Quarterly |
| Medicare Hospital Spending by Claim | Average spending by claim type during MSPB episodes | Hospital-level | Quarterly |
| Medicare Geographic Variation - National, State & County | Per capita spending, utilization, quality across geographies | National, State, County | Annual |
| Medicare Geographic Variation - by HRR | Same as above by Hospital Referral Region | HRR | Annual |
| Medicare Advantage Geographic Variation | MA spending and utilization | National, State | Annual |
| Hospital Provider Cost Report | Facility characteristics, utilization, cost/charges, financial info | Provider | Annual |
| SNF Cost Report | Same for skilled nursing facilities | Provider | Annual |
| Home Health Agency Cost Report | Same for HHAs | Provider | Annual |
| Medicare Part B Spending by Drug | Drug spending in outpatient settings | National | Annual |
| Medicare Part D Spending by Drug | Prescription drug spending | National | Annual |
| Quarterly Part B/D Spending by Drug | Near-real-time drug spending | National | Quarterly |

### A.5 Provider Utilization & Claims Data

| Dataset | Contents | Granularity | Time Period |
|---------|----------|-------------|-------------|
| Medicare Physician & Other Practitioners - by Provider | Services, payments, charges, beneficiary demographics per NPI | Individual NPI | 2013-2023 |
| Medicare Physician - by Provider and Service | Same broken down by HCPCS code and place of service | NPI + Service | 2013-2023 |
| Medicare Physician - by Geography and Service | Aggregated by state/national, HCPCS, provider type | National, State | 2013-2023 |
| Medicare Inpatient Hospitals - by Provider | Discharges, payments, charges for 3,000+ hospitals | Provider | 2013-2023 |
| Medicare Inpatient Hospitals - by Provider and Service | Same by DRG | Provider + DRG | 2013-2023 |
| Medicare Inpatient Hospitals - by Geography and Service | Aggregated by geography | National, State | 2013-2023 |
| Medicare Outpatient Hospitals - by Provider and Service | Outpatient services, payments, charges | Provider + APC | 2015-2023 |
| Medicare Part D Prescribers - by Provider | Prescribing patterns per provider | Individual NPI | 2013-2023 |
| Medicare Part D Prescribers - by Provider and Drug | Drug-level prescribing per provider | NPI + Drug | 2013-2023 |
| Medicare DME - by Supplier/Referring Provider | DME utilization and payments | Supplier/Provider | Multi-year |
| Medicare Post-Acute Care Utilization (HHA, Hospice, IRF, LTCH, SNF) | PAC utilization, payments, case-mix | Provider, State, National | 2014-2023 |
| Hospital Service Area | Geographic service areas for hospitals | Hospital/geography | Multi-year |

### A.6 Beneficiary Enrollment & Demographics

| Dataset | Contents | Granularity | Update Frequency |
|---------|----------|-------------|------------------|
| Medicare Monthly Enrollment | Current monthly beneficiary counts with coverage breakdowns | National, State, County | Monthly |
| CMS Program Statistics - Medicare Total Enrollment | Total enrollment trends | National, State | Annual |
| CMS Program Statistics - Original Medicare Enrollment | FFS enrollment | National, State | Annual |
| CMS Program Statistics - Medicare Advantage Enrollment | MA/other health plan enrollment | National, State | Annual |
| CMS Program Statistics - Part D Enrollment | Prescription drug plan enrollment | National, State | Annual |
| CMS Program Statistics - Medicare-Medicaid Dual Enrollment | Dual eligible counts | National, State | Annual |
| CMS Program Statistics - Medicare Deaths | Mortality among beneficiaries | National, State | Annual |
| Medicare Current Beneficiary Survey (MCBS) - Cost Supplement | Expenditures and payment sources for all services (microdata PUF) | Beneficiary-level (de-identified) | Annual |

### A.7 Quality Payment Program (QPP) / MIPS

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| PY 2023 Clinician Public Reporting: Overall MIPS Performance | Final MIPS scores, performance category scores per clinician | Individual clinician |
| PY 2023 Clinician Public Reporting: MIPS Measures and Attestations | Quality, PI, and Improvement Activities performance | Individual clinician |
| PY 2023 Group Public Reporting: MIPS Measures and Attestations | Same at group/TIN level | Group/TIN |
| PY 2023 Group Public Reporting: Patient Experience | CAHPS for MIPS at group level | Group/TIN |
| Quality Payment Program Experience | QPP participation and results | National |

### A.8 Chronic Conditions

**URL:** `https://data.cms.gov/medicare-chronic-conditions`

**21 Chronic Conditions Tracked:** Alzheimer's/Dementia, Arthritis (OA & RA), Asthma, Atrial Fibrillation, Autism Spectrum Disorders, Cancer (Breast, Colorectal, Lung, Prostate), Chronic Kidney Disease, COPD, Depression, Diabetes, Heart Failure, Hepatitis (B & C), HIV/AIDS, Hyperlipidemia, Hypertension, Ischemic Heart Disease, Osteoporosis, Schizophrenia/Psychotic Disorders, Stroke.

**Measures per Condition:**

- Prevalence (% of FFS beneficiaries with the condition)
- Total Medicare Standardized Per Capita Spending
- Total Medicare Per Capita Spending (actual)
- 30-day Hospital Readmission Rate
- Emergency Room Visits per 1,000 Beneficiaries

**Granularity:** National, State, County (FIPS codes).

**Demographic Breakdowns:** Age (<65 vs 65+), Sex, Race/Ethnicity (Non-Hispanic White, Black/African American, Asian/Pacific Islander, Hispanic, American Indian/Alaska Native), Dual Eligibility Status.

### A.9 Market Intelligence & Geographic Analysis

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| Market Saturation & Utilization - State-County | Medicare utilization relative to market capacity by service type | State, County |
| Market Saturation & Utilization - Core-Based Statistical Areas | Same by CBSA/MSA | CBSA/MSA |
| Medicare Telehealth Trends | Telehealth utilization since January 2020 | National + breakdowns |

### A.10 Nursing Home / SNF Quality

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| SNF VBP Facility-Level Dataset | FY 2026 SNF VBP performance results, readmission measures | Provider |
| MDS Quality Measures | Quality measures from Minimum Data Set assessments | Provider |
| Medicare Claims Quality Measures | Claims-based quality measures for nursing homes | Provider |
| Provider Information | Star ratings, beds, staffing, quality scores | Provider |
| SNF Quality Reporting Program | SNF-specific quality measures | Provider, National |
| Penalties, Deficiencies, Inspections | Regulatory compliance data | Provider |
| Payroll Based Journal Staffing (3 datasets) | Daily nurse and non-nurse staffing levels | Provider |
| Nursing Home Chain Performance Measures | Quality across chains/systems | Chain-level |

### A.11 Home Health & Hospice

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| Expanded Home Health VBP Model | Agency-level and cohort-level performance scores | Provider, Cohort |
| Home Health Care Agencies | Quality ratings, patient outcomes | Provider |
| Home Health CAHPS (HHCAHPS) | Patient survey results | Provider, State, National |
| Hospice Quality Reporting | Quality measures | Provider, State, National |
| Hospice CAHPS | Patient/family survey data | Provider, State, National |

### A.12 Dialysis / ESRD Quality

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| ESRD QIP Total Performance Scores | Payment Year 2026 facility scores and payment reductions | Facility |
| ESRD QIP Individual Measures | Dialysis Adequacy, Hospitalization Ratio, Readmission Ratio, Transfusion Ratio, Catheter, Infection, Depression Screening, Medication Reconciliation | Facility |
| Kidney Care Choices Model | ESRD value-based payment model results | Model participant |
| Comprehensive ESRD Care Model | ESCO performance, shared savings/losses | Model participant |

### A.13 Opioid & Prescription Monitoring

| Dataset | Granularity |
|---------|-------------|
| Medicare Part D Opioid Prescribing Rates - by Geography | National, State, County, ZIP |
| Medicaid Opioid Prescribing Rates - by Geography | State, County |
| Medicare Part D Prescribers - by Provider and Drug | Individual NPI + Drug |

### A.14 Disparities & Health Equity

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| Mapping Medicare Disparities - by Population | Chronic condition prevalence, ED visits, hospitalizations, readmissions, spending by demographics | National, State, County |
| Mapping Medicare Disparities - by Hospital | Hospital-level disparities | Hospital |
| Mapping Disparities by Social Determinants of Health | SDOH indicators linked to health outcomes | Geographic |
| Health Equity - Hospital | Dual-eligible %, disability %, racial composition | Hospital |
| Health Equity - State | State-level health equity aggregates | State |

### A.15 Risk Adjustment / HCC Data

Datasets containing HCC risk score data:

- **Geographic Variation PUF** -- average HCC risk scores at state, county, and HRR levels
- **MA Geographic Variation** -- MA risk score data at national and state levels
- **MSSP County-Level Expenditure and Risk Score Data** -- county-level risk scores for MSSP-assignable beneficiaries
- **Medicare Part D Prescribers - by Provider** -- beneficiary risk scores per prescribing provider
- **Medicare Physician & Other Practitioners - by Provider** -- average HCC risk score of each provider's Medicare panel

### A.16 Cost Reports

| Dataset | Contents | Granularity |
|---------|----------|-------------|
| Hospital Provider Cost Report | Revenue, costs, charges, case mix, payer mix, margins | Hospital |
| Skilled Nursing Facility Cost Report | Revenue, costs, utilization | SNF |
| Home Health Agency Cost Report | Revenue, costs | HHA |

---

## Appendix B: External Datasets for Linkage

### B.1 CDC PLACES: Local Data for Better Health

**Source:** [data.cdc.gov](https://data.cdc.gov/)

**40 measures** across 6 categories: health outcomes (diabetes, COPD, heart disease, stroke, cancer, kidney disease, depression), preventive services use (annual checkups, cholesterol screening, mammography), health risk behaviors (smoking, binge drinking, physical inactivity, obesity), disabilities, health status, and health-related social needs.

**Granularity:** Census tract, county, place (city/town), ZIP Code Tabulation Area (ZCTA).

**Join keys:** Census tract FIPS/GEOID, County FIPS (5-digit), ZCTA codes.

**ACO value:** Provides prevalence estimates for the exact chronic conditions that drive Medicare spending at the census tract level. Identify high-risk geographic pockets for targeted care management outreach.

### B.2 CDC/ATSDR Social Vulnerability Index (SVI)

**Source:** [svi.cdc.gov](https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html)

16 census variables in 4 themes:
- **Theme 1 - Socioeconomic:** Poverty, unemployment, housing cost burden, no health insurance, no high school diploma
- **Theme 2 - Household Composition & Disability:** Age 65+, age 17 and under, disability, single-parent, English proficiency
- **Theme 3 - Racial & Ethnic Minority Status:** Minority status, expanded race/ethnicity
- **Theme 4 - Housing Type & Transportation:** Multi-unit, mobile homes, overcrowding, no vehicle, group quarters

**Granularity:** Census tract (primary), ZCTA (starting 2022).

**Join keys:** Census tract FIPS, County FIPS, State FIPS.

**ACO value:** Single composite score identifying the most vulnerable communities. CMS is increasingly incorporating social risk into quality measurement and payment models.

### B.3 Census Bureau / American Community Survey (ACS)

**Source:** [data.census.gov](https://data.census.gov/) | **API:** [census.gov/data/developers](https://www.census.gov/data/developers/data-sets/acs-5year.html)

Health insurance coverage, poverty, income, educational attainment, disability status, employment, housing, race/ethnicity, age, language. Thousands of variables.

**Granularity:** ACS 5-year estimates available down to census block group. ACS 1-year for geographies 20,000+.

**Join keys:** FIPS codes (hierarchical), GEOIDs, ZCTA codes.

**ACO value:** Identify socioeconomic risk factors, transportation barriers, uninsured rates in your communities.

### B.4 AHRQ SDOH Database

**Source:** [ahrq.gov/sdoh/data-analytics/sdoh-data.html](https://www.ahrq.gov/sdoh/data-analytics/sdoh-data.html)

A curated, pre-linked compilation of SDOH variables from **44 federal sources** across 5 domains: Social Context, Economic Context, Education, Physical Infrastructure, Healthcare Context. Over 17,000 variables.

**Granularity:** County (2009-2020), Census tract (2009-2020), ZIP code (2011-2020).

**Join keys:** County FIPS, Census tract FIPS, ZIP codes -- explicitly designed for linkage with CMS data.

**ACO value:** The "meta-dataset" -- AHRQ has already harmonized dozens of sources into a single linkable format. Saves significant data engineering effort.

### B.5 HRSA Area Health Resources Files (AHRF)

**Source:** [data.hrsa.gov](https://data.hrsa.gov/topics/health-workforce/nchwa/ahrf)

Over 6,000 variables from 50+ data sources: physicians by specialty, nurses, NPs, PAs, dentists; health facilities (hospitals, FQHCs, nursing homes, mental health); population characteristics; economics.

**Granularity:** County, state, national.

**Join keys:** County FIPS (5-digit).

**ACO value:** Identify provider shortage areas. Assess primary care capacity vs. demand. Support network development strategies.

### B.6 County Health Rankings & Roadmaps

**Source:** [countyhealthrankings.org](https://www.countyhealthrankings.org/)

Nearly 90 measures annually: health outcomes (premature death, poor health), health behaviors (smoking, obesity), clinical care (uninsured rate, PCP ratio, preventable hospital stays), social/economic factors (education, unemployment, poverty, income inequality, crime), physical environment (air quality, housing, commuting).

**Granularity:** County level (all U.S. counties), state level. Annual since 2010.

**Join keys:** 5-digit county FIPS codes.

**ACO value:** Pre-calculated composite health rankings for quick community health assessment. Clinical care measures (preventable hospital stays, PCP ratios) directly relevant to ACO performance.

### B.7 USDA Food Access Research Atlas

**Source:** [ers.usda.gov/data-products/food-access-research-atlas](https://www.ers.usda.gov/data-products/food-access-research-atlas/)

Food desert classification, food access indicators, vehicle availability, population counts at various distance thresholds from supermarkets.

**Granularity:** Census tract level.

**Join keys:** Census tract FIPS codes (11-digit).

**ACO value:** Food insecurity drives chronic disease outcomes (diabetes, hypertension, obesity). Target nutrition counseling and medically-tailored meal programs.

### B.8 EPA EJScreen

**Source:** Previously at ejscreen.epa.gov (archived data available via Harvard HELD Collection)

Environmental indicators: PM2.5, ozone, diesel particulate, air toxics, traffic proximity, lead paint, Superfund proximity, drinking water noncompliance. Combined with socioeconomic indicators for Environmental Justice indexes.

**Granularity:** Census block group (finest available), census tract.

**Join keys:** Census block group FIPS (12-digit), Census tract FIPS (11-digit).

**ACO value:** Environmental exposures linked to respiratory disease, cardiovascular disease, and cancer. Root-cause analysis for geographic health outcome variation.

---

## Appendix C: Technical Linking Notes

### C.1 Primary Join Keys Across CMS Datasets

| Key | Used For | Format |
|-----|----------|--------|
| CCN | Facility identification (hospitals, SNFs, HHAs, hospices) | 6-character alphanumeric |
| NPI | Individual clinician identification | 10-digit numeric |
| TIN | Group/organization identification | 9-digit numeric (EIN format) |
| ACO ID | MSSP/REACH ACO identification | Alphanumeric |
| County FIPS | Geographic (county) | 5-digit: 2-digit state + 3-digit county |
| State FIPS | Geographic (state) | 2-digit |

### C.2 Critical Crosswalk Files

| Crosswalk | Source | Purpose |
|-----------|--------|---------|
| **HUD-USPS ZIP Code Crosswalk** | [huduser.gov](https://www.huduser.gov/portal/datasets/usps_crosswalk.html) | Maps ZIP codes to census tracts, counties, CBSAs (updated quarterly). Essential because CMS data often uses ZIP codes while external SDOH data uses census tracts. |
| **SSA-to-FIPS County Crosswalk** | [NBER](https://www.nber.org/research/data/ssa-federal-information-processing-series-fips-state-and-county-crosswalk) | CMS historically uses SSA county codes, not FIPS codes. This crosswalk is critical for linking CMS data to Census, CDC, or USDA data. |

### C.3 Recommended Linking Approach

1. **Geocode** beneficiary addresses to census tracts (or use the HUD ZIP-to-tract crosswalk)
2. **Join external datasets** at the tract level (PLACES, SVI, Food Atlas, AHRQ SDOH)
3. **For county-level datasets** (AHRF, County Health Rankings), use the county FIPS embedded in the first 5 digits of the tract FIPS
4. **For CMS data using SSA county codes**, apply the SSA-to-FIPS crosswalk first
5. **For provider-level linkages**, use NPI (clinicians) or CCN (facilities) directly across CMS datasets

### C.4 Data Access

- All datasets on data.cms.gov are **API-enabled** (RESTful APIs) and freely downloadable as CSV
- Provider Data Catalog API: `https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items`
- Main catalog metadata: `https://data.cms.gov/data.json`
- Quality data updates quarterly; enrollment data updates monthly; performance year data updates annually
