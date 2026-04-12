"""
Editorial pipeline orchestrator.

Generates AI-assisted methodology pages for each CMS/CDC dataset
used in CareGraph. Reads prompt templates, substitutes dataset metadata
and domain-specific hints, then calls `claude -p` to generate content.

Usage:
    python etl/editorial/run.py              # Run with Claude AI
    python etl/editorial/run.py --skip-ai    # Generate placeholder content (no AI)
    python etl/editorial/run.py --force      # Regenerate all (ignore checkpoint)

The orchestrator:
  1. Iterates datasets from etl/acquire/download.py
  2. Reads the prompt template, substitutes variables
  3. Calls `claude -p` (or generates placeholders with --skip-ai)
  4. Validates output against required section/length/phrase rules
  5. Tracks progress in a checkpoint file for resume support
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# Ensure repo root is on the path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from etl.acquire.download import DATASETS
from etl.editorial.validate import validate_methodology

EDITORIAL_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = EDITORIAL_DIR / "prompts"
HINTS_DIR = EDITORIAL_DIR / "hints"
OUTPUT_DIR = EDITORIAL_DIR / "output"
CHECKPOINT_FILE = EDITORIAL_DIR / ".checkpoint.json"

# Dataset metadata for prompt substitution — fields not in DATASETS dict
DATASET_META: dict[str, dict] = {
    "xubh-q36u": {
        "join_key": "CCN (CMS Certification Number)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~30",
        "suppression_notes": (
            "Hospitals with insufficient data for star ratings show "
            "'Not Available'. No cell-size suppression is applied to "
            "this dataset since it contains facility-level attributes, "
            "not patient-level counts."
        ),
    },
    "hrrp": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~12 per measure-hospital row",
        "suppression_notes": (
            "Hospitals with fewer than 25 eligible discharges for a "
            "condition show 'Too Few to Report'. ERR values are suppressed "
            "for these rows. Approximately 20-30% of measure-hospital "
            "combinations are suppressed for small volume."
        ),
    },
    "hvbp-tps": {
        "join_key": "Provider Number (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10",
        "suppression_notes": (
            "Hospitals not participating in HVBP (CAHs, Maryland waiver, "
            "insufficient measures) are excluded entirely. Domain scores "
            "may be blank when the hospital lacks enough measures in that "
            "domain. Approximately 15-20% of IPPS hospitals lack a TPS."
        ),
    },
    "nh-provider-info": {
        "join_key": "Federal Provider Number (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~90",
        "suppression_notes": (
            "Star ratings show 'Not Available' for facilities with "
            "insufficient inspection history or during the grace period "
            "after a change of ownership. Some fields (e.g., abuse icon, "
            "SFF status) are binary flags that may be blank rather than "
            "explicitly 'N'."
        ),
    },
    "nh-quality-mds": {
        "join_key": "Federal Provider Number (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~20 per measure-facility row",
        "suppression_notes": (
            "Facilities with fewer than 20 eligible residents for a "
            "measure are suppressed. Small rural nursing homes are "
            "disproportionately affected. Suppressed values appear as "
            "blank/null rather than zero."
        ),
    },
    "mssp-performance": {
        "join_key": "ACO_ID",
        "join_key_type": "Character string (e.g., A0001)",
        "field_count": "~80",
        "suppression_notes": (
            "ACOs with fewer than 11 beneficiaries in sub-categories "
            "have those values suppressed per CMS cell-size rules. "
            "Financial metrics for ACOs that terminated mid-year are "
            "annualized and may not be comparable to full-year ACOs."
        ),
    },
    "geo-var-county": {
        "join_key": "FIPS county code",
        "join_key_type": "5-digit string (state FIPS + county FIPS), zero-padded",
        "field_count": "~100",
        "suppression_notes": (
            "Counties with fewer than 11 beneficiaries in a spending "
            "category are suppressed (shown as '*' or blank). This "
            "primarily affects small rural counties and specialized "
            "service categories like hospice. Approximately 5% of "
            "county-metric combinations are suppressed."
        ),
    },
    "cdc-places": {
        "join_key": "CountyFIPS",
        "join_key_type": "5-digit string (state FIPS + county FIPS)",
        "field_count": "~10 per measure-county row (pivoted to ~40 measures per county)",
        "suppression_notes": (
            "PLACES does not suppress individual county estimates, but "
            "confidence intervals widen substantially for small-population "
            "counties where the model has less survey data to anchor "
            "estimates. Counties with very wide CIs should be interpreted "
            "with caution."
        ),
    },
}


def load_prompt_template() -> str:
    """Load the dataset methodology prompt template."""
    template_path = PROMPTS_DIR / "dataset_methodology.txt"
    return template_path.read_text(encoding="utf-8")


def load_hints(dataset_id: str) -> str:
    """Load domain-specific hints for a dataset. Returns empty string if none."""
    hints_path = HINTS_DIR / f"{dataset_id}.md"
    if hints_path.exists():
        return hints_path.read_text(encoding="utf-8").strip()
    return "(No dataset-specific hints available.)"


def load_index_stats() -> dict:
    """Load ETL output stats from site_data/index.json."""
    index_path = REPO_ROOT / "site_data" / "index.json"
    if index_path.exists():
        with open(index_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_row_count(dataset_id: str, index_data: dict) -> str:
    """Extract row count from index.json for a dataset."""
    entities = index_data.get("entities", {})
    for entity_info in entities.values():
        if entity_info.get("dataset_id") == dataset_id:
            count = entity_info.get("count", "unknown")
            return f"{count:,}" if isinstance(count, int) else str(count)
    return "unknown"


def build_prompt(dataset_id: str, template: str, index_data: dict) -> str:
    """Build the full prompt for a dataset by substituting variables."""
    ds = DATASETS[dataset_id]
    meta = DATASET_META.get(dataset_id, {})
    hints = load_hints(dataset_id)
    row_count = get_row_count(dataset_id, index_data)

    prompt = template.format(
        dataset_name=ds["name"],
        dataset_id=dataset_id,
        entity_type=ds["entity"],
        field_count=meta.get("field_count", "unknown"),
        row_count=row_count,
        join_key=meta.get("join_key", "unknown"),
        join_key_type=meta.get("join_key_type", "unknown"),
        suppression_notes=meta.get("suppression_notes", "No specific suppression notes."),
        hints=hints,
    )
    return prompt


def generate_placeholder(dataset_id: str) -> str:
    """Generate reasonable placeholder methodology content for --skip-ai mode."""
    ds = DATASETS[dataset_id]
    meta = DATASET_META.get(dataset_id, {})
    name = ds["name"]
    entity = ds["entity"]
    join_key = meta.get("join_key", "provider ID")
    join_key_type = meta.get("join_key_type", "string")
    hints = load_hints(dataset_id)

    # Parse hint bullets for use in limitations
    hint_bullets = []
    for line in hints.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            hint_bullets.append(line)

    limitations = hint_bullets[:4] if hint_bullets else [
        "- Small-volume providers may have suppressed or missing values.",
        "- Data reflects a reporting lag of 6-18 months from the measurement period.",
        "- Medicare Advantage beneficiaries are excluded from fee-for-service metrics.",
    ]

    return f"""## Overview

The {name} dataset is published by the Centers for Medicare & Medicaid Services (CMS) as part of the public-use data files available on data.cms.gov. This dataset contains {entity}-level records used to build {entity} entity pages on CareGraph. It provides key attributes, quality metrics, and operational data for each {entity} entity, enabling comparisons across providers and geographies.

The data is updated periodically by CMS and reflects the most recently available reporting period. CareGraph ingests this dataset during its ETL pipeline and joins it to {entity} entity pages using the {join_key} as the primary key.

## Join Strategy

This dataset is joined to {entity} entity pages using the {join_key} field, which is formatted as a {join_key_type}. During ETL, each row in the source dataset is matched to a {entity} entity page by this key. Records that do not match an existing entity page are logged but not displayed. The join is performed as a left join from the entity manifest to the dataset, so entity pages without matching records in this dataset will show missing data indicators rather than being excluded.

Normalization steps include stripping leading/trailing whitespace from the join key and zero-padding where necessary to ensure consistent matching. The join key format is validated during the ETL build step, and mismatches are reported in the build log.

## Known Limitations

{chr(10).join(limitations)}

## Data Quality Notes

- Some numeric fields in the source CSV are encoded as strings (e.g., with commas or dollar signs) and are parsed to numeric types during ETL. Values that fail parsing are set to null.
- Missing values in the source data appear as empty strings, "Not Available", or "N/A" depending on the field. The ETL normalizes all of these to null in the JSON manifest.
- Field names are normalized to snake_case during ETL processing. The original field names from the CMS CSV are preserved in the raw data section of each entity page.
- Date fields in the source data use varying formats (MM/DD/YYYY, YYYY-MM-DD) and are standardized to ISO 8601 (YYYY-MM-DD) during processing.
"""


def load_checkpoint() -> dict:
    """Load checkpoint file tracking which datasets have been processed."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_checkpoint(checkpoint: dict) -> None:
    """Save checkpoint file."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def call_claude(prompt: str) -> str:
    """Call claude -p with the given prompt and return the response."""
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (exit {result.returncode}): {result.stderr}"
        )
    return result.stdout.strip()


def run_editorial(
    skip_ai: bool = False,
    force: bool = False,
) -> dict[str, str]:
    """Run the editorial pipeline.

    Returns a dict of {dataset_id: status} where status is
    'generated', 'skipped', or 'failed: <reason>'.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    template = load_prompt_template()
    index_data = load_index_stats()
    checkpoint = {} if force else load_checkpoint()
    results: dict[str, str] = {}

    print("=" * 60)
    print(f"Editorial Pipeline ({'--skip-ai placeholder mode' if skip_ai else 'AI mode'})")
    print("=" * 60)

    for dataset_id, ds in DATASETS.items():
        output_path = OUTPUT_DIR / f"{dataset_id}.md"

        # Check checkpoint — skip if already successfully processed
        if dataset_id in checkpoint and checkpoint[dataset_id] == "ok":
            if output_path.exists():
                print(f"  [skip] {ds['name']} (checkpoint: already done)")
                results[dataset_id] = "skipped"
                continue

        print(f"  [gen]  {ds['name']} ({dataset_id})")

        try:
            if skip_ai:
                content = generate_placeholder(dataset_id)
            else:
                prompt = build_prompt(dataset_id, template, index_data)
                content = call_claude(prompt)

            # Write output
            output_path.write_text(content.strip() + "\n", encoding="utf-8")

            # Validate
            ok, errors = validate_methodology(output_path)
            if ok:
                print(f"         -> {output_path.name} [VALID]")
                checkpoint[dataset_id] = "ok"
                results[dataset_id] = "generated"
            else:
                print(f"         -> {output_path.name} [VALIDATION FAILED]")
                for e in errors:
                    print(f"            - {e}")
                checkpoint[dataset_id] = "validation-failed"
                results[dataset_id] = f"failed: validation ({'; '.join(errors)})"

        except Exception as e:
            print(f"         -> FAILED: {e}")
            checkpoint[dataset_id] = "error"
            results[dataset_id] = f"failed: {e}"

        save_checkpoint(checkpoint)

    # Print summary
    generated = sum(1 for v in results.values() if v == "generated")
    skipped = sum(1 for v in results.values() if v == "skipped")
    failed = sum(1 for v in results.values() if v.startswith("failed"))

    print()
    print("-" * 60)
    print(f"Summary: {generated} generated, {skipped} skipped, {failed} failed")
    print(f"Output:  {OUTPUT_DIR}")
    print("-" * 60)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CareGraph editorial pipeline — generate methodology pages"
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Generate placeholder content without calling Claude",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate all datasets (ignore checkpoint)",
    )
    args = parser.parse_args()

    results = run_editorial(skip_ai=args.skip_ai, force=args.force)

    # Exit with error if any failed
    if any(v.startswith("failed") for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
