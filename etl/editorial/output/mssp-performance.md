## Overview

The MSSP ACO Performance PY2024 dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains aco-level records used to build aco entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each aco entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to aco entity pages using the ACO_ID as the primary key.

## Join Strategy

This dataset is joined to aco entity pages using the ACO_ID field, which is formatted as a Character string (e.g., A0001). During ETL, each row in the source dataset is matched to a aco entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

- Savings and losses are calculated against a risk-adjusted, regionally-weighted benchmark that incorporates the ACO's own historical spending — ACOs that started with high spending have mechanically easier benchmarks, a known "rebasing" problem that CMS has tried to address with the Pathways to Success rule changes.
- The "Savings Rate" (Sav_rate) can be misleading: a negative savings rate means the ACO spent more than its benchmark, but the magnitude depends on both the ACO's efficiency and the benchmark's generosity — comparing savings rates across ACOs with different benchmark methodologies (e.g., BASIC vs. ENHANCED track) is not apples-to-apples.
- Quality scores transitioned from pay-for-reporting to pay-for-performance for many measures; ACOs in their first performance year may have different quality score calculations than established ACOs, affecting comparability.
- The beneficiary count (N_AB) reflects assigned beneficiaries, not all Medicare beneficiaries served; assignment methodology (prospective vs. retrospective, voluntary alignment) varies by track and can shift year-to-year, causing apparent changes in ACO size that reflect assignment rule changes rather than actual enrollment shifts.

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
