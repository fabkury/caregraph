## Overview

The Nursing Home Provider Info dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains snf-level records used to build snf entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each snf entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to snf entity pages using the Federal Provider Number (CCN) as the primary key.

## Join Strategy

This dataset is joined to snf entity pages using the Federal Provider Number (CCN) field, which is formatted as a 6-digit string, zero-padded. During ETL, each row in the source dataset is matched to a snf entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- The Five-Star Quality Rating System for nursing homes uses a different methodology than the hospital star ratings: nursing home stars incorporate health inspection results (most recent 3 years of standard and complaint surveys), staffing levels (from Payroll-Based Journal data), and quality measures (MDS-derived) — each component has its own 1-5 star rating plus an overall composite.
- Ownership type and legal business name can be misleading — many nursing homes operate under management agreements where the day-to-day operator differs from the legal owner; chains and private equity ownership are not directly identifiable from this dataset alone.
- "Number of certified beds" and "average number of residents per day" can diverge significantly — a facility with 120 beds but 60 average residents may be financially distressed or may serve a specialized population with high turnover.
- Facilities with a change of ownership (CHOW) in the past 3 years may have their health inspection history reset or partially carried over depending on CMS regional office decisions, making star ratings less reliable for recently acquired facilities.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
