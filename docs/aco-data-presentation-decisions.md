# ACO Data Presentation — Design Decisions

**Date:** 2026-04-12
**Status:** Implementing

## Overview

The ACO Table view previously rendered all 189 raw MSSP Performance fields as a flat two-column table (Field | Value) using CMS variable codes. This document records the decisions made while restructuring the view into domain-meaningful sections.

## Architectural Decision: Frontend-Side Grouping

**Choice:** Group, label, and format fields in the Astro page template rather than restructuring the ETL output.

**Why:** The raw JSON manifest intentionally preserves all original CMS field names for provenance fidelity and CSV export. Applying presentation logic at the frontend layer keeps the data pipeline clean and allows rapid iteration on display without re-running the ETL. The field mapping config lives in `site/src/config/aco-fields.ts`.

## Section Structure (10 sections)

The 189 raw fields map to 10 domain-meaningful sections, presented in this order:

| # | Section | Fields | Rationale |
|---|---------|--------|-----------|
| 1 | Program Structure | 7 | Context needed before interpreting any other data |
| 2 | Financial Performance (Savings Waterfall) | 20 | Core VBC outcome — shown as a stepped calculation |
| 3 | Per Capita Expenditure | 17 | Year × segment pivot table reveals trends |
| 4 | Risk Scores | 28 | Year × segment pivot tables (HCC + demographic + weights) |
| 5 | Beneficiary Demographics | 29 | Age, gender, race, enrollment — shown as distribution charts/tables |
| 6 | Utilization — Spending by Service | 12 | Per-capita spending breakdown by care setting |
| 7 | Utilization — Admissions & Visits | 17 | Rates per 1,000 beneficiaries with derived ratios |
| 8 | Provider Composition | 11 | Facility and clinician counts |
| 9 | CAHPS Patient Experience | 10 | Labeled survey domains with scores |
| 10 | Clinical Quality Measures | 20+ | Labeled measures with directionality indicators |

A final "Quality Reporting Flags" subsection within section 10 handles the binary flags (Met_QPS, etc.).

## Field Labeling Sources

- **CAHPS domains:** CMS CAHPS for ACOs Survey documentation. The numbered survey items (CAHPS_1 through CAHPS_11) map to specific patient experience domains. CAHPS_10 is not present in the PY2024 PUF.
- **Quality Measure IDs:** CMS MSSP Quality Measure Benchmarks documentation and the Quality Payment Program measure specifications. Each QualityID_NNN maps to a named clinical measure.
- **Financial fields:** CMS MSSP methodology documentation (Final Rule) and the MSSP PUF data dictionary.
- **All other fields:** CMS MSSP Public Use File (PUF) data dictionary.

## Formatting Conventions

| Data Type | Format | Example |
|-----------|--------|---------|
| Dollar amounts (per capita) | `$N,NNN` | $10,520 |
| Dollar amounts (aggregate) | `$N,NNN,NNN` | $92,407,570 |
| Percentages | `N.NN%` | 6.55% |
| Risk scores | `N.NNN` (3 decimal places) | 0.952 |
| Counts | `N,NNN` (locale-formatted) | 8,357 |
| Rates per 1,000 | `NNN` | 186 |
| Binary flags | Checkmark / cross icons | ✓ / ✗ |
| Suppressed values (`*`) | Displayed with tooltip explanation | * (suppressed) |
| Not reported (`-`) | "Not reported" in muted text | — |

## Suppressed and Missing Value Handling

- CMS suppresses values with `*` when cell sizes are <11 to protect beneficiary privacy. We display these with visual distinction and a tooltip: "Value suppressed by CMS to protect beneficiary privacy (cell size <11)."
- `-` indicates the ACO did not report via that pathway. We display as "—" with muted styling.
- Empty strings render as "—".

## Pivot Table Design (Expenditure & Risk Scores)

Time-series data (BY1, BY2, BY3, PY) is displayed as a pivot table:
- **Rows:** Population segments (ESRD, Disabled, Aged Dual, Aged Non-Dual)
- **Columns:** Time periods (BY1, BY2, BY3, PY)
- **Trend indicator:** A directional arrow comparing BY1 → PY (or BY3 → PY if BY1/BY2 unavailable)

Segment labels use full descriptive names, not CMS codes:
- ESRD → "End-Stage Renal Disease"
- DIS → "Disabled"
- AGDU → "Aged, Dual-Eligible"
- AGND → "Aged, Non-Dual"

## Quality Measure Directionality

Some measures are "inverted" — lower scores mean better performance:
- Measure 479 (All-Cause Unplanned Admissions): lower is better
- QualityID 001 (Diabetes HbA1c Poor Control >9%): lower is better

These are marked with "(lower is better)" in the display to prevent misinterpretation.

## Multi-Reporting Pathway Handling

Quality measures 134, 001, and 236 each have 4 reporting variants (WI, eCQM, MIPSCQM, MedicareCQM). Most ACOs report via only one pathway. We display the primary reported value prominently and collapse the unreported pathways, showing them in a muted sub-row only if the user expands the section.

## Section Navigation

An in-page table of contents with anchor links appears at the top of the Table view, allowing users to jump directly to any section. Each section heading includes a back-to-top link.

## CSS Approach

New styles are appended to `site/src/styles/global.css` using existing design tokens (colors, fonts, spacing). New class names follow the established pattern: `.pivot-table`, `.waterfall-table`, `.demo-bar`, `.quality-flags`, `.section-nav`.
