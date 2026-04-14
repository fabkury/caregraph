# County page redesign — design decisions

This document records decisions made for the county-page overhaul completed
on 2026-04-13. The goals were:

1. Remove empty sections — only render a section if there is data.
2. Abolish the Explore/Table split — a single unified view covering
   **every** variable available for the county.
3. Use human-readable labels instead of raw column codes.
4. Group variables logically by health-services domain.
5. Visualize where a chart beats a number.
6. Contextualize every metric against the distribution of all US counties
   (percentile badges + national medians).

## Data sources feeding a county page

| Source | Dataset id | Fields surfaced |
| --- | --- | --- |
| **Medicare Geographic Variation PUF (county level)** | `geo-var-county` | 150+ of the 247 raw columns, re-grouped into Beneficiary profile, Spending, Utilization, Preventable admissions |
| **CDC PLACES (county)** | `cdc-places` | All 40 measures (Health Outcomes, Prevention, Health Risk Behaviors, Disability, Health-Related Social Needs, Health Status) |
| **CDC SDOH Measures for County** | `cdc-sdoh` | All 9 measures (Economic, Education, Housing, Demographics) |
| **Cross-links** | built during ETL | Hospitals, SNFs, ACOs serving this FIPS |

## Data dictionary strategy

CMS publishes a PDF data dictionary with the Medicare Geographic Variation PUF,
but parsing a PDF into a structured label map is brittle. The column naming
convention in that file is, however, highly regular and stable across vintages
(`{SERVICE}_MDCR_{STDZD_}?PYMT_{AMT,PC,PCT,PER_USER}`, `BENES_{SERVICE}_{CNT,PCT}`,
`{SERVICE}_{EVNTS,CVRD_STAYS,CVRD_DAYS,VISITS,EPISODES}_PER_1000_BENES`, and the
AHRQ Prevention Quality Indicator `PQI##_...` codes). Rather than round-tripping
through the PDF we encode the expansion rules and the per-column labels in a
single TypeScript file (`site/src/config/county-fields.ts`). The PLACES and SDOH
datasets ship their own machine-readable `measure` and `short_question_text`
columns, so those labels come straight from the source CSVs.

Future work: if CMS exposes a machine-readable JSON/CSV dictionary for
Geographic Variation we should replace the hand-authored `county-fields.ts`
with a generated file.

## Section layout

The unified page has these sections, each rendered only when the underlying
data exists for this county:

1. **Overview** — county name/state, FIPS, Medicare population headline,
   provenance summary, percentile legend.
2. **Beneficiary Profile** — FFS vs MA mix, demographics, dual eligibility,
   average HCC risk score.
3. **Medicare Spending per Capita** — payment-composition bar chart
   (standardized per-capita spending by service setting) + total spending
   cards. Red marker = national county median.
4. **Utilization** — per-1000-beneficiary rates for IP stays, ER visits,
   OP visits, SNF stays, HH episodes, hospice, imaging, tests, procedures,
   DME, etc. Grid of metric cards.
5. **Preventable Admissions (AHRQ PQI)** — hospitalization rates per 100 000
   for ambulatory-care-sensitive conditions (diabetes, COPD/asthma,
   hypertension, CHF, bacterial pneumonia, UTI, lower-extremity amputation),
   age-stratified.
6. **Chronic Disease Prevalence** — PLACES Health Outcomes + Health Status
   measures with 95 % CIs.
7. **Prevention & Screening** — PLACES Prevention measures.
8. **Health Risk Behaviors** — PLACES Health Risk Behaviors.
9. **Disability** — PLACES Disability measures.
10. **Health-Related Social Needs** — PLACES social-needs measures +
    CDC SDOH (poverty, unemployment, education, broadband, housing,
    demographics).
11. **Related Facilities & ACOs** — crosslinked entities in this county.
12. **Full Data Table** — collapsible table with every raw field that we
    have a label for, plus the national median column for context.
13. **Methodology** — provenance envelopes.

If a section has **no values** for the current county (which happens for
small rural counties that are suppressed in some datasets) it is not
rendered.

## Contextualization — percentile badges

We compute a national benchmark file (`site_data/county_benchmarks.json`)
that mirrors `hospital_benchmarks.json`:

- For every numeric field in the county manifest we compute
  p10 / p25 / p50 / p75 / p90 / mean / n across all counties.
- For every county we compute the percentile rank of its value.
- Fields flagged `lowerIsBetter` (costs, readmission rates, PQI
  admissions, chronic disease prevalence, SDOH adversity measures) use the
  inverted color ramp — a low percentile is green (good), a high percentile
  is red (bad).

Percentiles rendered:

- **Metric cards**: small badge next to the value, e.g. `p42`. Colored
  by the standard `pctl-low`/`pctl-mid`/`pctl-high` classes (or the
  `pctl-inv-*` variants for lower-is-better fields).
- **Composition bars**: red vertical marker on each bar indicates the
  national county median share of total spending.

## Visualizations

- **Spending composition bar chart** (existing `.composition-row` style):
  each service setting is a horizontal bar whose length is its share of
  total standardized per-capita Medicare spending, with a vertical marker
  for the national median share. Makes it obvious when a county is
  over- or under-weighted on inpatient vs outpatient vs post-acute.
- **PLACES prevalence grid**: metric card with CI whiskers.
- **PQI bar chart**: per-condition admissions per 100 000, grouped by
  age band.
- **Utilization grid**: ordered by service category, with the per-1000
  value, total users, and percentile badge.

## Handling missingness

- A metric with a `null`/missing value is omitted from its card grid (not
  rendered as "—").
- If an entire section has zero non-null values, the whole section is
  skipped and the nav item is dropped.
- The SDOH enrichment is best-effort: if the CDC SODA API is unreachable
  at ETL time, the SDOH block simply won't render for any county.

## Follow-up ideas not in scope

- Year toggle (currently shows latest vintage).
- Small-multiple sparklines when we ship multiple vintages per county.
- Peer-county cohort (similar population size / urban-rural / region)
  analogous to the ACO peer cohort logic.
- In-browser choropleth: click a metric to map it across the US.
