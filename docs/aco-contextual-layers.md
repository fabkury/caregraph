# ACO Contextual Layers — Recommendations

**Date:** 2026-04-12
**Status:** Proposal

## Guiding Principle

A number in isolation is trivia. A number *in context* is insight. The goal is to answer the question every ACO leader actually asks: **"Compared to what?"**

---

## 1. MSSP-Wide Percentile Rank (all numeric sections)

**What:** For every key metric, show where this ACO falls in the distribution of all 476 MSSP ACOs.

**Why:** This is the single highest-impact contextual layer. It transforms every number from abstract to positional. "Savings rate: 3.95%" becomes "Savings rate: 3.95% (42nd percentile)."

**How:** Pre-compute percentile ranks during the ETL across all 476 ACO manifests and store them in a summary JSON file (`site_data/aco_benchmarks.json`). Display as:
- A small **percentile badge** next to each value (e.g., `p42`)
- Or a **mini gauge/strip** — a thin horizontal bar showing where the ACO falls on the distribution, with the median marked

**Implementation note:** Since we have all 476 manifests at build time, this is a straightforward ETL enrichment step. The benchmark file contains p10/p25/p50/p75/p90 for every numeric field. Each ACO page reads its own values and positions them against the benchmarks.

---

## 2. Per Capita Expenditure: Risk-Adjusted Comparison

**What:** Next to the raw per-capita expenditure, show the **expected expenditure** given this ACO's risk score, and the **residual** (actual minus expected).

**Why:** A raw expenditure number confounds population acuity with delivery efficiency. An ACO spending $13,350/capita looks expensive against the MSSP median of $12,693 — but if its HCC risk scores are all above 1.0 (sicker than average), the raw number is misleading. The risk-adjusted residual separates the two: *are you expensive because your patients are sick, or because you're inefficient?* This is the core analytical question in Value-Based Care.

**How:** Compute a simple risk-adjusted expected expenditure per segment: `MSSP_median_expenditure × ACO_risk_score`. The difference is the "efficiency gap." Display as an additional column in the expenditure pivot table:

| Segment | PY Actual | Risk-Adjusted Expected | Difference |
|---|---|---|---|
| Aged, Non-Dual | $12,840 | $12,693 × 1.184 = $15,028 | **−$2,188** (efficient) |

---

## 3. Utilization Metrics: MSSP Median Reference Lines

**What:** Show the MSSP median next to each utilization rate (admissions, ED visits, imaging, visits).

**Why:** Utilization rates are the most actionable numbers on the page — they directly connect to care redesign interventions. But a rate like "335 admissions per 1,000" is meaningless without a reference. The MSSP median (251) immediately contextualizes it as 33% above typical.

**How:** For each utilization metric in the kv-table, add a third column showing the MSSP median and the percentage difference:

| Metric | This ACO | MSSP Median | Difference |
|---|---|---|---|
| Hospital Admissions | **335** | 251 | +33% |
| ED Visits | **788** | 618 | +27% |
| PCP Visits | 3,229 | 4,192 | −23% |

**Enhanced version:** For the largest outliers, derive an **"opportunity sizing"** estimate. If admissions dropped to the median, that's 84 fewer per 1,000 across N beneficiaries = X avoided admissions × average cost = $Y potential savings. This is the kind of analysis ACO leadership uses for strategic planning.

---

## 4. CAHPS: Domain-Level Benchmark Bars

**What:** Overlay the MSSP median (and 40th/90th percentile) on the existing CAHPS horizontal bar chart.

**Why:** CAHPS scores exist on a 0–100 scale, but the practical range is narrow (most scores cluster between 60–95). Without benchmarks, a score of 70 looks mediocre when it might actually be above median. The reference lines create a visual "zone" system:
- Below 40th percentile: improvement needed (quality gate risk)
- 40th–75th: acceptable
- Above 75th: strength

**How:** On each CAHPS bar, add a thin vertical marker at the median and a shaded zone for the interquartile range:

```
Health Promotion & Education: 69.14  [============================|==]  median: 65.66
                                                          ↑ this ACO is above p75
```

---

## 5. Quality Measures: Threshold Markers

**What:** Show the MSSP 40th percentile, median, and 90th percentile for each quality measure.

**Why:** Quality measures directly affect the ACO's shared savings rate. The 40th percentile is the critical threshold — below it, the ACO risks reduced savings or failing the quality gate. Showing these thresholds turns an abstract score into a pass/fail/excel indicator.

Example: HbA1c Poor Control at 13.82% (higher = worse). MSSP median is 8.44%, p90 is 13.76% — this ACO is in the bottom decile. That's a specific, actionable clinical finding invisible without the benchmark.

**How:** For each measure, show a mini comparison below the value:

```
Diabetes: HbA1c Poor Control >9%   13.82%   ▓▓▓▓▓▓▓▓▓░  p92 (worse)
  40th pctl: 7.21%  |  Median: 8.44%  |  This ACO: 13.82%
```

For inverted measures (lower is better), the color scale should always read green = good, red = concern.

---

## 6. Spending by Service: Composition Comparison

**What:** Show the ACO's spending mix as a percentage composition alongside the MSSP median composition.

**Why:** Absolute dollar amounts per service category are useful, but the *composition* reveals care model differences. An ACO spending 33% on outpatient and 21% on physician services (vs. MSSP median 23%/32%) has a structurally different care model — possibly reflecting hospital-centric care patterns in rural areas.

**How:** Side-by-side 100% stacked horizontal bars (this ACO vs. MSSP median) or an additional "% of total" and "MSSP median %" column in the existing table.

---

## 7. Risk Scores: Coding Intensity Gap

**What:** Next to each CMS-HCC risk score, show the Demographic risk score for the same segment. The difference is the **coding intensity gap** — how much the risk score is driven by clinical documentation vs. pure demographics.

**Why:** This is one of the most sophisticated analytical insights in VBC. A high HCC risk score can mean either (a) genuinely sick patients or (b) aggressive coding practices. The Demographic risk score captures only age/sex/Medicaid status. The gap is the coding-driven component.

Example — Aged Non-Dual PY:
- HCC Risk Score: 1.184
- Demographic Risk Score: 1.035
- **Coding Intensity Gap: +0.149**

This means 0.149 of the 0.184 above-average risk comes from clinical coding, not demographics. It could reflect genuine clinical complexity (e.g., high chronic disease burden in Appalachia) or coding optimization. Either way, it's a critical conversation for the ACO medical director.

**How:** Add a "Coding Gap" column to the risk score pivot table. No new data needed — both HCC and Demographic scores are already in each manifest.

---

## 8. Demographics: MSSP-Wide Comparison

**What:** For key demographic distributions (age, dual-eligible %, race), show the MSSP-wide average alongside the ACO's values.

**Why:** A dual-eligible rate of 8.42% means nothing in isolation. Against the MSSP median (6.89%) and p75 (11.39%), it's slightly above average. Showing the comparison directly on the demographic callouts and bar charts provides instant context.

**How:** In the demographic bar charts, add a subtle marker line for the MSSP median. For the special populations callouts, show the comparison inline: "Dual-Eligible: 8.42% (MSSP median: 6.89%)."

---

## 9. Financial Waterfall: Benchmark Annotations

**What:** Annotate key waterfall steps with the MSSP median for the same step.

**Why:** The jump from Historical Benchmark ($10,928) to Updated Benchmark ($13,899) is a $2,971 increase. Is that typical? Showing the MSSP median for Historical Benchmark and Updated Benchmark reveals whether this ACO's benchmark trajectory is normal or unusual. A large positive regional adjustment might indicate a high-cost region; a large prior savings adjustment might indicate strong prior performance.

**How:** Add a "MSSP Median" column or tooltip to the waterfall steps for Historical Benchmark, Regional Adjustment, Updated Benchmark, Savings Rate, Final Share Rate, and Earned Savings.

---

## 10. Peer Cohort Comparison

**What:** Identify a cohort of structurally similar ACOs and show how this ACO compares to its peers specifically, not just the full MSSP population.

**Why:** Comparing a 37K-beneficiary BASIC-track rural ACO to the full MSSP population (which includes 5K-beneficiary urban ENHANCED-track ACOs) is noisy. A peer cohort filters out structural differences and reveals true performance variation. This is the comparison an ACO board of directors cares about most: *"Among ACOs like us, how are we doing?"*

**How:** See the detailed peer cohort specification below.

---

## Peer Cohort Comparison — Detailed Specification

### Goal

Assign every ACO a peer cohort of structurally similar ACOs, enabling fair "apples-to-apples" comparisons. Display peer cohort medians alongside MSSP-wide medians on every metric.

### Why Simple Binning Fails

A naive approach (same track + same size band) creates too few groups with too much internal heterogeneity. A 40K-beneficiary BASIC ACO in Appalachia and a 40K-beneficiary BASIC ACO in suburban Connecticut share a track and size but have fundamentally different populations, cost environments, and care delivery infrastructure. Meaningful peer comparison requires a multi-dimensional similarity measure.

### Approach: Hard Partition + Distance-Based Nearest-Neighbor

The method has two layers:

1. **Hard partition on track group** — BASIC (tracks A/B/C/D, n=167) and ENHANCED (tracks E/EN, n=309) ACOs are never mixed. Track group defines the financial framework (upside-only vs. two-sided risk, prospective vs. retrospective benchmarking rules). Cross-track comparisons are structurally invalid.

2. **Within each partition, compute a distance metric** across structural features and select each ACO's K nearest neighbors. This produces overlapping, ACO-specific cohorts that adapt to each ACO's unique position in the feature space.

### Empirical Basis for Feature Selection

The following analysis was performed on all 476 PY2024 ACO manifests to guide feature selection.

#### Correlation with Per Capita Expenditure (the primary cost outcome)

| Feature | r with PCE | Interpretation |
|---|---|---|
| `UpdatedBnchmk` | **+0.980** | Near-perfect — benchmark is computed *from* historical spending. Tautological. |
| `HistBnchmk` | **+0.968** | Also near-tautological. Correlated r=0.977 with UpdatedBnchmk. |
| `ADM` (admissions) | +0.906 | Strong, but this is an *outcome*, not a structural feature. |
| `% age 85+` | +0.803 | Strong. Frailty-driven costs beyond what HCC captures. |
| `CMS_HCC_RiskScore_AGND_PY` | +0.747 | Strong. Clinical acuity of the dominant population segment. |
| `P_EDV_Vis` (ED visits) | +0.756 | Strong, but also an outcome. |
| `Perc_Dual` | +0.512 | Moderate. Captures SDOH burden independent of HCC. |
| `NP/PCP ratio` | +0.379 | Moderate. Care model structure. |
| `Rural facility proxy` | −0.144 | Weak. Rural ACOs spend slightly *less* per capita on average. |
| `log(N_AB)` | −0.040 | Near-zero. Size barely predicts spending. |

#### Inter-Feature Correlation Matrix (Acuity Features)

|  | HCC AGND | HCC DIS | HCC AGDU | Perc Dual | % 85+ | HistBnchmk |
|---|---|---|---|---|---|---|
| **HCC AGND** | 1.000 | 0.837 | 0.681 | 0.230 | 0.757 | 0.755 |
| **HCC DIS** | 0.837 | 1.000 | 0.605 | 0.316 | 0.715 | 0.807 |
| **HCC AGDU** | 0.681 | 0.605 | 1.000 | −0.063 | 0.490 | 0.441 |
| **Perc Dual** | 0.230 | 0.316 | −0.063 | 1.000 | 0.307 | 0.509 |
| **% 85+** | 0.757 | 0.715 | 0.490 | 0.307 | 1.000 | 0.804 |
| **HistBnchmk** | 0.755 | 0.807 | 0.441 | 0.509 | 0.804 | 1.000 |

#### Key Findings

1. **Exclude HistBnchmk and UpdatedBnchmk.** Both are near-tautological with the outcome (r ≥ 0.97). They are also highly redundant with the acuity features (r = 0.76–0.81 with HCC scores and % 85+). Including them would double-count the acuity signal and create cohorts that are circular ("your peers are ACOs that spent about the same").

2. **Exclude utilization outcomes (ADM, P_EDV_Vis, etc.).** These are what we *want to compare*, not what we should match on. Matching on admissions would produce cohorts where everyone has similar admissions — defeating the purpose.

3. **HCC_AGND, HCC_DIS, HCC_AGDU are correlated** (r = 0.60–0.84). Using a weighted composite score reduces noise from 3 correlated dimensions to 1 without losing much information.

4. **Perc_Dual is the most independent composition feature** (r = 0.23 with HCC_AGND, r = −0.06 with HCC_AGDU). It captures a distinct dimension: SDOH burden and Medicaid crossover complexity.

5. **% 85+ adds signal beyond HCC** (r = 0.757 with HCC, but r = 0.803 with expenditure — closer to expenditure than HCC alone). Frailty costs in the very old (falls, post-acute, hospice) are not fully captured by HCC coding.

6. **Feature availability is high.** All proposed features are available for 100% of ACOs except Perc_LTI (90%, impute median for missing) and HCC_ESRD (91%, handled by using composite HCC instead).

### Feature Set (Final)

The features capture structural factors that influence performance *independent of management quality* — things an ACO cannot easily change within a performance year.

#### A. Population Acuity (weight: 1.5×)

| Feature | Source | Transform | Rationale |
|---|---|---|---|
| Composite HCC Risk Score | `CMS_HCC_RiskScore_{seg}_PY` × `RR_weight_{seg}_PY` summed across AGND, DIS, AGDU, ESRD | Weighted average using the ACO's own RR weights | Collapses 3–4 correlated segment-level HCC scores into a single population-level acuity measure. Weight reflects actual segment composition. |
| % Aged 85+ | `N_Ben_Age_85plus / N_AB × 100` | None | Captures frailty-driven cost beyond HCC coding. r = 0.80 with expenditure, partially independent of HCC (r = 0.76). |

**Why weight 1.5×:** Acuity features have the strongest correlation with expenditure (r = 0.75–0.80) and admissions (r = 0.78). They represent the primary structural determinant of an ACO's cost profile. Two ACOs with similar acuity face similar clinical challenges regardless of other differences.

#### B. Population Composition (weight: 1.25×)

| Feature | Source | Transform | Rationale |
|---|---|---|---|
| Dual-Eligible % | `Perc_Dual` | None | SDOH burden. Low correlation with HCC (r = 0.23) so captures an independent dimension. Dual-eligibles drive disproportionate post-acute and behavioral health utilization. |
| ESRD Weight | `RR_weight_ESRD_PY` | None | Even small ESRD populations (2–3%) dramatically shift per-capita costs ($80K–$100K vs. $10K–$13K). The RR weight captures the ACO's ESRD exposure as a fraction of total risk. |
| Disabled Weight | `RR_weight_DIS_PY` | None | Disabled beneficiaries have distinct utilization patterns (high behavioral health, DME, disability-related services). Moderate correlation with HCC (r = 0.32 with Perc_Dual) but captures a different population segment. |
| Long-Term Institutionalized % | `Perc_LTI` | Impute median (0.76%) for 50 missing ACOs | Post-acute care intensity. ACOs with high LTI face structurally different SNF and long-term care cost profiles. |
| % Under 65 | `N_Ben_Age_0_64 / N_AB × 100` | None | Proxy for disabled/ESRD composition from a different angle. ACOs with high under-65 population are managing a fundamentally different demographic than aged-dominant ACOs. |

**Why weight 1.25×:** Composition features are moderately correlated with expenditure (r = 0.30–0.51) and capture SDOH and demographic dimensions orthogonal to clinical acuity.

#### C. Scale (weight: 1.0×)

| Feature | Source | Transform | Rationale |
|---|---|---|---|
| Beneficiary count | `N_AB` | log₂ transform | Log-transform reduces skew (range: 1,500–200,000). A 5K ACO and a 50K ACO face different economies of scale, statistical credibility, and management complexity. Near-zero correlation with expenditure (r = −0.04) — size doesn't predict costs, but it matters for organizational comparability. |
| Total clinician count | `N_PCP + N_Spec + N_NP + N_PA + N_CNS` | log₂ transform | Network size as a proxy for organizational complexity. Partially correlated with N_AB but captures network breadth independently. |

**Why weight 1.0×:** Size features don't predict spending or outcomes but matter for comparing operational contexts. A 5K-beneficiary ACO shouldn't be measured against a 100K ACO's quality infrastructure.

#### D. Care Delivery Infrastructure (weight: 1.0×)

| Feature | Source | Transform | Rationale |
|---|---|---|---|
| Hospital count | `N_Hosp` | sqrt transform (reduces right skew) | Facility-based ACOs have structurally different cost profiles (facility fees, employed clinicians, capital costs) vs. physician-only ACOs. 47% of ACOs have zero hospitals. |
| Critical Access Hospital count | `N_CAH` | sqrt transform | Best single proxy for rurality. CAHs operate under cost-based reimbursement, have distinct volume characteristics, and serve geographic monopoly markets. |
| FQHC count | `N_FQHC` | sqrt transform | Safety-net indicator. FQHCs serve Medicaid/uninsured populations and receive PPS payments. High FQHC count suggests the ACO operates in underserved markets. |
| NP-to-PCP ratio | `N_NP / max(N_PCP, 1)` | None | Care model signal. Nationally, median NP/PCP ratio is ~0.5; A3563 has 1.16. High ratios indicate advanced practice provider–dependent models, common in rural and primary-care-shortage areas. r = 0.38 with expenditure. |
| PCP-to-Specialist ratio | `N_PCP / max(N_Spec, 1)` | None | Primary-care orientation. ACOs with high PCP/Spec ratios (>1) are primary-care-led; those below 0.5 are specialist-heavy. Different care coordination challenges. |

**Why weight 1.0×:** Infrastructure features are important but partially endogenous (ACOs choose their network configuration). They capture care delivery constraints more than patient-level structural factors.

#### E. Assignment Type (weight: 0.5×)

| Feature | Source | Transform | Rationale |
|---|---|---|---|
| Assignment type | `Assign_Type` | Binary: Prospective = 1, Retrospective = 0 | Affects beneficiary attribution timing and the ACO's ability to manage its panel prospectively. Important for interpreting utilization patterns but less impactful on structural cost comparability. |

**Why weight 0.5×:** Assignment type matters for financial mechanics and panel management strategy, but its effect on clinical comparability is secondary. The hard partition on track group already captures the primary program-structure distinction. Within a track group, assignment type is a secondary modifier.

### Distance Computation

1. **Partition** ACOs into BASIC (A/B/C/D, n=167) and ENHANCED (E/EN, n=309). All subsequent computation is within-partition.

2. **Transform** features as specified above (log₂, sqrt, imputation).

3. **Standardize** all features to zero mean, unit variance (z-score) within each partition. Standardization is partition-specific because BASIC and ENHANCED ACOs have different distributions.

4. **Apply domain weights** as specified (1.5× for Acuity, 1.25× for Composition, 1.0× for Scale and Infrastructure, 0.5× for Assignment Type). Concretely: multiply each z-scored feature by its domain weight before computing distance.

5. **Compute Euclidean distance** between every pair of ACOs within the partition:

   ```
   d(i, j) = sqrt( Σ_k  w_k × (z_ik − z_jk)² )
   ```

   where `w_k` is the domain weight for feature k.

6. **Select K = 30 nearest neighbors** for each ACO. With 167 BASIC ACOs, K=30 is 18% of the partition; with 309 ENHANCED ACOs, K=30 is 10%. Both ranges provide adequate statistical robustness while maintaining specificity.

### Validation Protocol

#### Face Validity Checks

Test on three archetype ACOs to ensure the cohort "makes sense" to a VBC practitioner:

1. **A3563** — Large BASIC-track rural ACO (WV, 37.5K beneficiaries, HCC 1.18, 18 CAHs, 76 FQHCs). Peers should be other large BASIC ACOs with above-average acuity and rural infrastructure. Preliminary prototype (15 nearest neighbors within BASIC) produced:
   - Healthcare Solutions Network (25K, HCC 1.18, BASIC-B) — strong match
   - CAMC Health Network (12K, also WV, BASIC-B) — face-valid geographic overlap
   - MaineHealth ACO (36K, BASIC-B) — similar rural New England system
   - Dartmouth Health (24K, BASIC-A) — similar rural academic system
   
   Weaknesses: some peers have substantially lower HCC (0.94–0.96 vs. 1.18). Increasing Acuity weight from 1.5 to 2.0 would tighten this axis if needed.

2. **A small urban physician-only ENHANCED ACO** (~5K beneficiaries, 0 hospitals, 0 CAHs). Peers should be other small ENHANCED physician-group ACOs.

3. **A very large integrated ENHANCED ACO** (~100K+ beneficiaries, many hospitals). Peers should be other large health-system-based ENHANCED ACOs.

#### Quantitative Checks

- **Track purity:** 100% by construction (hard partition).
- **Size spread:** For each cohort, compute the ratio of max to min N_AB among the 30 peers. Target: median ratio < 5×. If too wide, increase Scale weight.
- **Acuity spread:** For each cohort, compute the standard deviation of composite HCC among the 30 peers. Target: peer-cohort HCC std < 0.5 × MSSP-wide HCC std (i.e., the cohort should be at least 2× more homogeneous than the full population on acuity).
- **Symmetry check:** If A is in B's top-30, how often is B in A's top-30? Target: > 60% mutual membership. Low symmetry indicates an unstable feature space.
- **Outcome variance reduction:** The coefficient of variation for key outcomes (savings rate, expenditure, admissions) within each ACO's peer cohort should be smaller than the CV across the full partition. If peer cohorts don't reduce outcome variance, the feature set is not capturing meaningful structural differences.

#### Tuning Levers (in priority order)

If validation reveals problems:

1. **Increase Acuity weight** (1.5 → 2.0) if cohorts span too wide an HCC range.
2. **Increase Scale weight** (1.0 → 1.5) if cohorts mix 5K and 100K ACOs.
3. **Decrease K** (30 → 20) if cohorts are too heterogeneous overall (at the cost of statistical precision).
4. **Increase K** (30 → 40) if cohorts are too small for stable medians (less likely with n=167/309).

### Output

The ETL produces `site_data/aco_peer_cohorts.json`:

```json
{
  "metadata": {
    "method": "knn-within-track-partition",
    "k": 30,
    "features": [
      "composite_hcc", "pct_85plus", "perc_dual", "rr_weight_esrd",
      "rr_weight_dis", "perc_lti", "pct_under65", "log2_n_ab",
      "log2_total_clinicians", "sqrt_n_hosp", "sqrt_n_cah",
      "sqrt_n_fqhc", "np_pcp_ratio", "pcp_spec_ratio", "assign_type"
    ],
    "weights": {
      "acuity": 1.5,
      "composition": 1.25,
      "scale": 1.0,
      "infrastructure": 1.0,
      "assignment": 0.5
    },
    "basic_partition_size": 167,
    "enhanced_partition_size": 309
  },
  "cohorts": {
    "A3563": {
      "track_group": "BASIC",
      "peer_ids": ["A3283", "A3644", "A4513", ...],
      "peer_medians": {
        "Sav_rate": 3.81,
        "Per_Capita_Exp_TOTAL_PY": 13502,
        "QualScore": 81.22,
        "ADM": 298,
        "P_EDV_Vis": 694,
        "CAHPS_1": 83.5,
        "Measure_479": 0.155,
        "CMS_HCC_RiskScore_AGND_PY": 1.04
      },
      "cohort_description": "30 similar BASIC-track ACOs: large, above-average acuity, rural infrastructure"
    }
  }
}
```

### Frontend Display

Each ACO page displays **three reference points** for every key metric:

| Reference | Label | Color |
|---|---|---|
| This ACO | Bold/primary | — |
| MSSP Median | Subtle marker | Gray |
| Peer Median | Distinct marker | Blue/teal |

A brief cohort description appears at the top of the Table view: *"Compared to 30 structurally similar BASIC-track ACOs: large networks, above-average population acuity, rural care infrastructure."*

A collapsible "About this peer group" section lists the 30 peer ACOs (linked to their pages) and explains the matching methodology.

### Cohort Description Generation

Auto-generate a plain-English description from the centroid of the cohort's features:

1. **Track:** "BASIC-track" or "ENHANCED-track" (by partition).
2. **Size:** "small (<10K)" / "mid-size (10K–25K)" / "large (25K–50K)" / "very large (>50K)" based on cohort median N_AB.
3. **Acuity:** "below-average" / "average" / "above-average" acuity based on cohort median composite HCC vs. partition median.
4. **Infrastructure:** Classify by dominant pattern:
   - "physician-led" if median N_Hosp = 0
   - "hospital-affiliated" if median N_Hosp ≥ 1 and median N_CAH = 0
   - "rural" if median N_CAH ≥ 1 or median N_FQHC ≥ 5
   - "safety-net" if median N_FQHC ≥ 10
5. **Composition:** Add qualifiers if notable:
   - "high dual-eligible" if cohort median Perc_Dual > MSSP p75
   - "high ESRD exposure" if cohort median RR_weight_ESRD > MSSP p75

Example: *"30 similar BASIC-track ACOs: large, above-average acuity, rural infrastructure, moderate dual-eligible burden"*

---

## Priority & Feasibility Matrix

| # | Recommendation | Impact | Feasibility | New Data Needed |
|---|---|---|---|---|
| 1 | Percentile ranks | **Very High** | **Easy** | None — all 476 ACO manifests |
| 2 | Risk-adjusted expenditure | **Very High** | **Easy** | None — risk scores + expenditure in each manifest |
| 3 | Utilization median reference | **High** | **Easy** | None |
| 4 | CAHPS benchmark bars | **High** | **Easy** | None |
| 5 | Quality measure thresholds | **High** | **Easy** | None |
| 6 | Spending composition chart | **Medium** | **Medium** | None |
| 7 | Coding intensity gap | **High** | **Easy** | None — HCC and Demographic scores already in manifest |
| 8 | Demographics comparison | **Medium** | **Easy** | None |
| 9 | Waterfall annotations | **Medium** | **Medium** | None |
| 10 | Peer cohort comparison | **Very High** | **Medium** | None — requires ETL enrichment step with distance computation |

Items 1–5 and 7 are all computable from the existing 476 ACO manifests with no new data sources. Item 7 requires zero additional computation — the data is already in each manifest, it just needs to be juxtaposed. Together, these six items would transform the ACO pages from a data display into an analytical tool.
