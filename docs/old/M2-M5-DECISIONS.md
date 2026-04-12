# M2-M5 Build Decisions

**Date range:** April 2026
**Covers:** Milestones 2 through 5 (Entity enrichment, Methodology Hub, Interactive views, About + Polish)

---

## M2: Entity Enrichment and Cross-Links

### CMS API changes (SODA retirement)

The legacy SODA API (`https://data.cms.gov/resource/{id}.csv`) returns 410 Gone for all datasets. All ETL downloads now use one of:

- **Direct CSV bulk download URLs** (preferred, most stable)
- **Provider Data API**: `https://data.cms.gov/provider-data/api/1/datastore/query/{id}/0`
- **CMS Data API**: `https://data.cms.gov/data-api/v1/dataset/{uuid}/data`

### Dataset IDs and URLs used

| Dataset | Local ID | UUID / SODA ID | Source |
|---|---|---|---|
| Hospital General Information | `xubh-q36u` | — | Provider Data API / CSV |
| Hospital Readmissions Reduction Program | `9n3s-kdb3` | — | Provider Data API / CSV |
| Hospital Value-Based Purchasing | `ypbt-haku` | — | Provider Data API / CSV |
| Medicare Geographic Variation (county) | `geo-var-county` | `6219697b-8f6c-4164-bed4-cd9317c58ebc` | CMS Data API / CSV |
| SNF Quality Reporting | `4pq5-n9py` | — | Provider Data API / CSV |
| ACO Shared Savings Program | `aco-ssp` | — | CMS Data API / CSV |
| CDC PLACES (county) | `swc5-untb` | — | CDC / SODA-compatible API |

### CDC PLACES as chronic conditions source

The spec calls for county-level chronic condition prevalence. CDC PLACES provides model-based small-area estimates at the county level for 36+ health measures (diabetes, COPD, obesity, etc.). This was chosen because:

- It is the only freely available source of county-level chronic condition prevalence.
- The data aligns well with CMS county FIPS codes.
- Updated annually by CDC.

### County-to-FIPS mapping from county names

The Geographic Variation dataset uses `BENE_GEO_CD` for the numeric FIPS code and `BENE_GEO_DESC` in the format `"ST-County Name"` (e.g., `"CA-Los Angeles"`). The ETL parses state abbreviation and county name by splitting on the first hyphen.

Hospital and SNF datasets provide city and state but not FIPS codes. Cross-linking to counties uses a county name + state lookup table built from the Census Bureau's FIPS code list. This is imperfect (name variations, independent cities) but covers >99% of facilities.

### Cross-link strategy (FIPS-based hospital / county / SNF)

All cross-links between entity types use FIPS codes as the common join key:

- **Hospital to County**: Hospital ZIP code mapped to county FIPS via HUD ZIP-to-county crosswalk or county name + state matching.
- **SNF to County**: Same approach as hospitals.
- **County to Hospitals/SNFs**: Reverse of the above — county pages list all facilities in that FIPS.
- **Hospital to SNFs**: Shared county FIPS creates "in the same area" links.
- **ACO to Counties/Hospitals**: ACO performance data includes service area information.

Cross-links are stored as neighborhood manifests: each entity's JSON manifest includes a `related` array with `{type, id, label, context}` objects.

### Search index as precomputed JSON

Global search uses a precomputed JSON index (`search-index.json`) generated at ETL time containing all entity names, IDs, types, and a few key attributes. The browser loads this index on the search page and filters client-side. No server-side search is needed because:

- The index is ~500KB gzipped for ~15K entities.
- Client-side filtering is fast enough (< 50ms) for the entity count.
- Keeps the architecture fully static.

---

## M3: Methodology Hub and Editorial Pipeline

### Methodology Hub structure

The Methodology Hub lives at `/methodology/` with per-dataset detail pages at `/methodology/dataset/{slug}/`. Each dataset page includes:

- Dataset name, source agency, and vintage
- Download URL and access method
- Column definitions used by CareGraph
- Known limitations, suppression rules, and caveats
- Update cadence and freshness tracking

### Editorial pipeline with --skip-ai mode

The spec calls for Claude-generated editorial content (dataset summaries, limitation narratives, etc.) via an ETL editorial stage. The pipeline is implemented in `etl/editorial/` with:

- A `generate.py` script that reads manifest data and produces editorial JSON.
- A `--skip-ai` flag that produces placeholder editorial content without calling any AI API.
- Templates for each content type (dataset summary, limitation narrative, etc.).

For M3, all editorial content is generated in `--skip-ai` mode with placeholder text. Full AI-generated editorial content is pending a pipeline run with Claude Max API access.

### Placeholder editorial content

All methodology pages currently show placeholder editorial text marked with a visual indicator. The placeholders follow a consistent format and are structurally complete (correct headings, sections, links) — only the prose body is placeholder. This ensures:

- Pages are navigable and structurally testable.
- No broken links or missing sections.
- Easy to swap in real editorial content later.

---

## M4: Interactive Views (Map, Compare, Workspace)

### Leaflet + TopoJSON for maps

The choropleth map at `/map/` uses:

- **Leaflet** (v1.9) for the map rendering engine — lightweight, well-documented, no API key required.
- **TopoJSON** for county boundary data — ~800KB for all US counties, much smaller than GeoJSON.
- A precomputed `county-summaries.json` with one row per FIPS containing key metrics for choropleth coloring.

Alternatives considered and rejected:
- **Mapbox GL JS**: Requires API key, heavier, overkill for static choropleths.
- **D3 alone**: More code for less functionality; Leaflet provides zoom/pan/tiles for free.

### Compare view with summary JSON (not full manifests)

The Compare page (`/compare/`) loads a precomputed `compare-summaries.json` file containing a compact representation of each entity (name, ID, type, and 5-8 key metrics). This is much smaller than loading full entity manifests. The compare UI:

- Accepts up to 5 entities of the same type.
- Renders a side-by-side table of key metrics.
- Highlights best/worst values in each row.
- Entities are selected from a search interface on the page.

### Workspace in localStorage

The Workspace page (`/workspace/`) persists user-pinned entities and notes in `localStorage` under the key `caregraph-workspace`. Design decisions:

- **No server-side storage**: Keeps the architecture static and avoids auth.
- **JSON structure**: `{items: [{type, id, label, addedAt, notes}], version: 1}`.
- **Export/import**: Users can download the workspace as a JSON file and re-import on another browser.
- **Persistence warning**: A banner reminds users that data is browser-local.
- **Size limit**: localStorage is typically 5-10MB; workspace data is trivially small.

---

## M5: About Page, Accessibility, and Polish

### About page content

The About page at `/about/` contains:

1. The verbatim public pitch from spec section 3 (as a blockquote).
2. License table: MIT for code, per-source licenses for data (all federal sources are public domain).
3. Citation text and BibTeX entry.
4. GitHub repository link.
5. Error reporting link to GitHub Issues.

### Accessibility improvements

- **Skip-to-content link**: First element in `<body>`, visually hidden, visible on keyboard focus.
- **ARIA landmarks**: `role="navigation"`, `role="search"`, `role="main"`, `role="contentinfo"` on nav, search, main, footer.
- **Focus-visible styles**: All interactive elements (links, buttons, inputs) get a visible `2px solid` outline on keyboard focus via `:focus-visible`.
- **Search input**: `aria-label="Search CareGraph"` for screen readers.

### Nav link cleanup

All nav links now point to real pages. The "About" link changed from `#` to `/about/`. "Explore" remains `#` as a placeholder for the browse dropdown (future enhancement).

### Comprehensive Playwright tests

Smoke tests expanded to cover M3-M5:

- **M3**: Methodology hub loads, per-dataset page loads, required sections present.
- **M4**: Map page loads with Leaflet container, Compare page loads, Workspace loads with empty state.
- **M5**: About page content (pitch, citation, license, GitHub link, error reporting), skip-to-content link, ARIA attributes, nav links validation.

---

## Cross-cutting decisions

### GitHub repository URL

The canonical repository URL used throughout the site is `https://github.com/fabkury/caregraph`. The footer "Report an error" link points to the Issues page of this repository.

### Static-only architecture confirmed

All five milestones maintain the fully-static architecture. No server-side logic, no database, no API keys, no authentication. The VPS serves only static files behind nginx.

### Entity count at M5 completion

- ~5,400 hospital pages
- ~3,200 county pages
- ~15,000 SNF pages
- ~500 ACO pages
- ~6 methodology dataset pages
- Plus: home, search, map, compare, workspace, about = ~24,100+ total pages
