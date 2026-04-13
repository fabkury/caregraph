## Overview

The ACO Assigned Beneficiaries by County dataset is published by CMS as part of the Medicare Shared Savings Program (MSSP) public use files on data.cms.gov. It reports the number of Medicare fee-for-service beneficiaries assigned to each ACO, broken down by the beneficiary's county of residence. Each row represents one ACO-county pair with the count of assigned beneficiaries in that county. The current file covers Performance Year 2023.

This dataset enables geographic analysis of ACO service areas: which counties an ACO draws beneficiaries from, how concentrated or dispersed its beneficiary population is, and how ACO coverage overlaps with county-level health metrics. CareGraph uses it to build the beneficiary-by-county section on ACO entity pages and to create cross-links between ACO and county pages.

## Join Strategy

This dataset joins to ACO entity pages using the ACO_ID field (character string, e.g., "A0001"). During ETL, the ACO_ID is normalized to uppercase and matched to ACO entity manifests. The county dimension uses a derived FIPS code: the source file provides State_Name and County_Name rather than FIPS codes directly, so the ETL maps these to 5-digit FIPS codes via a name-based lookup. Suffix-aware matching handles common variations (e.g., "St." vs "Saint", "County" suffix presence or absence). ACO-county pairs that cannot be matched to a valid FIPS code are logged and excluded.

For each ACO, the ETL selects the top counties by beneficiary count for display on the ACO page and creates bidirectional cross-links from county pages back to ACOs that serve beneficiaries in that county.

## Known Limitations

- **Cell-size suppression.** ACO-county combinations with fewer than 11 assigned beneficiaries are suppressed per CMS privacy rules. For ACOs with wide geographic spread, many county rows are suppressed. Summing unsuppressed rows undercounts the ACO's total assigned beneficiaries.
- **Medicare FFS only.** Beneficiary counts reflect only Original Medicare (fee-for-service) enrollees assigned through the MSSP attribution methodology. Medicare Advantage enrollees are excluded entirely, which underrepresents total ACO-aligned lives in markets with high MA penetration.
- **Retrospective attribution.** Beneficiaries are assigned to ACOs based on the plurality of their primary care services during the performance year. This is a retrospective calculation and may not align with the beneficiary's self-identified primary care relationship or the provider's perception of their panel.
- **Residence county, not service county.** The county field reflects the beneficiary's county of residence, not where they received care. Beneficiaries who cross county lines for care are counted in their home county, which can overstate an ACO's presence in residential counties and understate it in counties with major medical centers.
- **Temporal misalignment.** The beneficiary-by-county file may cover a different performance year than the MSSP performance results file (e.g., PY2023 beneficiary counts paired with PY2024 financial results). Year alignment should be verified when combining these datasets.
- **Name-based FIPS matching.** Because the source file uses county names rather than FIPS codes, the ETL's name-to-FIPS mapping can fail for counties with unusual names, name changes, or independent cities (e.g., Virginia independent cities). Unmatched counties are excluded from the geographic visualization.

## Data Quality Notes

- Suppressed values appear as `*`, `.`, or blank strings in the source CSV. The ETL normalizes all of these to null in the JSON manifest. Rows where the beneficiary count is null are retained in the raw data but excluded from geographic aggregations.
- Column names vary across annual releases (e.g., casing changes, underscore vs. space). The ETL uses a candidate-list column matching strategy via `_find_column()` to handle these variations without manual mapping updates.
- ACO_ID is preserved as a string throughout the pipeline. Leading characters and formatting are maintained exactly as published by CMS to ensure consistent matching across MSSP datasets.
- No deduplication is performed — each row represents a unique ACO-county pair as published. If CMS publishes duplicate rows (rare but observed in some vintages), both are ingested.
