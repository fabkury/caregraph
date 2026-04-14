## Overview

The ACO Participants dataset identifies the provider organizations participating in the Medicare Shared Savings Program (MSSP), published by the Centers for Medicare & Medicaid Services (CMS). Each record links a participant—identified by Tax Identification Number (TIN) and, where applicable, CMS Certification Number (CCN)—to its parent Accountable Care Organization (ACO) via the ACO_ID field. The file is published annually as a point-in-time snapshot, typically reflecting the participant roster as of January 1 of the performance year.

This dataset answers questions such as: which provider organizations belong to a given ACO, how many TINs are enrolled in each ACO, and which hospitals (by CCN) participate in shared savings arrangements. Because participants are identified at the TIN level rather than the individual clinician level, a single record may represent a large multi-provider group practice encompassing hundreds of individual physicians. The dataset is essential for mapping the organizational structure of MSSP ACOs and for cross-linking ACO participation to hospital-level quality and cost metrics.

## Join Strategy

CareGraph joins this dataset to ACO entity pages using the `ACO_ID` field, a character string in the format `A0001` (a letter prefix followed by a four-digit zero-padded number). Each participant record is matched to its corresponding ACO page at `/aco/{ACO_ID}`. No normalization of ACO_ID is required beyond preserving the original string format.

Hospital participants that carry a CCN enable a secondary cross-link to hospital entity pages at `/hospital/{CCN}`. The CCN is a 6-character zero-padded string and is matched using the same normalization applied across all CareGraph hospital joins. Participant records without a CCN (e.g., physician group practices, FQHCs) link only to the ACO page and do not generate hospital cross-links.

## Known Limitations

- **TIN ≠ provider count.** Each participant record represents a single TIN, which may encompass anywhere from one solo practitioner to hundreds of clinicians in a large group practice. Counting participant records as a proxy for provider headcount significantly understates the true number of clinicians in an ACO.
- **Point-in-time snapshot only.** The participant list reflects the roster as of approximately January 1 of the performance year. Mid-year additions (via ACO expansion requests) and mid-year departures are not captured until the next annual file release.
- **Multi-ACO participation.** MSSP rules permit a provider organization to participate in multiple ACOs under different TINs. A physician group with locations in two ACO service areas may appear in both participant lists, which can produce double-counting in cross-link or aggregate analyses if not deduplicated.
- **No Medicare Advantage coverage.** This dataset covers only MSSP (Original Medicare fee-for-service ACOs). Providers participating exclusively in Medicare Advantage ACO arrangements are not included.
- **CCN availability is limited to institutional providers.** Only hospital and certain facility participants carry a CCN. Physician group practices, FQHCs, and other non-hospital participants lack a CCN, limiting the ability to cross-link these records to other CMS facility-level datasets.
- **Reporting lag.** The participant file for a given performance year is typically published several months after the start of that year, and may not align with the actual roster at the time of data consumption.

## Data Quality Notes

- **ACO_ID format.** The `ACO_ID` field is a character string (e.g., `A0001`), not a numeric field. ETL preserves the original string representation to avoid stripping the alphabetic prefix or leading zeros.
- **CCN sparsity.** The CCN field has a high null rate because it is populated only for institutional (hospital/facility) participants. Non-hospital TINs leave this field blank, which is expected behavior rather than a data quality defect.
- **TIN as string.** TIN values are 9-digit numeric identifiers stored as strings to preserve leading zeros. Any numeric casting would corrupt TINs beginning with zero.
- **No deduplication across years.** When multiple vintage files are loaded, the same TIN–ACO_ID pair may appear in successive annual snapshots. CareGraph displays the most recent performance year file and does not merge or deduplicate across vintages.
