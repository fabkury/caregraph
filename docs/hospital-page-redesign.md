# Hospital Page Redesign — Design Decisions

## Goal

Redesign hospital detail pages to match the ACO page pattern: a single unified
scrollable view (no Explore/Table tabs) with structured sections, national
benchmarks, percentile context, and domain-expert data groupings.

## Current data coverage (5,426 hospitals)

| Dataset | Hospitals with data | Notes |
|---------|-------------------|-------|
| General Information | 5,426 (100%) | Name, address, type, ownership, star rating, star rating component breakdowns |
| HRRP Readmissions | 3,055 (56%) | 6 conditions; mainly Acute Care hospitals |
| VBP Total Performance | 2,454 (45%) | 4 domains + TPS; Acute Care only (by CMS rules) |
| FIPS county link | 5,227 (96%) | Enables county cross-links |
| Related entities | 5,244 (97%) | Counties, SNFs, DRGs, etc. |

Star ratings: 2,866 hospitals (53%) have a 1–5 star rating; the remainder (mostly Critical Access, Psychiatric, VA, Children's, DoD) show "Not Available."

## Section structure (domain-expert grouping)

### 1. Overview
- Name, address, phone, hospital type, ownership, emergency services, birthing-friendly
- **Star rating display**: Large star visualization with rating/5
- **Hospital type context card**: Brief explanation of what this type means (e.g., "Critical Access Hospitals are small rural hospitals with ≤25 beds that are at least 35 miles from the nearest hospital")

### 2. CMS Star Rating Breakdown
The general_info data includes per-domain measure group counts that CMS uses to compute the overall star rating. These are rarely surfaced by other tools, making this a differentiator.

**Display**: Horizontal stacked bars for each of the 5 CMS quality domains:
- **Mortality** (MORT): X of Y measures, N better / N same / N worse than national
- **Safety**: X of Y measures, N better / N same / N worse
- **Readmissions** (READM): X of Y measures, N better / N same / N worse
- **Patient Experience** (Pt Exp): X of Y measures reported
- **Timely & Effective Care** (TE): X of Y measures reported

Color coding: Green chips for "better," gray for "no different," red for "worse."

### 3. Readmissions (HRRP)
**Excess Readmission Ratio** is the key metric — 1.0 = expected, >1.0 = penalized.

**Display**:
- Horizontal bar/bullet chart per condition showing ERR relative to 1.0 baseline
- Color: green (<1.0), yellow (1.0–1.05), red (>1.05)
- Show national median ERR from benchmarks
- Volume context: discharge count per condition (small-volume footnote if <25)
- **Penalty status callout**: "This hospital is/is not penalized under HRRP"

Conditions: AMI, Heart Failure, Pneumonia, COPD, Hip/Knee Replacement, CABG

### 4. Value-Based Purchasing (VBP)
**Total Performance Score (TPS)** determines payment adjustment.

**Display**:
- TPS headline with percentile badge and national median
- 4 domain scores as gauge-style cards with percentile context:
  - Clinical Outcomes (25% weight)
  - Safety (25% weight)
  - Person & Community Engagement (25% weight)
  - Efficiency & Cost Reduction (25% weight)
- Domain weights shown as context
- **Payment adjustment direction**: "TPS above/below national median suggests a positive/negative payment adjustment"

### 5. CMS Payment Programs Summary
A consolidated view of how this hospital fares across the 3 major Medicare payment adjustment programs. This section only renders when readmissions or VBP data is available.

**Display**: 3-column card grid:
- **HRRP** (Readmissions): Penalized / Not Penalized (with worst ERR)
- **VBP**: TPS score with above/below median indicator
- **HAC Reduction**: Status if data available; "Data not available" otherwise

### 6. Related Entities
Links to county, ACOs, SNFs, DRGs, drugs, conditions.

### 7. Methodology / Provenance
Dataset lineage with vintage dates and row counts.

## Benchmark strategy

**Computed at ETL time** in `build_hospital_benchmarks.py`:

For each numeric metric across all hospitals:
- Percentiles: p10, p25, p50 (median), p75, p90
- Mean and count (n)
- Per-hospital percentile rank (1–100)

**Stratification**: Benchmarks are computed across all hospitals with data for
that metric. Future enhancement: stratify by hospital type (Acute Care vs
Critical Access) since they serve fundamentally different populations.

**Benchmark fields**:
- VBP: total_performance_score, clinical_outcomes_score, safety_score, person_community_score, efficiency_score
- HRRP: excess_readmission_ratio (aggregated as worst ERR per hospital), average ERR
- Star rating: hospital_overall_rating

## Visual design principles

1. **Percentile badges**: Small colored pills showing "p42" like ACO pages
   - p1–p25 (bottom quartile): Red background
   - p26–p74 (middle): Amber/yellow background
   - p75–p100 (top quartile): Green background
   - For "lower is better" metrics, colors are inverted

2. **National median markers**: Shown alongside hospital values for instant context

3. **Section navigation**: Floating sidebar/top nav with anchor links to each section

4. **Conditional rendering**: Sections only appear when the hospital has data for them (many metrics are N/A for non-Acute Care hospitals)

5. **Help text**: Brief explanations of what each metric means, following the ACO page's tooltip pattern

## Hospital type explanations

Hospital type determines which CMS programs apply:

| Type | Count | VBP eligible | HRRP eligible | Star rated | Notes |
|------|-------|-------------|---------------|------------|-------|
| Acute Care | 3,116 | Yes | Yes | Usually | Standard IPPS hospitals |
| Critical Access | 1,376 | No | No | Sometimes | Rural, ≤25 beds, cost-based reimbursement |
| Psychiatric | 633 | No | No | No | Inpatient psychiatric only |
| VA | 132 | No | No | No | Federal, not in Medicare |
| Children's | 94 | No | No | No | Pediatric specialty |
| Rural Emergency | 39 | No | No | No | New designation (2023+), ED only |
| DoD | 32 | No | No | No | Federal military |
| Long-term | 4 | No | No | No | LTCH, ≥25 day average LOS |

This context helps users understand *why* a hospital may lack VBP or HRRP data.

## Decisions made

1. **Single unified view** — Remove Explore/Table tabs. All information in one scrollable page with section nav anchors.

2. **Star rating breakdown is a first-class section** — The general_info already contains CMS domain-level performance counts (better/same/worse vs. national) that most tools don't surface. This is free context.

3. **HRRP readmissions shown as bullet chart relative to 1.0** — More intuitive than a raw table. The 1.0 baseline is the key reference point.

4. **VBP domains shown with weights** — Users need to know that each domain is 25% of TPS to interpret scores correctly.

5. **Hospital type explanations** — Brief contextual cards explaining why non-Acute Care hospitals have less data. This prevents confusion.

6. **Benchmarks computed nationally** — Not stratified by type in v1. This is a conscious simplification; type-stratified benchmarks are a future enhancement.

7. **Graceful degradation** — Page sections are conditionally rendered. A Critical Access Hospital with only general_info still gets a useful page (overview + star rating breakdown + related entities).
