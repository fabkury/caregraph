## Overview

The Hospital Value-Based Purchasing TPS dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains hospital-level records used to build hospital entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each hospital entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to hospital entity pages using the Provider Number (CCN) as the primary key.

## Join Strategy

This dataset is joined to hospital entity pages using the Provider Number (CCN) field, which is formatted as a 6-digit string, zero-padded. During ETL, each row in the source dataset is matched to a hospital entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- The Total Performance Score (TPS) is a weighted composite: Clinical Outcomes (25%), Safety (25%), Person & Community Engagement (25%), and Efficiency & Cost Reduction (25%) — but a hospital missing an entire domain has the remaining domains reweighted, making cross-hospital comparisons imprecise.
- Hospitals that do not meet the minimum case thresholds for enough measures in a domain receive no domain score; approximately 15-20% of IPPS hospitals do not receive a TPS in any given year.
- The "Efficiency & Cost Reduction" domain uses Medicare Spending Per Beneficiary (MSPB) which only captures fee-for-service spending — hospitals in markets with high Medicare Advantage penetration have MSPB calculated on a smaller, potentially non-representative FFS population.
- Performance scores reflect both achievement (vs. national floor/benchmark) and improvement (vs. the hospital's own baseline); a hospital can score well on improvement while still being below the national median.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
