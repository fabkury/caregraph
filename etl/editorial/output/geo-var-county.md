## Overview

The Medicare Geographic Variation by County dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains county-level records used to build county entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each county entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to county entity pages using the FIPS county code as the primary key.

## Join Strategy

This dataset is joined to county entity pages using the FIPS county code field, which is formatted as a 5-digit string (state FIPS + county FIPS), zero-padded. During ETL, each row in the source dataset is matched to a county entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- All spending metrics are available in both "actual" and "standardized" (price-adjusted) variants; CareGraph uses the standardized per-capita figures (suffix _STDZD_PYMT_PC) to enable fair cross-county comparisons by removing geographic payment adjustments (wage index, cost-of-living, teaching hospital add-ons, etc.).
- The data covers Medicare fee-for-service (FFS) beneficiaries only — counties with high Medicare Advantage penetration (e.g., parts of Florida, Southern California, Puerto Rico) have a smaller and potentially non-representative FFS population, making per-capita spending figures less generalizable to the full Medicare population.
- County-level aggregation uses the beneficiary's county of residence, not the county where services were delivered; border counties and counties near major medical centers may show utilization patterns that reflect cross-county care-seeking behavior.
- Small counties (fewer than 11 beneficiaries in a given category) have values suppressed per CMS cell-size suppression rules to protect beneficiary privacy; this disproportionately affects rural counties and specific service categories (e.g., hospice, SNF) in low-population areas.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
