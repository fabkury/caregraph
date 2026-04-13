# Tier A Dataset Implementation Decisions

> Date: 2026-04-12. Documents design decisions for implementing 7 Tier A datasets from `hhs-datagov-dataset-suggestions.md`.

---

## Datasets Being Implemented

1. **ACO Beneficiaries by County** — improves ACO↔County cross-links
2. **Hospital Cost Report** — hospital financial health dashboard
3. **SNF Cost Report** — nursing home financial health dashboard
4. **HAC Reduction Program** — hospital penalty completion
5. **CDC SDOH Measures** — county social determinants
6. **Medicare Chronic Conditions by County** — county disease burden + spending
7. **NADAC Drug Pricing** — drug acquisition cost transparency

---

## 1. ACO Beneficiaries by County

### Data Source
- **CSV URL:** `https://data.cms.gov/sites/default/files/2024-11/8a74dd30-06a1-4751-beee-dc0dd3c9d609/Number_Of_ACO_Assigned_Beneficiaries_by_County_PUF_2023_01_01.csv`
- **Columns:** Year, ACO_ID, State_Name, County_Name, State_ID (SSA), County_ID (SSA), AB_Psn_Yrs_ESRD, AB_Psn_Yrs_DIS, AB_Psn_Yrs_AGDU, AB_Psn_Yrs_AGND, Tot_AB_Psn_Yrs, Tot_AB
- **Key challenge:** State_ID and County_ID are **SSA codes**, not FIPS. Must use SSA-to-FIPS crosswalk. Many values suppressed (`*` or `.`).

### Decision: SSA-to-FIPS Conversion
Use the existing `load_ssa_to_fips_crosswalk()` scaffold in `etl/normalize/keys.py`. The SSA county code is formed by concatenating `State_ID` (2-digit) + `County_ID` (3-digit) into a 5-digit SSA code, then mapping to FIPS. We'll use the NBER SSA-to-FIPS crosswalk file. If the crosswalk is unavailable, fall back to matching on State_Name + County_Name to existing county manifests.

### Decision: Suppressed Values
Values of `*` (fewer than 11 beneficiaries) and `.` (not applicable) are treated as 0 for aggregation purposes but flagged. The `Tot_AB` column (total beneficiaries contributing at least one person-month) is the primary metric. Where suppressed, we still create the cross-link but without a beneficiary count context string.

### Presentation Changes
- **ACO pages:** Replace the current "all counties in state, capped at 20" approach in `build_crosslinks.py` with precise county links from this dataset. Show top 20 counties by assigned beneficiaries. Context string: "X assigned beneficiaries" (or "< 11 beneficiaries" if suppressed).
- **County pages:** Add ACO links with beneficiary context. Show all ACOs active in the county. Context string: "X beneficiaries assigned" and quality score from ACO manifest.
- **No new data section** on either page — this changes cross-linking only.

---

## 2. Hospital Cost Report

### Data Source
- **CSV URL:** `https://data.cms.gov/sites/default/files/2026-01/3c39f483-c7e0-4025-8396-4df76942e10f/CostReport_2023_Final.csv`
- **Join key:** `Provider CCN` (column 1), 6-char zero-padded.
- **117 columns** covering utilization, costs, charges, revenue, assets, liabilities.

### Decision: Curated Financial Metrics
Rather than dumping all 117 columns, compute 10 derived financial health indicators:

| Metric | Formula | Format | Interpretation |
|--------|---------|--------|----------------|
| Operating Margin | `Net Income from Service to Patients` / `Net Patient Revenue` | % | Core profitability from patient care |
| Total Margin | `Net Income` / `Total Income` | % | Overall profitability including other income |
| Cost per Discharge | `Total Costs` / `Total Discharges (all)` | $ | Operational efficiency |
| Occupancy Rate | `Total Days (all)` / `Total Bed Days Available` | % | Capacity utilization |
| Uncompensated Care % | `Cost of Uncompensated Care` / `Total Costs` | % | Safety-net burden indicator |
| Current Ratio | `Total Current Assets` / `Total Current Liabilities` | ratio | Short-term financial stability |
| Medicare Day Share | `Total Days Title XVIII` / `Total Days (all)` | % | Medicare dependency |
| Cost-to-Charge Ratio | `Cost To Charge Ratio` (direct column) | ratio | Pricing efficiency |
| Employees per Bed | `FTE - Employees on Payroll` / `Number of Beds` | ratio | Staffing intensity |
| Net Patient Revenue | direct column | $ | Top-line revenue |

### Decision: Benchmarking
During ETL, compute national median and 25th/75th percentile for each metric across all hospitals. Store these benchmarks in a shared `site_data/compare/hospital_cost_benchmarks.json`. On the frontend, display each metric with a percentile badge (same pattern as ACO pages) and national median comparison.

### Presentation: "Financial Health" Section
New card on hospital pages with:
1. **Headline metric grid** (4 cards): Operating Margin, Occupancy Rate, Cost per Discharge, Current Ratio
2. **Revenue & Cost summary** (kv-table): Net Patient Revenue, Total Other Income, Total Operating Expense, Net Income — with positive/negative coloring
3. **Safety-net indicators** (2 cards): Uncompensated Care %, Medicare Day Share
4. **Balance sheet highlight** (kv-table): Total Assets, Total Liabilities, Fund Balance
5. Each metric shows value + percentile badge + national median

Fiscal year noted in section header: "Financial Health (FY 2023 Cost Report)".

---

## 3. SNF Cost Report

### Data Source
- **CSV URL:** `https://data.cms.gov/sites/default/files/2025-11/34ea98e4-20f4-42f7-b5b2-616d35b0fe93/CostReportsnf_Final_23.csv`
- **Join key:** `Provider CCN` (column 1), 6-char zero-padded.
- **122 columns** covering SNF and NF (nursing facility) utilization, costs, revenue.

### Decision: Curated Financial Metrics
Same approach as hospitals, adapted for SNF context:

| Metric | Formula | Format | Interpretation |
|--------|---------|--------|----------------|
| Operating Margin | `Net Income from service to patients` / `Net Patient Revenue` | % | Core profitability |
| Total Margin | `Net Income` / `Total Income` | % | Overall profitability |
| Cost per Resident Day | `Total Costs` / `Total Days Total` | $ | Cost efficiency |
| Occupancy Rate | `Total Days Total` / `Total Bed Days Available` | % | Capacity utilization |
| Medicare Day Share | `Total Days Title XVIII` / `Total Days Total` | % | Medicare payer mix |
| Medicaid Day Share | `Total Days Title XIX` / `Total Days Total` | % | Medicaid payer mix |
| Current Ratio | `Total Current Assets` / `Total current liabilities` | ratio | Financial stability |
| Net Patient Revenue | direct column | $ | Top-line revenue |

### Decision: Payer Mix Emphasis
Medicaid day share is a critical SNF quality predictor. High Medicaid-share facilities often have lower staffing and more deficiencies. Display the payer mix as a horizontal stacked bar (Medicare / Medicaid / Other) to make this visually prominent.

### Presentation: "Financial Health" Section
New card on SNF pages:
1. **Headline metrics** (3 cards): Operating Margin, Cost per Resident Day, Occupancy Rate
2. **Payer Mix bar** (stacked horizontal bar): Medicare % | Medicaid % | Other %
3. **Revenue & Cost summary** (kv-table): Net Patient Revenue, Total Operating Expense, Net Income
4. **Balance sheet** (kv-table): Total Assets, Total Liabilities, Fund Balance
5. Percentile badges for each metric against national SNF benchmarks.

---

## 4. HAC Reduction Program

### Data Source
- **API:** Provider Data API, dataset ID `yq43-i98g`
- **Join key:** `facility_id` = CCN
- **Columns:** facility_name, facility_id, state, fiscal_year, psi_90_composite_value, psi_90_w_z_score, clabsi_sir/w_z, cauti_sir/w_z, ssi_sir/w_z, cdi_sir/w_z, mrsa_sir/w_z, hai_measures_start_date, hai_measures_end_date, total_hac_score, payment_reduction
- **3,055 rows** (one per hospital)

### Decision: Combined Penalty Dashboard
The HAC penalty status should be presented alongside HRRP and VBP data to create a unified "CMS Penalty Programs" view. This is the killer contextualization: users see at a glance whether a hospital is penalized under 0, 1, 2, or 3 programs.

### Presentation: "CMS Payment Programs" Card
Replace or augment existing HRRP/VBP sections with a combined card:

1. **Penalty Summary Row** (3 badges side by side):
   - HRRP: "Penalized" (red) / "Not Penalized" (green) — from existing readmissions data (excess ratio > 1.0 for any condition)
   - VBP: Net payment adjustment % — from existing VBP data (positive = green, negative = red)
   - HAC: "Payment Reduced" (red) / "No Reduction" (green) — from `payment_reduction`

2. **HAC Detail Card** (below summary):
   - Total HAC Score with interpretation ("lower is better; hospitals in worst quartile receive 1% payment reduction")
   - Component measures table:
     | Measure | SIR | Winsorized Z-Score |
     |---------|-----|--------------------|
     | PSI-90 Composite | 0.95 | -0.26 |
     | CLABSI | 0.51 | -0.22 |
     | CAUTI | 0.13 | -1.01 |
     | SSI (Colon/Hysterectomy) | 0.87 | 0.03 |
     | CDI (C. difficile) | 0.44 | 0.22 |
     | MRSA Bacteremia | 0.32 | -0.80 |
   - Measurement period shown in footer.

### Decision: SIR Interpretation
SIR (Standardized Infection Ratio) values < 1.0 mean fewer infections than expected (good). Display with color: green if < 0.8, neutral if 0.8-1.2, red if > 1.2. This helps non-clinical users interpret the numbers.

---

## 5. CDC SDOH Measures

### Data Source
- **API:** SODA API at `data.cdc.gov`, dataset `i6u4-y3g4`
- **Join key:** `LocationID` = county FIPS
- **28,287 rows** (9 measures × ~3,143 counties)
- **Columns:** Year, StateAbbr, LocationName, Category, Measure, Data_Value (%), MOE, TotalPopulation, LocationID (FIPS), MeasureID, Short_Question_Text

### Decision: Measure Grouping
Group the 9 SDOH measures into 3 thematic domains for clearer presentation:

**Economic Stability:**
- Poverty (below 150% FPL)
- Unemployment

**Education & Connectivity:**
- No high school diploma
- No broadband internet access

**Housing & Demographics:**
- Housing cost burden
- Crowding
- Single-parent households
- Racial/ethnic minority status
- Age 65+ population

### Decision: National Context
During ETL, compute national median, 25th percentile, and 75th percentile for each measure across all counties. Store in `site_data/compare/county_sdoh_benchmarks.json`. On each county page, show each SDOH measure with a horizontal bar showing where the county falls relative to the national distribution, colored by quartile.

### Presentation: "Social Determinants of Health" Section
New card on county pages:
1. **9-metric grid** (3 per row): Each metric card shows:
   - Measure name (short)
   - Value (%)
   - Margin of error (±X%)
   - Horizontal mini-bar showing position in national distribution
   - Quartile color (green = healthier quartile, red = concerning quartile)
2. Domain grouping headers (Economic Stability / Education & Connectivity / Housing & Demographics)
3. Source and year footnote: "Source: CDC SDOH, ACS 2017-2021"

### Decision: "Higher = Concerning" Inversion
All 9 SDOH measures are "higher is worse" (higher poverty, higher unemployment, etc.). Use the inverted color scheme: red for top quartile (worst), green for bottom quartile (best). The only exception is Age 65+ which is neutral — present it in gray.

---

## 6. Medicare Chronic Conditions by County

### Data Source
- **Source:** `data.cms.gov/medicare-chronic-conditions/specific-chronic-conditions`
- **Join key:** `Bene_Geo_Cd` = county FIPS (when `Bene_Geo_Lvl` = "County")
- **21 conditions** tracked: Alzheimer's/Dementia, Arthritis (RA/OA), Asthma, Atrial Fibrillation, Autism, Cancer (various), COPD, Depression, Diabetes, Drug/Substance Use, Heart Failure, Hepatitis (B & C), HIV/AIDS, Hyperlipidemia, Hypertension, Ischemic Heart Disease, Kidney Disease, Schizophrenia/Other Psychotic, Stroke/TIA, Tobacco Use
- **Columns per condition:** Prevalence %, Per-capita total Medicare spending, Beneficiary count

### Decision: Download Strategy
The chronic conditions data may not be available via a standard CMS data-api endpoint. If API access fails, fall back to downloading the pre-built CSV geographic data files from the CMS website. The data dictionary confirms county-level files exist with FIPS codes.

### Decision: Dual Prevalence View
Where CareGraph already has CDC PLACES prevalence data for the same condition (e.g., COPD, diabetes, depression), show **both** estimates side by side:
- **PLACES estimate:** Survey-modeled, covers entire population
- **CMS CCW estimate:** Claims-confirmed, Medicare FFS population only

This dual view is unique to CareGraph and reveals whether the Medicare population has higher or lower condition burden than the general population — often significantly higher for chronic conditions.

### Presentation: "Medicare Chronic Disease Burden" Section
New card on county pages:
1. **Condition table** with columns:
   | Condition | Medicare Prevalence | PLACES Estimate | National Avg | Per-Capita Spending |
   |-----------|-------------------|-----------------|--------------|---------------------|
   | Diabetes  | 28.3%             | 12.1%           | 27.1%        | $2,145              |
   
   - Medicare Prevalence: from this dataset, with red/green coloring vs national average
   - PLACES Estimate: from existing CDC PLACES data (if available for this condition), in muted gray
   - Per-Capita Spending: in dollars, with color (red if above national median)
   
2. **Top 5 costliest conditions** callout box showing the 5 conditions with highest per-capita spending for this county
3. Source footnote: "Source: CMS Chronic Condition Data Warehouse, Medicare FFS beneficiaries only"

---

## 7. NADAC Drug Pricing

### Data Source
- **API:** SODA-style API at `data.medicaid.gov`, dataset `fbb83258-11c7-47f5-8b18-5f8e79f7e704`
- **Columns:** ndc_description, ndc, nadac_per_unit, effective_date, pricing_unit, pharmacy_type_indicator, otc, explanation_code, classification_for_rate_setting, corresponding_generic_drug_nadac_per_unit
- Updated weekly.

### Decision: Drug Name Matching
CareGraph Drug entities are keyed by generic drug name (e.g., "LISINOPRIL"). NADAC records are at the NDC level with `ndc_description` containing the product name. Strategy:
1. Parse `ndc_description` to extract generic drug name (normalize to uppercase, remove dosage/strength/form info).
2. Match to CareGraph drug entities by normalized generic name.
3. When multiple NDC records match one drug, aggregate: compute median NADAC per unit across all matching NDCs, weighted by a "representative" approach (most common dosage form).

### Decision: Medicare Markup Calculation
For drugs on both NADAC and Part D Spending:
- `Part D cost per unit` = Total Spending / Total Dosage Units (from existing Part D data)
- `NADAC per unit` = median acquisition cost (from NADAC)
- `Markup ratio` = Part D cost per unit / NADAC per unit
- `Spread` = Part D cost per unit - NADAC per unit

This shows how much more Medicare pays vs. what pharmacies pay to acquire the drug.

### Presentation: "Drug Pricing Transparency" Section
New card on drug pages:
1. **Key metric grid** (3 cards):
   - Pharmacy Acquisition Cost (NADAC per unit)
   - Medicare Part D Cost per Unit (derived from existing data)
   - Markup Ratio (Part D / NADAC)
2. **Interpretation text:** If markup > 2.0: "Medicare pays significantly more than pharmacy acquisition cost." If markup < 1.5: "Medicare payment is close to pharmacy acquisition cost."
3. **Classification badge:** Generic (G) or Brand (B) from `classification_for_rate_setting`
4. **OTC indicator** if `otc` = "Y"
5. Source footnote: "Pharmacy acquisition cost from CMS NADAC survey (weekly). Medicare cost from Part D Spending data."

### Decision: Scope Limitation
NADAC only covers pharmacy-dispensed drugs (not physician-administered Part B drugs). For drugs that are primarily Part B (e.g., infusion drugs), NADAC may not have data. In those cases, the Drug Pricing Transparency section is simply omitted.

---

## Cross-Cutting Decisions

### Benchmarking Infrastructure
All 7 datasets share a common benchmarking pattern. During ETL, after enrichment:
1. Scan all manifests of a given entity type
2. Compute percentiles (25th, 50th, 75th) for each new numeric metric
3. Store in `site_data/compare/{entity}_benchmarks.json`
4. Frontend reads benchmark file and displays percentile badges

### ETL Dataset IDs
| Internal ID | API Type | Entity |
|---|---|---|
| `aco-bene-county` | data-api (CSV direct) | aco + county |
| `hosp-cost-report` | data-api (CSV direct) | hospital |
| `snf-cost-report` | data-api (CSV direct) | snf |
| `hac-reduction` | provider-data | hospital |
| `cdc-sdoh` | soda | county |
| `nadac` | soda (data.medicaid.gov) | drug |

### Provenance
Each new dataset adds a provenance entry to the enriched manifests, following the existing `build_provenance()` pattern.

### Error Handling
If a dataset download fails, the enrichment step is skipped gracefully. The base entity manifests remain valid without the enrichment data. The frontend conditionally renders sections only when the data section exists in the manifest.
