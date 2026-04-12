# Editorial Pipeline (AI-Assisted Content Generation)

This directory will contain the AI editorial pipeline described in spec §11.1.

## What goes here (future milestones)

- **`prompts/`** — Versioned prompt templates for generating methodology content, metric subtitles, limitations entries, and coverage-card narrative text.
- **`hints/`** — Maintainer-authored domain knowledge nuggets that override or augment the generic prompt templates. This is the feedback loop: when a maintainer spots a wrong or missing caveat, they add a hint here and re-run the pipeline.
- **`output/`** — Generated methodology pages and metric subtitles (committed to git). One file per dataset or metric.
- **`validate.py`** — Validates AI output: shape checks, length bounds, forbidden phrases (`"I cannot"`, `"As an AI"`), required sections.
- **`run.py`** — Orchestrator that iterates datasets/metrics, constructs structured prompts from ETL schema + suppression stats + hints, calls `claude -p`, and writes validated output.

## Pipeline mechanics

1. Orchestrator iterates every dataset and metric needing narrative content.
2. Constructs structured prompts from ETL schema, suppression statistics, sample row counts, join-key validation results, and any hints.
3. Calls Claude via `claude -p` (Claude Max subscription, batched if throttled).
4. Output written to `output/`, committed to git.
5. Validation pass checks shape, length, forbidden phrases.
6. Frontend build consumes these files alongside data manifests.

## Not implemented in M1

This is a stub. The editorial pipeline will be built in M3 (weeks 11-13).
