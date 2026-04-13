# Methodology Page Completion — Remaining Work

**Date:** 2026-04-13
**Context:** The Methodology hub was updated to list all 30 datasets (grouped by entity type with role badges), but the editorial pipeline was only partially run. 16 of 30 datasets now have full methodology detail pages. 14 remain.

## What was completed

### Infrastructure (fully done)
- **`etl/editorial/run.py`** — `DATASET_META` entries added for all 30 datasets (join keys, field counts, suppression notes)
- **`etl/editorial/hints/*.md`** — Hint files written for all 30 datasets (3–6 domain-expert bullets each)
- **`site/src/lib/dataset-registry.ts`** — Shared TypeScript registry with all 30 datasets (name, entity, vintage, role, source)
- **`site/src/pages/methodology/index.astro`** — Redesigned hub with 7 entity-type sections, role badges (base/enrichment/cross-link), source agency
- **`site/src/pages/methodology/dataset/[id].astro`** — Updated to import shared registry, adds Role and Source to provenance card

### Editorial content (16 of 30 done)
Generated via `python etl/editorial/run.py` (uses `claude -p`):

| Dataset ID | Entity | Status |
|---|---|---|
| xubh-q36u | hospital | Done |
| hrrp | hospital | Done |
| hvbp-tps | hospital | Done |
| hosp-timely-care | hospital | Done |
| hosp-complications | hospital | Done |
| hosp-hcahps | hospital | Done |
| hosp-hai | hospital | Done |
| hosp-unplanned-visits | hospital | Done |
| hosp-mspb | hospital | Done |
| nh-provider-info | snf | Done |
| nh-quality-mds | snf | Done |
| nh-deficiencies | snf | Done |
| nh-ownership | snf | Done |
| mssp-performance | aco | Done |
| geo-var-county | county | Done |
| cdc-places | county | Done |

## What remains (14 datasets)

| Dataset ID | Entity | Checkpoint Status |
|---|---|---|
| hosp-cost-report | hospital | Not started |
| hac-reduction | hospital | Not started |
| nh-penalties | snf | Error (retry needed) |
| snf-cost-report | snf | Not started |
| aco-participants | aco | Not started |
| aco-snf-affiliates | aco | Not started |
| aco-bene-county | aco | Not started |
| partd-drug-spending | drug | Not started |
| partb-drug-spending | drug | Not started |
| partb-discarded-units | drug | Not started |
| nadac | drug | Not started |
| inpatient-by-drg | drg | Not started |
| cdc-sdoh | county | Not started |
| cms-chronic-conditions | county | Not started |

## How to resume

The editorial pipeline supports checkpoint-based resumption. It will skip datasets already marked "ok" and retry those marked "error":

```bash
# From repo root — generates remaining methodology pages via claude -p
python etl/editorial/run.py

# Copy output to site_data (or run full ETL which does this automatically)
cp etl/editorial/output/*.md site_data/editorial/

# Rebuild the site
cd site && npm run build
```

The `nh-penalties` dataset errored on the first run. The pipeline will automatically retry it on the next run. If it fails again, check `etl/editorial/.checkpoint.json` and investigate the error.

To force regeneration of all datasets (including those already done):
```bash
python etl/editorial/run.py --force
```

To generate placeholder content without AI (for testing layout):
```bash
python etl/editorial/run.py --skip-ai
```

## After completion

Once all 30 methodology pages are generated:
1. All 30 "Pending" → "View details" links on the Methodology hub will be active
2. Spot-check a sample of generated pages for factual accuracy
3. Rebuild and redeploy the site

## Optional follow-up (Step 6 from original plan)

Update `site_data/index.json` enrichment tracking: currently `enriched_with` arrays in the ETL output don't list all enrichment datasets, so some methodology detail pages show "—" for row counts. This requires changes to the ETL build scripts (`etl/build/`), not the Methodology page itself.
