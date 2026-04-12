# CareGraph — Product Specification

**Version:** 0.1 (Draft)
**Prepared:** April 2026
**Status:** Internal product brief, pre-implementation
**Derived from:** `cms-dataset-combinations-for-vbc.md`
**License target:** MIT (code + ETL). Data content: per-source licenses documented in the Methodology Hub.
**Hosting target:** Single low-cost VPS. Static-only serving. No ads. No auth.

---

## Table of Contents

1. [Working Names](#1-working-names)
2. [Executive Summary](#2-executive-summary)
3. [Public Pitch (Embedded)](#3-public-pitch-embedded)
4. [Goals and Non-Goals](#4-goals-and-non-goals)
5. [Users and Use Cases](#5-users-and-use-cases)
6. [Core Product Concepts](#6-core-product-concepts)
7. [Information Architecture](#7-information-architecture)
8. [Page Specifications](#8-page-specifications)
9. [The Ten Analytical Use Cases](#9-the-ten-analytical-use-cases-from-the-source-brief)
10. [Cross-Linking Model](#10-cross-linking-model)
11. [Trust and Methodology System](#11-trust-and-methodology-system)
12. [Export System](#12-export-system)
13. [Technical Architecture](#13-technical-architecture)
14. [Repository Structure](#14-repository-structure-proposed)
15. [Design Principles](#15-design-principles-editorial)
16. [Out-of-Scope for v1](#16-out-of-scope-for-v1-parking-lot)
17. [Open Questions](#17-open-questions)
18. [Milestones](#18-milestones-suggested)

---

## 1. Working Names

Three candidates for discussion:

1. **CareGraph** — Leads with the core value proposition: a graph of interlinked CMS entities where every hospital, SNF, clinician, ACO, county, condition, and drug is a node, and the join keys (CCN, NPI, TIN, ACO ID, FIPS) are the edges. Short, memorable, evocative. Caveat: "graph" suggests visualization; reality is more "deeply interlinked pages."
2. **Linchpin** (or **Linchpin Health**) — Names the thing that makes the system work: the linchpin identifiers (CCN, NPI, TIN, FIPS) that hold the dataset combinations together. Plain-spoken, practical, technical-but-accessible. Risk: common English word, weaker for SEO.
3. **Medicare Commons** — Frames the tool as a public commons for Medicare data — emphasizes the free, open-source, public-good positioning. Less flashy, more civic. Pairs well with the MIT + no-ads posture.

Alternates worth considering: **ValueLens**, **CareAtlas**, **Through-line**, **Strata CMS**, **Confluence Health** (namespace collision risk with Atlassian).

**Recommended for this spec:** **CareGraph**. The interlinking is the distinctive property; the name should point at it directly. Every reference in this document uses "CareGraph" as a placeholder — swap freely.

---

## 2. Executive Summary

CareGraph is a free, open-source, ad-free website that unifies 100+ publicly available CMS datasets (plus curated external SDOH, workforce, and environmental data) into a single richly interlinked exploration tool. It serves two audiences simultaneously: (a) value-based care leaders — ACO executives, medical directors, population health strategists — who need scorecards, benchmarks, maps, and actionable rankings; and (b) researchers, journalists, and data-curious clinicians who need filterable tables, full methodology, and downloadable precomputed joins.

The product's core bet is that most of the analytical value CMS data can deliver is already computable ahead of time. Rather than ship raw datasets and expect users to assemble joins themselves, CareGraph precomputes the ten most-valuable dataset combinations documented in the source brief (`cms-dataset-combinations-for-vbc.md`) and exposes each combination through canonical entity pages (Hospital, SNF, Clinician, ACO, County, Condition, Drug, DRG…) with dense cross-links. The ten analytical use cases from the source brief drive which joins the ETL builds; users reach each use case in v1 by navigating the entity spine directly. A unified **Explore** / **Table** mode toggle lets leaders browse and researchers interrogate the same page. Guided "playbook" pages that walk users through each use case are deferred to v2 (see §16).

All heavy lifting runs on the maintainer's workstation via a manual ETL. The VPS serves only static files. The browser renders precomputed JSON manifests through a lightweight data grid; in-browser SQL querying is deferred to v2 (see §16).

---

## 3. Public Pitch (Embedded)

> **CareGraph — the public Medicare data you already paid for, finally connected.**
>
> The federal government publishes hundreds of high-value datasets about how Medicare works: which hospitals readmit patients, which nursing homes are understaffed, which counties spend the most per beneficiary, which clinicians prescribe outside the norm. Using these datasets *together* is hard. Join keys differ. File formats differ. Methodology notes live in PDFs. Most people give up.
>
> CareGraph stitches them together. Look up a hospital, see its readmission performance **and** its downstream SNF quality **and** its affiliated ACOs **and** its county's SDOH context — all in one place, all cross-linked, all exportable as CSV. Click any number to see exactly where it came from, how stale it is, how many patients are behind it, and what it does not tell you.
>
> Free. No ads. No login. Source code MIT-licensed on GitHub. Built and maintained by a small group of contributors who believe public data should be genuinely usable, not just technically available.

This pitch block is the canonical copy used on the Home hero and the About page.

---

## 4. Goals and Non-Goals

### 4.1 Goals

- **G1 — Maximize usefulness.** Pre-compute every high-value join documented in the source brief so users read answers off the page instead of building a pipeline.
- **G2 — Maximize interlinking.** Every entity page links to every other entity it relates to. A user following their curiosity should never hit a dead-end that says "now go download three CSVs from data.cms.gov."
- **G3 — Serve both audiences in one UI.** VBC leaders get polished scorecards, maps, and benchmarks; researchers get filterable tables, methodology, and downloads. Same pages, different emphases, one-click toggle.
- **G4 — Trust as a first-class feature.** Every metric carries provenance, freshness, sample size, suppression status, and known limitations inline. Methodology is loud, not buried.
- **G5 — Low ongoing cost.** Static-first architecture, precomputed data, VPS-hostable, zero scheduled cloud infra.
- **G6 — Fully reproducible.** ETL and site code MIT-licensed; anyone can rebuild CareGraph from data.cms.gov on their own machine.

### 4.2 Non-Goals (v1)

- **NG1** — Live querying of data.cms.gov or any external source at request time.
- **NG2** — User accounts, authentication, or server-side personalization.
- **NG3** — A public REST/GraphQL API. (Bulk parquet/CSV downloads serve this need partially.)
- **NG4** — LLM-powered natural-language query. Noted as a candidate for a future version.
- **NG5** — Any PHI-bearing or non-public data.
- **NG6** — Automated ETL scheduling. ETL runs manually on the maintainer's workstation.
- **NG7** — Mobile-first design. The site is responsive but tuned for desktop use.

---

## 5. Users and Use Cases

### 5.1 Primary personas

1. **Elena — VP of Population Health, mid-size MSSP ACO.** Wants: which SNFs in her service area should be in her preferred network; how her ACO compares to competitors; which counties have the worst SDOH-adjusted outcomes. Comfort with data: reads scorecards and charts, delegates SQL. Primary entry points: her ACO's canonical page and the Hospital/SNF entity browsers, following cross-links into downstream post-acute partners.
2. **Marcus — health services researcher at a university.** Wants: county-level joins of chronic conditions × SVI × geographic variation; methodology confidence to cite in a paper; CSV and parquet downloads of every cut to analyze in his own tools (R, pandas, DuckDB CLI). Comfort with data: fluent. Primary entry points: Explore browsers in Table mode + Methodology Hub + the downloadable parquet artifacts.
3. **Ruth — investigative journalist.** Wants: which nursing home chains have the worst aggregate deficiencies; what their cost reports show; which ACOs they affiliate with. Needs CSVs for her own spreadsheet work. Primary entry points: SNF Explore browser, Compare view.
4. **Diego — resident physician curious about his hospital's MSPB.** Wants: to understand what drives spending after discharge; to see peer benchmarks. Comfort: technical but time-poor. Primary entry points: his hospital's canonical page, the MSPB episode-decomposition panel within it, and the Compare view against peer hospitals.

### 5.2 Analytical use cases covered (the ten from the source brief)

Each of these drives which joins the v1 ETL precomputes. In v1, users reach them by navigating the entity spine; guided narrative pages are deferred to v2 (§16). See §9 for the full mapping from use case → starting entity → navigation path.

1. Post-Acute Care Network Optimization
2. Population Risk Stratification Using Community-Level SDOH
3. Physician Network Performance Profiling
4. Readmission Root-Cause Analysis Across the Care Continuum
5. ACO Competitive Benchmarking and Market Intelligence
6. Health Equity Gap Analysis
7. Drug Spending Optimization
8. Workforce Gap Analysis for Network Adequacy
9. Episode-Level Spending Decomposition
10. Chronic Disease Burden Mapping for Care Management Targeting

---

## 6. Core Product Concepts

### 6.1 Entity spine

The site is organized around **entities**. An entity is anything with a stable public identifier that can be joined across datasets. The full v1 entity set:

| Entity | Join key | Approx. count | Primary source datasets |
|---|---|---|---|
| Hospital | CCN | ~5,000 | HVBP, HRRP, HAC, HCAHPS, MSPB, Cost Report, Inpatient by Provider, Unplanned Visits |
| SNF / Nursing Home | CCN | ~15,000 | SNF VBP, MDS, PBJ, Penalties, Cost Report, PAC Utilization |
| Home Health Agency | CCN | ~11,000 | HHVBP, HHCAHPS, Home Health Care Agencies |
| Hospice | CCN | ~5,000 | Hospice QRP, Hospice CAHPS |
| Dialysis Facility | CCN | ~7,800 | ESRD QIP, Kidney Care Choices, CEC |
| Clinician | NPI | ~1.3M | Physician Utilization, MIPS Clinician Reporting, Part D Prescribers, Facility Affiliations |
| Physician Group | TIN | ~250K | MIPS Group, ACO Participants |
| ACO | ACO ID | ~600 | MSSP, REACH, ACO Participants, ACO Beneficiary by County |
| County | FIPS (5) | ~3,200 | Geographic Variation, Chronic Conditions, Market Saturation, MSSP County |
| State | FIPS (2) | 51 | All national/state rollups |
| HRR | HRR code | ~300 | Geographic Variation by HRR |
| CBSA / MSA | CBSA code | ~950 | Market Saturation by CBSA |
| Census Tract | FIPS (11) | ~74,000 | PLACES, SVI, USDA Food Atlas, EJScreen, ACS |
| Drug | Generic + Brand pair | ~2,500 | Part B by Drug, Part D by Drug, Discarded Units |
| Chronic Condition | CMS 21 canonical | 21 | Chronic Conditions (Specific + Multiple), PLACES |
| DRG | 3-digit code | ~740 | Inpatient by Provider & Service |
| HCPCS | 5-char code | ~13,000 | Physician by Provider & Service, Part B Drug |
| Episode (MSPB) | CCN + condition | abstract | Hospital Spending by Claim, MSPB |

Each entity has a **canonical page** at a stable URL (e.g., `/hospital/123456`, `/county/06037`, `/clinician/1234567890`). Every mention of an entity anywhere on the site — in prose, in a table cell, in a map tooltip — is a link to its canonical page.

### 6.2 Unified Explore / Table modes

Every entity page offers two visual modes:

- **Explore mode** (default): scorecards, choropleth maps, ranked leaderboards, trend sparklines, prose commentary, contextual highlights. Designed for Elena and Diego.
- **Table mode**: the same data rendered as a filterable, sortable, groupable data grid with per-column methodology popovers (source dataset, vintage, suppression flags) and one-click CSV export respecting the current filters, sort, and groupings. Designed for Marcus and Ruth.

Toggle lives in the global header and is sticky per session (localStorage).

> **v1 scope note.** An earlier draft of this spec called the second mode "Query mode" and included a DuckDB-WASM SQL console with cross-parquet querying (page-scoped, entity-type-scoped, and cross-entity tiers plus a dedicated `/lab` page with a schema catalog). All of that is deferred to v2 (see §16). v1 Table mode is a high-quality, methodology-aware data grid — not a SQL surface. v1's priorities are **accuracy, trust, correctness, and thoroughness** within a bounded scope; arbitrary user querying is a large, ambitious feature line that deserves its own design phase and is best built on top of an already-solid v1 data foundation.

### 6.3 Trust as first-class

Every metric cell, chart label, and table column carries a trust affordance — a small info icon that reveals provenance, freshness, sample size, suppression status, confidence interval (if available), and known caveats. Pages additionally open with a **Coverage Card** summarizing aggregate trust: "This page composes 7 datasets. 6 are current to 2026-Q1; Cost Report is current to 2022. 4,982 of 5,012 US hospitals have full coverage; 30 are missing at least one metric. See Methodology →"

### 6.4 Interlink density as an explicit quality gate

Every canonical entity page must offer, on average, **≥10 distinct outbound links** to other canonical entities, and no leaf value naming an entity should appear as plain text. County names are links. DRG codes are links. Drug names are links. Condition names are links. Clinician names are links. Violating this gate fails ETL validation.

---

## 7. Information Architecture

### 7.1 Global navigation

```
[CareGraph logo]  Home   Explore ▾   Maps   Methodology   Workspace   About
                                                        [Explore / Table mode toggle]  [🔍 search]
```

- **Home** — landing; pitch, entity quick-pick, current data vintages.
- **Explore** — dropdown listing entity browsers: Hospitals · SNFs · HHAs · Hospices · Dialysis · Clinicians · Groups · ACOs · Counties · States · Drugs · Conditions · DRGs.
- **Maps** — map-first entry point.
- **Methodology** — dataset dictionary, lineage, known limitations, downloadable bundles.
- **Workspace** — localStorage-backed pins, cohorts, and notes.
- **About** — pitch, license, GitHub link, citation, contributors.

### 7.2 URL scheme

```
/                                              Home
/explore/hospitals?state=OH&sort=-mspb         Entity browser (filtered, sharable)
/hospital/123456                               Canonical hospital page
/hospital/123456/quality                       Section anchor / deep link
/hospital/123456/episodes/HF                   Episode-decomposition drilldown (HF)
/snf/125678
/hha/017001
/clinician/1234567890
/aco/A1234
/county/06037                                  Los Angeles, CA
/state/CA
/drug/metformin
/condition/diabetes
/drg/470
/compare?hospital=123456,234567,345678
/map?layer=chronic.diabetes.prevalence&geo=tract
/methodology
/methodology/dataset/hospital-readmissions-reduction-program
/workspace
/search?q=cleveland+clinic
/about
```

URLs are shareable, bookmarkable, and stable across ETL refreshes. Entity IDs never change; metric vintages are appended as URL parameters only when a user specifically pins a historical view.

---

## 8. Page Specifications

### 8.1 Home

**Purpose:** Onboard a first-time visitor in 30 seconds; give a returning user a fast entry point.

**Layout (top to bottom):**
1. **Hero.** Logo, tagline, pitch paragraph, primary CTA: "Explore by entity."
2. **Global search box** (large, centered). Placeholder: *Search hospitals, counties, clinicians, ACOs, drugs, conditions…*
3. **Entity quick-pick.** Tile grid: Hospitals · SNFs · HHAs · Clinicians · ACOs · Counties · Drugs · Conditions · DRGs. Each tile goes to the respective Explore browser.
4. **Data freshness panel.** *"Current data vintages: 2026-Q1 for hospital quality, 2024 for physician utilization, 2022 for cost reports. Last site refresh: 2026-03-15."* With a link to the full vintage table in the Methodology Hub.
5. **Source transparency.** One line linking to the GitHub repository, where the full commit history serves as the de facto change log.
6. **Footer.** License, GitHub link, suggested citation, "Report an error" (GitHub Issue), contact.

### 8.2 Global Search

**Purpose:** Jump to any entity by name or identifier.

**Behavior:**
- Client-side index served as a precomputed JSON blob, lazy-loaded on first focus.
- Type-ahead results grouped by entity type: *"Hospitals (3), Clinicians (15), Counties (1)."*
- Accepts CCN, NPI, ACO ID, FIPS, ZIP, drug name, condition name, DRG code, and plain-English entity names.
- Each result shows a disambiguator ("Cleveland Clinic — Main Campus, Cleveland, OH").
- Enter → full results page at `/search?q=…`.

### 8.3 Entity Browser ("Explore" pages)

**Purpose:** Let users filter, sort, and rank the full population of an entity type.

**Layout:**
- **Header.** Entity type, count ("5,012 hospitals"), Explore/Table mode toggle, "Download filtered CSV," "Pin cohort to Workspace."
- **Filter rail (left).** State, region, ownership type, bed size range, ACO affiliation, quality tier, chronic condition specialty, demographics served. Filters vary per entity type.
- **Main (Explore mode).** Ranked leaderboard with scorecards: star rating, MSPB ratio, readmission ratio, HCAHPS, etc. Each row clickable to canonical page.
- **Main (Table mode).** Data grid with all columns visible, column visibility controls, sortable headers, client-side group-by, row count, per-column methodology popovers, and "Export CSV" / "Export parquet" respecting the current filters, sort, and groupings. Implemented with a lightweight client-side grid component; no SQL engine in v1.
- **Map toggle.** Pin all filtered entities on a map when geocoded.

**Trust affordances:** Each sortable column header has an info icon exposing the source dataset, column definition, vintage, and suppression policy.

### 8.4 Canonical Entity Page — generic template

This template applies to every entity type, with small variations (Section 8.5).

**Header strip**
- Entity-type badge · Name · Canonical ID (copy button) · City/State · Small locator map
- Action row: ⭐ Pin to Workspace · 📥 Download page bundle · 🔗 Copy permalink · Mode toggle

**Year selector** (adjacent to header strip)
- When datasets span multiple vintages (e.g., HVBP FY24/FY25/FY26, Physician Utilization 2013–2023), the page offers a **year toggle**. Default is the latest available vintage. Switching the year re-renders affected panels. Panels whose data exists for only one vintage show "single-year only" and do not change.
- The URL updates with the selected year parameter (e.g., `/hospital/123456?year=2024`), keeping the view shareable and bookmarkable.
- **ETL implication:** entity tables are indexed by year. The ETL produces one row per entity per available vintage for time-varying datasets. The page manifest includes all vintages; the frontend filters to the selected year at render time.

**Coverage card** (always visible near top)
- *"This page composes 7 datasets. 6 current to 2026-Q1; Cost Report current to 2022. 14 of 142 metric cells suppressed for small cell sizes. See Methodology →"*

**Overview panel**
- Identifying details from Provider Data (type, ownership, beds, membership, chain/system, addresses).

**Performance panels** (accordion; each collapsible and deep-linkable by anchor)
- **Quality** — star rating, VBP score, HRRP, HAC, HCAHPS, readmission ratios by condition. Explore: scorecards + sparklines. Query: row-level tables.
- **Financial** — MSPB ratio, Inpatient by DRG, Cost Report ratios, payer mix, margins.
- **Utilization** — volumes by service line, post-acute referral patterns, episode mix.
- **Workforce** — staffing (PBJ for SNFs), affiliated clinicians for hospitals.
- **Equity** — dual-eligible %, disability %, racial composition, Mapping Medicare Disparities outcomes.

**Related entities panel** — the interlinking payoff
- For a Hospital: affiliated clinicians (NPIs), downstream SNFs (from PAC utilization), parent county (with SDOH snapshot), ACO affiliations, DRG mix, MSPB episode breakdowns.
- Every related entity is a link to its canonical page.
- Every link carries a one-line context metric: *"→ Sunrise SNF — 24.1% rehosp rate, flagged."*

**Analysis entry points**
- *"Compare this hospital to peers →"* (opens Compare view pre-populated with the current entity and a suggested peer cohort).
- *"See this hospital on the map →"* (opens Map Explorer centered on its location, with relevant layers).

**Methodology footer**
- Expandable block: every dataset feeding this page, with vintage, row counts, suppression counts, caveats. Every line links to its Methodology Hub page.
- **"Report an error" link** — opens a prefilled GitHub Issue template naming the current entity and page section. This is the feedback loop for AI-generated methodology content (§11.1).

**Export row**
- *"Download everything on this page as a CSV bundle (zip)"* — every table used to render the page plus a `provenance.json`.
- *"Download this page's underlying parquet"* — the same data in columnar format for researchers who want to load it into their own tools (pandas, R, DuckDB CLI, etc.). Parquet files are build artifacts only; the browser itself never reads them in v1.

### 8.5 Per-entity variant notes

- **Hospital page** emphasizes episode decomposition (MSPB), DRG mix, affiliated clinicians, and downstream post-acute referrals.
- **SNF page** emphasizes PBJ staffing trends, deficiencies timeline, rehospitalization rates, ACO affiliates.
- **Clinician page** emphasizes MIPS scores, prescribing patterns, panel risk mix, facility affiliations, group membership.
- **ACO page** emphasizes savings/losses history, quality score trend, full participant roster (linked TINs and NPIs), beneficiary counts by county (each a link), track history.
- **County page** emphasizes SDOH overlays (SVI, PLACES, food access, AHRQ SDOH, County Health Rankings), chronic condition prevalence by demographic, attributed ACO beneficiaries, Market Saturation, Geographic Variation, lists of local hospitals/SNFs/clinicians.
- **Drug page** emphasizes national spending trends, top prescribing providers (linked NPIs), geographic prescribing patterns, Part B waste, generic/biosimilar alternatives.
- **Condition page** emphasizes prevalence maps, demographic disparities, spending per beneficiary, readmission and ED rates, related HCPCS and Part D classes.
- **DRG page** emphasizes payment distribution, volume by hospital, LOS, MSPB episode context.

### 8.6 Map Explorer

**Purpose:** A first-class geographic entry point. Many questions are intrinsically spatial and deserve a map-first view.

**Layout:**
- Full-screen choropleth map (Leaflet; raster tiles from a free provider like Stamen/CartoDB/OpenStreetMap).
- **Left rail** — layer picker hierarchically organized: Quality · Spending · Chronic Conditions · SDOH · Workforce · ACO Penetration.
- **Granularity toggle** — State ▸ HRR ▸ County ▸ ZCTA ▸ Census Tract. Layers expose only the granularities they support.
- **Multi-layer blend** — compose up to two layers (e.g., diabetes prevalence + SVI) with a bivariate palette.
- Click a region → side panel with a condensed entity snapshot and "Go to [County] page →" link.
- Export: CSV of the active layer, PNG screenshot, permalink carrying the full layer state.

**Trust affordances:** Every layer has an info popover — e.g., *"PLACES: census-tract modeled estimates based on BRFSS; not direct measurement."*

### 8.7 Compare View

**Purpose:** Put entities side by side. Core researcher use case and a power-user tool for executives ("compare our hospital to 5 peers").

**Layout:**
- Chips at top listing entities being compared (up to ~20). Add/remove via search.
- Metric selector (left) — a tree of metrics available for the entity type.
- Body — a wide table with entities as columns, metrics as rows, cells color-coded to flag best/worst.
- Alternate visualization — small-multiples trend chart panel.
- **Peer group builder** — *"Add all 50 hospitals in OH with 300–500 beds."* Saves as a cohort to Workspace.
- Export: CSV of the compare table; "Save comparison to Workspace."

### 8.8 Methodology Hub

**Purpose:** Operationalize "trust as a first-class feature." Methodology is a destination, not an appendix.

**Layout:**
- **Overview.** Philosophy statement, data quality principles, update cadence, how to cite.
- **Dataset Dictionary.** Filterable list of every source dataset. Each dataset has its own page:
  - Full provenance — URL, last downloaded, byte size, row count in, row count out.
  - Field dictionary — every column, type, definition, allowed values.
  - Join strategy — *"joined to Hospital via CCN; 14 rows discarded due to CCN format issues."*
  - Known limitations — *"CMS suppresses measure values where denominator < 11."*
  - Suppression statistics — counts and percentages for the current refresh.
  - Caveats and gotchas — SSA-to-FIPS issues, VBP scoring changes across years, MA/FFS differences, etc.
  - Source license and attribution.
- **Crosswalks.** Documentation for every crosswalk used (HUD ZIP-to-tract, NBER SSA-to-FIPS, NPPES, drug code normalization) with version info.
- **Lineage diagram.** A visual DAG of how source datasets flow into entity pages. Hoverable.
- **Limitations ledger.** A single curated page listing everything CareGraph does *not* tell you — e.g., *"Medicare Advantage encounter data is not included; all utilization reflects FFS only."* Written candidly. Updated every refresh.
- **Download everything.** Zipped parquet bundle of all precomputed tables plus the full provenance JSON, for researchers who want bulk access.

### 8.9 Workspace

**Purpose:** Personal pinboard with zero backend. All state in localStorage.

**Features:**
- **Pinned entities** — any entity can be pinned from its canonical page.
- **Saved cohorts** — peer groups built in Compare or Explore filters.
- **Notes** — free-text notes attached to pinned items.
- **Export workspace** — download the full workspace as a JSON blob; import on another device.
- **Persistence warning banner** — *"Your workspace lives in this browser only. Export regularly if you rely on it."*

### 8.10 About

- The embedded public pitch (Section 3).
- License info (MIT for code; per-source for data, with a table).
- Contributor credits.
- How to cite — suggested citation text plus BibTeX.
- Links to GitHub repo, issues, and discussions.
- Changelog linked from Methodology.

---

## 9. The Ten Analytical Use Cases (from the source brief)

The ten dataset combinations documented in `cms-dataset-combinations-for-vbc.md` are the organizing principle for **what cross-entity joins the v1 ETL precomputes**. They are not shippable pages in v1 — the guided "playbook" page concept is deferred to v2 (see §16). In v1, users reach each of these analyses by starting at the relevant entity page and following cross-links, or by using the Compare view.

Each use case listed below should be end-to-end reachable in v1 through entity navigation alone. If a user cannot answer the use case's question by clicking through entity pages and cross-links, the v1 ETL has a gap and should grow to fill it — *before* v2 adds guided narrative on top.

| # | Analytical use case | Starting entity | Entities traversed | How a user reaches it in v1 |
|---|---|---|---|---|
| 1 | Post-Acute Care Network Optimization | ACO or Hospital | SNF (bulk) → County → HHA | From the ACO/Hospital page, follow "downstream SNFs"; use Compare to rank them |
| 2 | Population Risk Stratification via SDOH | County or ACO | County → Tracts → Conditions | County page's SDOH and condition panels; drill to tracts |
| 3 | Physician Network Performance Profiling | ACO or Group | Clinicians (bulk) → DRG → Drug | ACO page's participant roster; Compare clinicians |
| 4 | Readmission Root-Cause Analysis | Hospital | Hospital → SNF → HHA → County | Hospital page's readmission panel + downstream-SNF links + County SDOH |
| 5 | ACO Competitive Benchmarking | ACO | Peer ACOs → Counties → Participants | ACO page's peer set; Compare ACOs across counties |
| 6 | Health Equity Gap Analysis | ACO or County | County → Tracts → Conditions | County page's equity panel with demographic breakdowns |
| 7 | Drug Spending Optimization | ACO or Clinician | Clinicians → Drugs → Geography | Clinician page's prescribing panel → Drug pages |
| 8 | Workforce Gap Analysis | County or ACO | County → Clinician supply | County page's workforce panel |
| 9 | Episode-Level Spending Decomposition | Hospital | Hospital → DRG → MSPB episode | Hospital page's MSPB panel with claim-type breakdown and DRG mix |
| 10 | Chronic Disease Burden Mapping | County or ACO | Conditions → Tracts → Food access | Condition page + County tract overlays (Map Explorer) |

These ten use cases are a **quality gate on ETL completeness**: every v1 release should be able to answer each of them via entity navigation, even though none of them has a dedicated guided page. v2 will add the guided playbook layer on top.

---

## 10. Cross-Linking Model

Cross-linking is generated at **ETL time**, not at render time. The ETL emits, for each entity, a **neighborhood manifest**: a list of related entities with relationship type and a contextual metric. Example:

```
hospital/330123
  ├── county/36061            [location, Manhattan NY]
  ├── aco/A1234               [participant, MSSP BASIC Track E]
  ├── clinicians/[NPIs…]      [via Facility Affiliations]
  ├── snfs/[top 10 downstream by discharge volume, via PAC Utilization]
  ├── drgs/[top 20 by volume]
  ├── conditions/[HF, AMI, pneumonia, COPD, THA/TKA — HRRP measures]
  └── mspb_episode/330123     [1:1]
```

**Rules:**

- **Every leaf value that names an entity is a link.** County names, DRG codes, drug names, condition names, clinician names, ACO names — always links. Validated by ETL.
- **Every related-entity link carries a one-line context metric** so the user can judge whether to click before committing.
- **Bi-directional when true.** If Hospital A lists SNF B as a downstream partner, SNF B's page lists Hospital A as an upstream referrer.
- **Link freshness matches underlying data vintage.** A link's context metric is stamped with the vintage it came from; stale links render with a subtle age indicator.

---

## 11. Trust and Methodology System

This is a *system*, not a set of pages. Implementation rules:

1. **Every data point is emitted from ETL inside a provenance envelope** carrying: dataset ID, column ID, vintage, granularity, suppression flag, sample size / denominator, confidence interval (if available), and quality tier.
2. **Frontend components render an info affordance next to any value.** Hover or click reveals the envelope inline.
3. **Page-level Coverage Cards** aggregate cell-level metadata into a page-scope summary.
4. **Methodology Hub deep-links.** Every info popover offers a "Full methodology →" link to the relevant dataset page.
5. **Known-limitations ledger.** A single curated page listing everything CareGraph consciously does not measure or measures with caveats. Written candidly. Updated with every refresh.
6. **Refusal to interpolate.** Where a dataset lacks coverage for an entity (e.g., a small SNF below CMS suppression thresholds), the UI shows "—" with an explanatory tooltip — never a default value, never a zero.
7. **Quality tier indicator.** Each metric gets a tier visible on hover:
   - **Direct** — direct measurement, complete coverage.
   - **Direct (partial)** — direct measurement with documented suppression.
   - **Modeled** — a modeled estimate (e.g., PLACES small-area estimation).
   - **Imputed** — reserved, not used in v1.
The goal is that a careful user should be able to build their own confidence — or skepticism — about any specific number on any specific page, without leaving CareGraph.

> **On the refresh changelog.** An earlier draft of this spec included a public, human-readable "refresh changelog" as rule 8 of this section and as a "What's new" panel on the Home page. That feature was dropped: the full codebase and its development history are on the project's GitHub repository, and the git log plus release tags already serve this purpose for anyone who cares enough to look. Maintaining a parallel hand-written or AI-generated changelog duplicated effort without adding signal.

### 11.1 Editorial pipeline (AI-assisted content generation)

Much of the written prose in CareGraph is not hand-authored. The **per-dataset methodology pages**, the **limitations ledger entries**, the **plain-English metric subtitles**, and the **coverage-card narrative text** are generated by an AI pipeline that runs as a dedicated stage of the build process, emitting versioned markdown/JSON into the repo before the frontend build consumes them.

**Why AI-assisted.** CareGraph has ~100 source datasets, each needing a methodology page with caveats, join notes, and suppression discussion. Thousands of metrics each need a plain-English subtitle. Hand-authoring all of this would take months on the first pass and rot on every subsequent data refresh. At the same time, this content is safety-critical: vague or incorrect methodology text would undermine the tool's entire trust premise. The pipeline is designed to make generation cheap *and* rigorous, with human review concentrated where it matters most.

**What IS AI-generated in v1**
- Per-dataset methodology pages — caveats, known limitations, join-strategy prose, field-level descriptions.
- Metric subtitles — the plain-English one-liners attached to every metric across the site.
- Limitations ledger entries — per-dataset and per-page honest-account paragraphs.
- Coverage-card narrative text — the sentence accompanying the structural coverage stats.

**What is NOT AI-generated**
- Numeric values of any kind — every number comes straight from the ETL's provenance envelopes.
- Source-dataset names, vintages, row counts, suppression counts — all structural facts flow through unchanged.
- Cross-link targets and their one-line context metrics — generated deterministically from neighborhood manifests.
- The About page, the public pitch in §3, and any high-stakes editorial decisions about site voice — these stay hand-authored.

**Pipeline mechanics.** The editorial stage is a standalone ETL step (§13.2, step 8.5) implemented in Python under `etl/editorial/`:

1. An orchestrator (`etl/editorial/run.py`) iterates every dataset and every metric that needs narrative content.
2. For each item, it constructs a **structured prompt** from the ETL's schema, suppression statistics, sample row counts, join-key validation results, and any dataset-specific **hints** from `etl/editorial/hints/` (maintainer-authored nuggets of domain knowledge that override or augment the generic template).
3. The orchestrator calls Claude via the Claude Code CLI (`claude -p`) with the templated prompt and captures the response. The maintainer runs a **Claude Max subscription**; the pipeline is designed to run in batches respecting the Max plan's throughput throttle. If a batch is throttled, the pipeline gracefully stops and can be resumed where it left off on the next invocation.
4. Output is written to versioned files under `etl/editorial/output/` — one file per dataset or metric — and committed to git.
5. A validation pass checks that each output parses as the expected shape (markdown frontmatter, required fields, length bounds, forbidden phrases like `"I cannot"` or `"As an AI"`), and hard-fails the build if it does not.
6. The frontend build consumes these files as inputs alongside the data manifests.

**Regeneration and determinism.** The pipeline is idempotent and re-runnable. Running it a second time on the same inputs may produce slightly different prose (LLM sampling), but the **structural contract** — required sections, required fields, length bounds, forbidden phrases — is enforced by validation. Prompts live under `etl/editorial/prompts/` and are versioned with the code, so every historical output can be traced to a specific prompt + input combination via git blame.

**Human review.** Every AI output is committed to git before it ships. A maintainer review pass is required before a release tag — line-by-line at first, spot-check as the pipeline matures. The `hints/` directory is the feedback loop: when a maintainer spots a wrong or missing caveat, they add a hint and re-run the pipeline, so corrections **compound** across refreshes instead of being forgotten.

**Trust gates inside the prompts.** Because an LLM could in principle invent caveats that do not exist, each prompt is engineered to:

- Quote source-dataset field names and definitions **verbatim** from the structured input, never paraphrased.
- Refuse to generate numeric claims — the validation pass strips any number that does not appear in the structured input envelope.
- Cite the specific column, metric, or join step being described.
- Flag uncertainty explicitly ("This dataset does not document X") rather than speculate.
- Stay under length bounds to discourage filler prose.

**The trade.** The pipeline buys coverage and freshness at the cost of a concentrated review burden on the maintainer. The alternative — hand-writing every methodology page and metric subtitle — would either ship years late or leave the trust-first goal unmet in a different way. The AI pipeline is a deliberate choice to front-load tooling effort so that content breadth scales with datasets, not with human-hours.

---

## 12. Export System

CSV is the default lingua franca. Rules:

- **Every chart, table, and scorecard has a "Download CSV" affordance.**
- **Every canonical page has a "Download page bundle"** — a zip of CSVs for every data component on the page plus a `provenance.json` describing vintages, sources, and suppression counts.
- **Explore (entity browser) pages** expose "Download filtered CSV," respecting active filters and sort.
- **Compare view** exports the full compare table.
- **Methodology Hub** exposes the full ETL parquet bundle for researchers who want bulk access.
- **Filename convention:** every export includes entity ID, metric scope, and data vintage — e.g., `hospital_330123_quality_2026Q1.csv`.
- **No watermarking, no row caps, no email gates.**

---

## 13. Technical Architecture

### 13.1 Overview

Two separate transport paths — **code via GitHub, built artifacts via direct rsync**. Built artifacts (5–15 GB of parquet + JSON + HTML) never touch GitHub.

```
                                 site/dist/ (5–15 GB)            [Low-cost VPS]
                           ┌──── rsync over SSH ─────────▶       Nginx serves
[Developer workstation]    │                                     /var/www/caregraph/current
  1. ETL → site_data/      │                                     (symlink; atomic swap)
  2. Astro build → dist/   │
  3. deploy.sh             │
                           │     source code (tens of MB)        [GitHub]
                           └──── git push ───────────────▶       MIT repo: ETL src,
                                                                 frontend src, docs,
                                                                 editorial prompts
```

The VPS runs *no* application server and *no* database. All interactivity is client-side; the browser renders precomputed JSON manifests through a lightweight data grid. In-browser SQL querying (DuckDB-WASM, `/lab` page, cross-parquet JOINs) is deferred to v2 — see §16. GitHub is exclusively the home of source code; the VPS is exclusively the home of built output. The two never cross.

### 13.2 Build-time (ETL)

- **Language.** Python for orchestration and acquisition; DuckDB for joins and aggregations; a thin glue layer for manifest emission.
- **Inputs.** data.cms.gov CSV/JSON downloads (all 100+ datasets from the source brief), **NPPES NPI Registry** (clinician names, credentials, specialties, addresses — required for any entity page that references a provider), CDC PLACES, CDC/ATSDR SVI, AHRQ SDOH, HRSA AHRF, USDA Food Atlas, Census ACS, County Health Rankings, HUD ZIP-to-tract crosswalk, NBER SSA-to-FIPS crosswalk.
- **Steps:**
  1. **Acquire** raw files into `data/raw/` (content-addressable; never overwritten; full history).
  2. **Normalize** join keys (CCN format, NPI format, SSA→FIPS, ZIP→tract, drug name canonicalization).
  3. **Validate** — row counts, null rates, suppression detection, schema drift alarms that hard-fail the build.
  4. **Build entity tables** — one parquet per entity type (`hospital.parquet`, `county.parquet`, …).
  5. **Build derived joins** — one parquet per analytical use case from §9 (e.g., hospital-to-downstream-SNF, ACO-to-participant, county-to-tract-SDOH).
  6. **Build page manifests** — one JSON per canonical page with all data needed to render.
  7. **Build neighborhood manifests** — the cross-link graph.
  8. **Build provenance envelopes** — metadata feeding every trust affordance.
  9. **Generate editorial content** — call the AI editorial pipeline (§11.1): for every dataset and every metric, construct a structured prompt from schema, suppression stats, and maintainer hints; invoke `claude -p`; validate and write outputs under `etl/editorial/output/`. Commit to git.
  10. **Build search index** — a single JSON blob for the global search type-ahead.
  11. **Emit site input** — `site_data/` directory with JSON manifests + parquet shards + editorial content, content-hashed for cache-busting.
- **Execution.** Manual, triggered by the maintainer. Expected runtime: tens of minutes to a few hours depending on refreshed inputs.
- **Output location.** `site_data/` on the workstation. Gitignored — never committed. Feeds directly into the frontend build (§13.3).

### 13.3 Frontend build (workstation)

After ETL completes, the frontend is built on the same workstation:

- **Input.** `site_data/` produced by ETL (§13.2).
- **Tooling.** Astro in static-site mode (`npm run build`) — produces a fully static `site/dist/` directory containing HTML pages, JSON manifests, parquet shards, search index, and all client-side assets.
- **Output.** `site/dist/` — typically 5–15 GB, dominated by parquet. Gitignored. Never committed.
- **Content-hashed assets.** Parquet files and large JSON manifests carry content-hash filenames so the VPS can cache them indefinitely and older versions can coexist with newer ones during atomic swaps.

`site/dist/` is the single artifact that ships to the VPS.

### 13.4 Deployment (workstation → VPS)

Built artifacts travel directly from the laptop to the VPS via `rsync` over SSH. **GitHub is not in this path.** This is the direct answer to the GitHub repo-size question: because GitHub's soft limit is ~1 GB and individual files cap at 100 MB, a 5–15 GB parquet bundle cannot live in git — not as a data branch, not as LFS, not as Releases. It travels via rsync instead, and reproducibility is preserved by the fact that anyone with the MIT-licensed source can re-run the ETL from data.cms.gov themselves.

**Layout on the VPS:**

```
/var/www/caregraph/
├── current → releases/20260411-153022/    # symlink Nginx serves from
└── releases/
    ├── 20260411-153022/                   # current release
    ├── 20260315-094511/                   # previous — kept for rollback
    └── 20260214-181207/                   # one before that
```

**Deploy procedure** (scripted in `deploy/deploy.sh`):

```bash
# Run on the workstation, after ETL + frontend build have completed.
TS=$(date +%Y%m%d-%H%M%S)
VPS=deploy@vps.example.com
RELEASE_DIR=/var/www/caregraph/releases/${TS}

# 1. Upload the new release to a timestamped directory.
#    --link-dest hardlinks unchanged content-hashed files from the live release,
#    so VPS disk usage stays close to one full release regardless of history.
rsync -av --delete \
  --link-dest=/var/www/caregraph/current/ \
  site/dist/ \
  ${VPS}:${RELEASE_DIR}/

# 2. Atomically swap the symlink. Nginx follows it on the next request.
ssh ${VPS} "ln -sfn ${RELEASE_DIR} /var/www/caregraph/current"

# 3. Prune old releases, keeping the last 3 for rollback.
ssh ${VPS} "cd /var/www/caregraph/releases && ls -1t | tail -n +4 | xargs -r rm -rf"
```

Because the symlink swap is atomic at the filesystem level and Nginx follows the symlink on each request, users never see a half-uploaded release. **Rollback** is a single `ln -sfn` on the VPS pointing `current` at any previous timestamped release.

**Nginx configuration** (abbreviated, lives at `deploy/nginx.conf`):

```nginx
server {
    listen 443 ssl http2;
    server_name caregraph.org;

    root /var/www/caregraph/current;
    index index.html;

    # Long-lived immutable cache for content-hashed assets.
    location ~* \.(parquet|json|js|css|woff2|png|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Short cache on the HTML shell.
    location / {
        expires 5m;
        try_files $uri $uri/ /index.html;
    }
}
```

**Transfer size.** The first deploy uploads the full 5–15 GB over SSH — plan for it. Subsequent deploys transfer only files whose content hash changed (typically a small fraction of the bundle); `rsync --link-dest` hardlinks the rest from the previous release, so VPS disk usage stays close to one release total.

**No CI involved.** Deploys are a local shell command run by the maintainer. A GitHub-Actions-based deploy path could be added later, but since the ETL needs substantial disk and compute, that path would require a self-hosted runner — not GitHub's free runners.

### 13.5 Run-time (browser)

- **Framework.** Astro in static-site mode (HTML-first performance, island architecture, good JSON interop). Confirmed.
- **Page data format.** JSON manifests, one per canonical page, with metrics, cross-links, and provenance envelopes inlined. Sized to be parsed in a single `fetch` — no paging, no streaming.
- **Charts.** ECharts or Observable Plot.
- **Maps.** Leaflet (zero API-key cost, raster tiles). Confirmed. Geography files served as TopoJSON/GeoJSON.
- **Data grid (Table mode).** A lightweight client-side grid component (TanStack Table or AG Grid Community are the top candidates) operating directly on the page's JSON manifest. Supports filter, sort, group-by, column visibility, and CSV export. No SQL engine in v1.
- **Search index.** Precomputed FlexSearch or lunr JSON blob, lazy-loaded on first search focus.
- **State.** URL parameters are canonical for shareable state. localStorage is used only for Workspace pins, mode toggle, and dismissed banners.
- **Accessibility.** WCAG 2.2 AA target. Keyboard navigation, screen reader support, high-contrast mode, no color-only encoding.
- **No DuckDB-WASM in v1.** Earlier drafts planned a DuckDB-WASM console for in-browser cross-parquet querying; deferred to v2 (§16). Parquet files are still produced by the ETL but serve **only** as downloadable artifacts for external tools — never consumed by the browser in v1. This removes ~5 MB of runtime from every page load and keeps the client tier simple.

### 13.6 Hosting

- **Provider.** Hetzner. Budget ceiling: **≤ $20/month** (a CX32 or equivalent — 4 vCPU / 8 GB / 80 GB SSD — fits easily within this budget and provides ample headroom for the static workload).
- **Domain.** `caregraph.org`, registered and owned by the maintainer. DNS managed at the registrar or Hetzner DNS.
- **Disk.** One full release is ~15 GB; with `rsync --link-dest` hardlinking unchanged content-hashed files, keeping 3 releases costs only marginal extra disk. 80 GB SSD leaves room for growth.
- **Caching.** Long-lived immutable cache on all content-hashed assets; short cache on the HTML shell (see Nginx config in §13.4).
- **Source of truth.** The GitHub repo is the source of truth for *code*. The workstation holds the source of truth for *built artifacts* — but because the ETL is fully reproducible from the MIT-licensed source plus data.cms.gov, the VPS is replaceable at any time by re-running ETL + deploy from any workstation with enough disk.
- **Logs.** Standard Nginx access logs only; privacy-by-default posture. No analytics beacons, no third-party scripts.
- **TLS.** Let's Encrypt via certbot, auto-renewed by the system's package cron.

### 13.7 Size envelope (rough)

- Parquet total: **5–15 GB** (dominated by Physician by Provider & Service and Part D Prescribers by Provider & Drug).
- JSON manifests: **200–500 MB**.
- HTML shell + critical CSS per page: **under 200 KB**.
- Parquet shards fetched lazily per page. Typical canonical page full load target: **under 2 s** on a mid-tier connection.
- VPS disk footprint with 3 hardlinked releases: **≈ 15–20 GB total**.

---

## 14. Repository Structure (proposed)

```
caregraph/
├── README.md
├── LICENSE                    # MIT
├── .gitignore                 # ignores data/raw, data/interim, site_data, site/dist
├── docs/
│   ├── spec.md                # this document
│   └── methodology/
├── etl/
│   ├── acquire/               # raw download scripts per source
│   ├── normalize/             # join-key and crosswalk logic
│   ├── build/                 # entity + page manifest builders
│   ├── validate/              # row counts, suppression, schema drift
│   ├── provenance/            # envelope construction
│   ├── editorial/             # AI editorial pipeline (see §11.1)
│   │   ├── prompts/           # versioned prompt templates
│   │   ├── hints/              # maintainer-authored domain knowledge
│   │   ├── output/             # generated methodology + subtitles (committed)
│   │   ├── validate.py         # shape, length bounds, forbidden phrases
│   │   └── run.py              # orchestrator; shells out to `claude -p`
│   └── run.py                 # top-level orchestrator
├── data/
│   ├── raw/                   # content-addressable downloads (gitignored)
│   └── interim/               # work artifacts (gitignored)
├── site_data/                 # ETL output, fed to frontend build (gitignored)
├── site/                      # frontend source (Astro)
│   ├── src/
│   ├── public/
│   ├── dist/                  # Astro build output, rsync'd to VPS (gitignored)
│   └── package.json
└── deploy/
    ├── deploy.sh              # rsync + atomic symlink swap (see §13.4)
    └── nginx.conf
```

**What lives in git:** everything except `data/raw/`, `data/interim/`, `site_data/`, and `site/dist/`. Total committed size stays in the tens of megabytes.

**What does not live in git:** every gigabyte-scale artifact. Raw downloads are re-fetchable from data.cms.gov; interim and built artifacts are re-buildable from the ETL. Anyone cloning the repo can rebuild the whole site from source.

---

## 15. Design Principles (editorial)

- **Plain speech over jargon.** Metric names always carry a plain-English subtitle. *"MSPB Ratio — Medicare Spending Per Beneficiary relative to the national median."*
- **Numbers have units.** No naked ratios.
- **Dates are explicit.** Always show the vintage next to the number.
- **Cells can be empty.** Missing data is rendered as "—" with a tooltip explaining why. Never show zeros as a stand-in.
- **Dense but calm.** Heavy information density is fine; visual noise is not. Default to muted palettes; reserve color for encoding.
- **Civic tone.** This is public data. The voice is neutral, specific, non-promotional.
- **No dark patterns.** No nag modals, no cookie banners we don't need, no email capture, no upsell.

---

## 16. Out-of-Scope for v1 (parking lot)

- **Guided playbook pages.** An earlier draft of this spec included 10 guided "playbook" pages — one per analytical use case from the source brief — each a stepped narrative that walked the user from a starting entity through downstream entities with interpretive commentary, a findings panel, and a one-page PDF export. **All of that is deferred to v2.** Rationale: playbook commentary has to be clinically and analytically credible, and the credible way to author it is not via AI generation (which v1 accepts for structural methodology content but considers too risky for decision-driving narrative). In v1, users reach every analytical use case by navigating the entity spine directly, as documented in §9. The v1 ETL still precomputes every cross-entity join each use case requires, so v2 can add the guided narrative layer on top without new data work.
- **Arbitrary user querying — DuckDB-WASM, SQL surface, `/lab` page.** An earlier draft of this spec included in-browser SQL across parquet files with three tiers — per-page console, entity-type-scoped queries, and cross-entity JOINs — plus a dedicated `/lab` page with a schema catalog sidebar and a persistent SQL editor. All of that is deferred to v2. **Rationale:** v1's priorities are accuracy, trust, correctness, and thoroughness within a bounded scope; arbitrary user querying is a large feature line whose UX (schema discovery, memory warnings, query construction, result handling) deserves its own design phase. It is also best built on top of an already-solid v1 data foundation — and the precomputed parquet files v1 produces are exactly the scaffolding a v2 query layer needs, so nothing blocks that future path.
- **LLM-powered natural-language query** — *"Show me SNFs in Ohio with readmission rates above peers."* A strong candidate for a future version once the entity model, precomputed parquet set, and v2 query layer are stable; the neighborhood manifests and provenance envelopes are good scaffolding for it.
- **User accounts and server-side personalization.**
- **Public programmatic API** beyond the downloadable parquet bundles.
- **Automated ETL scheduling** on the VPS or in cloud infra.
- **Non-English localization.**
- **Mobile-first design** (v1 is responsive but optimized for desktop).
- **Real-time data freshness.**
- **Medicare Advantage encounter data** (if/when it becomes public at this granularity).

---

## 17. Resolved Decisions (log)

These questions were raised during spec development and resolved. Recorded here so they don't resurface.

| # | Question | Decision |
|---|---|---|
| 1 | Name | **CareGraph** |
| 2 | Maintainer model | Solo maintainer |
| 3 | Hosting provider + budget | Hetzner, ≤ $20/mo |
| 4 | Domain | `caregraph.org` (maintainer-owned) |
| 5 | Frontend framework | Astro (static-site mode) |
| 6 | Map engine | Leaflet (raster tiles, zero API key cost) |
| 7 | Starting entity subset (first public release) | Hospitals + SNFs + Counties + ACOs |
| 8 | Data vintage strategy | Year toggle on entity pages (ETL ships all available vintages) |
| 9 | Non-source-brief datasets | NPPES pulled for clinician names/specialties/addresses |
| 10 | AI editorial provider | Claude Max subscription via `claude -p`, batched if throttled |
| 11 | Re-suppression policy | No re-suppression pass; CMS's own per-dataset suppression is sufficient |
| 12 | Error reporting UX | "Report an error" → GitHub Issue link in every page footer |
| 13 | Refresh changelog | Dropped; GitHub commit history + release tags serve this purpose |
| 14 | Artifact storage (git vs rsync) | Direct rsync to VPS; built artifacts never touch GitHub |
| 15 | DuckDB-WASM (in-browser SQL) | Deferred to v2; frontend consumes JSON only |
| 16 | Playbook pages | Deferred to v2; ten use cases drive ETL scope but have no dedicated pages in v1 |
| 17 | Geographic scope | National from day one |

---

## 18. Open Questions (remaining)

The following remain genuinely open:

1. **Parquet shard granularity.** Per-entity-type files (one `hospital.parquet` for all 5,000 hospitals) vs per-page JSON-only with parquet only as a download artifact? Needs a small benchmarking spike during M1 to see how large the per-entity JSON manifests actually get for the starting subset.
2. **Quality tier labels.** *Direct / Partial / Modeled* is the proposed vocabulary; to be confirmed via early user feedback.
3. **Suppression-warning loudness.** Default is loud; a one-click "hide low-confidence metrics" filter may be worth adding. Revisit during M5 polish.
4. **AI editorial review bar.** §11.1 describes a maintainer review pass before each release tag. Given solo maintenance, is line-by-line review sustainable past the first refresh, or does it need to degrade to spot-check + sampling? Answer depends on how stable the output quality turns out to be in practice.
5. **Cross-links to out-of-scope entity types.** The v1 starting subset is Hospitals + SNFs + Counties + ACOs. Hospital pages will reference clinicians (NPIs), drugs, DRGs, and conditions — entity types not yet fully built. Decision: render these as plain text with a tooltip ("Clinician pages coming in a future release") rather than broken links, and exempt pages from the ≥10-outbound-link gate until the referenced entity type is built.

---

## 18. Milestones (solo maintainer)

The v1 starting subset is **Hospitals + SNFs + Counties + ACOs** (4 entity types). These must be fully implemented before the first public release. Remaining entity types (Clinicians, HHAs, Hospices, Dialysis, Drugs, Conditions, DRGs, Groups, States, HRRs, CBSAs, Census Tracts, HCPCS, Episodes) are v1.x follow-on releases.

All timelines are solo-maintainer estimates, assuming roughly half-time sustained effort.

- **M1 — Skeleton (weeks 1–4).** Repo scaffolding, Astro project, ETL orchestration harness (`run.py` + `acquire/` + `normalize/` stubs), Hospital + County entity pages end-to-end with one dataset each. Methodology Hub shell. Deployable static site with two real pages on a Hetzner staging VPS. Confirm domain `caregraph.org` is resolving.
- **M2 — Four-entity spine (weeks 5–10).** Hospitals, SNFs, Counties, and ACOs fully joined across all relevant source-brief datasets plus NPPES. Year toggle working. Cross-links between these four entity types. Global search index covering these 4 types. Explore browsers with Table mode. All use cases in §9 that are answerable within these 4 entities are reachable via navigation.
- **M3 — Editorial pipeline (weeks 11–13).** AI editorial pipeline built and wired into ETL step 9: prompts under `etl/editorial/prompts/`, hint stubs, validation pass, `claude -p` orchestration with Max-plan batching/resume logic. Methodology Hub populated for every dataset feeding the 4 starting entities. First full maintainer review pass. GitHub Issue "Report an error" template created.
- **M4 — Maps + Compare + Workspace (weeks 14–16).** Map Explorer (Leaflet + county/state choropleth layers), Compare view (Hospitals vs Hospitals, SNFs vs SNFs, Counties vs Counties, ACOs vs ACOs), localStorage Workspace.
- **M5 — Polish and public launch (weeks 17–19).** Accessibility audit (axe/Lighthouse, target WCAG 2.2 AA), performance budget (< 200 KB initial load, < 2 s entity page), public pitch site copy, GitHub README, first full data refresh, soft launch at `caregraph.org`.

**First public release acceptance criteria:**
- Hospitals, SNFs, Counties, and ACOs are fully implemented: all panels populated, cross-links working, year toggle functional, methodology pages reviewed, exports producing valid CSVs.
- ≥95% of entities in these 4 types render a page (the remainder are documented as "insufficient source data").
- Every AI-generated methodology page has been reviewed at least once by the maintainer.
- Lighthouse accessibility score ≥ 90 on sample entity pages.
- Deploy pipeline tested end-to-end: ETL → Astro build → rsync → atomic swap → live at `caregraph.org`.

---

*End of spec.*
