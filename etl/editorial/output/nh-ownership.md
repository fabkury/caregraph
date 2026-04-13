Now I have a thorough understanding of the dataset, the ETL code, and the style of existing methodology pages. Let me write the methodology page.

## Overview

The Nursing Home Ownership dataset is published by the Centers for Medicare & Medicaid Services (CMS) through the Care Compare program (formerly Nursing Home Compare) and is available as a public-use file on data.cms.gov (dataset identifier: `y2hd-n93e`). It contains one row per ownership record for Medicare- and Medicaid-certified skilled nursing facilities (SNFs) in the United States and its territories, with approximately 10 fields per record including owner name, owner type, and ownership percentage. Because each facility can have multiple owners, the dataset contains multiple rows per facility â€” reflecting the legal entity, managing entity, and all individuals or organizations holding 5% or more ownership interest as reported on CMS Form 855A (Medicare enrollment application). The dataset reflects current ownership status at the time of publication.

This dataset answers questions such as: Who owns or operates a given nursing facility? Is the facility for-profit, nonprofit, or government-owned? What percentage of the facility does each owner hold? Is the facility part of a chain? How many distinct entities have an ownership stake? It provides the ownership and corporate structure information displayed on CareGraph SNF entity pages.

## Join Strategy

Each ownership record is joined to a CareGraph SNF entity page using the Federal Provider Number field, which is the facility's CMS Certification Number (CCN). The CCN is a 6-character string, zero-padded on the left (e.g., `015001`). During ETL, the join key is normalized by the `normalize_ccn` function, which strips leading and trailing whitespace and enforces zero-padding to six digits. Because each facility may have multiple owners, the join produces a one-to-many relationship: all matching ownership records are collected into an `ownership` array on the SNF entity page manifest. SNF pages without matching ownership records display no ownership section. Source rows with CCN values that do not match any existing SNF entity page are excluded from the site build. Malformed CCN values that fail normalization are skipped and logged during the ETL build step.

## Known Limitations

- **Self-reported data.** Ownership information is self-reported by facilities on CMS Form 855A (Medicare enrollment application). CMS does not independently verify the accuracy or completeness of reported ownership structures. Misreporting is possible and difficult to detect from the data alone.
- **Beneficial ownership opacity.** Complex ownership structures â€” private equity firms, real estate investment trusts (REITs), and multi-layered holding companies â€” may not be fully transparent. The "operating company" listed may differ from the ultimate beneficial owner. CMS has proposed but not yet finalized rules requiring more granular ownership disclosure.
- **Current snapshot only.** The dataset captures current ownership as of the publication date. Ownership history and change-of-ownership (CHOW) events are not included. This is a significant gap because CMS resets certain enforcement actions upon ownership change, and research shows quality often declines during ownership transitions.
- **Reporting lag.** Change-of-ownership events may take 3â€“6 months to appear in the dataset due to the time required for CMS to process Form 855A updates and publish refreshed data.
- **Chain classification ambiguity.** Chain affiliation is indicated in the data but the definition of "chain" is broad â€” small regional operators with 2â€“3 facilities are classified alongside national operators with 100+ facilities. No threshold distinguishes regional from national chains.
- **Ownership type categories.** The for-profit, nonprofit, and government ownership categories are the most commonly used classification, but the distinction can be misleading. Some nonprofit facilities are part of large health systems that exhibit staffing and investment patterns comparable to for-profit chains.

## Data Quality Notes

- **Ownership percentage as a string.** The `ownership_percentage` field in the source CSV is stored as a string and may contain formatting characters. The ETL parses it to a float using `_try_float`; values that fail parsing are set to null.
- **Missing or blank fields.** Owner name, owner type, and ownership percentage fields may be blank for some records. The ETL normalizes empty strings and the sentinel values "N/A" and "Not Available" to null in the JSON manifest. Remaining non-empty fields from each row are included as-is.
- **Character encoding issues.** The source CSV is read with `errors="replace"` during ETL, meaning malformed UTF-8 byte sequences are replaced with the Unicode replacement character (U+FFFD). Owner names containing non-ASCII characters (e.g., accented letters in proper names) may appear with replacement characters rather than the intended glyphs.
- **No deduplication of owners.** The ETL collects all ownership rows matching a CCN without deduplication. If the source data contains duplicate rows for the same owner entity at the same facility, both appear in the `ownership` array on the manifest.
