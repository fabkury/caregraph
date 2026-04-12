## Overview

The CDC PLACES County-Level Data dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains county-level records used to build county entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each county entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to county entity pages using the CountyFIPS as the primary key.

## Join Strategy

This dataset is joined to county entity pages using the CountyFIPS field, which is formatted as a 5-digit string (state FIPS + county FIPS). During ETL, each row in the source dataset is matched to a county entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- CDC PLACES estimates are model-based small area estimates (SAE) derived from the Behavioral Risk Factor Surveillance System (BRFSS), not direct measurements — the estimates use multilevel regression and poststratification (MRP) to produce county-level prevalence from state-level survey data, which introduces model uncertainty reflected in the confidence intervals.
- The "age-adjusted" prevalence estimates use the 2000 US standard population for age adjustment; this facilitates comparison across counties with different age distributions, but the adjustment can mask the actual burden of disease in counties with very old or very young populations.
- PLACES reports both "crude" and "age-adjusted" prevalence for most measures; CareGraph displays age-adjusted values by default, but users comparing to local health department reports (which often use crude prevalence) may see discrepancies.
- The data release year does not match the survey year — PLACES 2023 data release uses BRFSS 2021 survey data, creating a 2-year lag; health behaviors and chronic disease prevalence may have shifted, particularly post-COVID-19.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
