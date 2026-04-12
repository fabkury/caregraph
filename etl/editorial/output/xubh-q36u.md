## Overview

The Hospital General Information dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains hospital-level records used to build hospital entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each hospital entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to hospital entity pages using the CCN (CMS Certification Number) as the primary key.

## Join Strategy

This dataset is joined to hospital entity pages using the CCN (CMS Certification Number) field, which is formatted as a 6-digit string, zero-padded. During ETL, each row in the source dataset is matched to a hospital entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- The "Hospital Overall Rating" (star rating) is calculated by CMS using a latent variable model grouping ~60 measures into 5 categories; hospitals can have "Not Available" when they have insufficient measure data or have opted out of star ratings.
- Emergency services is self-reported by hospitals and does not distinguish between full ED, freestanding ED, and urgent care center capabilities.
- VA hospitals, tribal hospitals, and hospitals in US territories are included in the file but often lack star ratings and may use non-standard CCN formats (e.g., VA facilities have CCNs starting with certain alpha prefixes that may not match other CMS datasets).
- The "Hospital Type" field conflates Critical Access Hospitals (CAHs) with other acute care types; CAHs have fundamentally different cost reporting and payment rules that affect comparability of metrics across types.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
