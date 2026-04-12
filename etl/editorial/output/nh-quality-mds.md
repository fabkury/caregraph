## Overview

The SNF Quality Measures (MDS) dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains snf-level records used to build snf entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each snf entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to snf entity pages using the Federal Provider Number (CCN) as the primary key.

## Join Strategy

This dataset is joined to snf entity pages using the Federal Provider Number (CCN) field, which is formatted as a 6-digit string, zero-padded. During ETL, each row in the source dataset is matched to a snf entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- MDS (Minimum Data Set) quality measures are derived from clinical assessments that nursing home staff complete for every resident; self-reporting bias is a known concern — facilities with poor documentation practices may paradoxically appear to have better outcomes because conditions are underreported.
- The "long-stay" vs "short-stay" distinction is critical: long-stay measures (e.g., pressure ulcers, falls with injury, antipsychotic use) apply to residents with 101+ cumulative days, while short-stay measures (e.g., rehospitalization rate, functional improvement) apply to those with shorter stays — mixing the two populations produces misleading quality comparisons.
- Antipsychotic medication use among long-stay residents is a headline measure, but CMS excludes residents with diagnoses of schizophrenia, Huntington's disease, or Tourette syndrome from the denominator — the reported rate is not "all residents" but "residents without qualifying exclusion diagnoses."
- Facilities with fewer than 20 eligible residents for a given measure are suppressed and show as missing data; small rural nursing homes frequently fall below this threshold across multiple measures, resulting in systematically incomplete quality profiles.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
