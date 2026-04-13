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
    # ── Phase 1 hospital enrichment datasets ──────────────────────
    "hosp-timely-care": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~15 per measure-hospital row",
        "suppression_notes": (
            "Hospitals with fewer than 25 cases for a measure show 'Not "
            "Available' or footnote codes. ED throughput measures (OP-18, "
            "OP-22) exclude critical access hospitals and hospitals without "
            "an ED. Some measures have been removed or retired across CMS "
            "reporting cycles, creating gaps in time-series comparisons."
        ),
    },
    "hosp-complications": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10 per measure-hospital row",
        "suppression_notes": (
            "Hospitals with fewer than 25 cases in the denominator have "
            "mortality and complication rates suppressed ('Too Few to "
            "Report'). Risk adjustment uses CMS hierarchical logistic "
            "regression but does not adjust for socioeconomic status. "
            "Rates reflect a 3-year measurement window lagging 12-24 months."
        ),
    },
    "hosp-hcahps": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~60 (multiple survey dimensions with top/middle/bottom box scores)",
        "suppression_notes": (
            "Hospitals with fewer than 100 completed surveys are suppressed. "
            "Survey response rates vary widely (15-40%) and lower rates may "
            "introduce non-response bias. Results are adjusted for patient "
            "mix (age, education, self-rated health, language) but not for "
            "hospital characteristics like size or teaching status."
        ),
    },
    "hosp-hai": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10 per measure-hospital row",
        "suppression_notes": (
            "Hospitals with fewer than 1 predicted infection for a given "
            "measure are suppressed. Data comes from the CDC National "
            "Healthcare Safety Network (NHSN), not CMS claims. SIR "
            "(Standardized Infection Ratio) values are risk-adjusted for "
            "facility characteristics but suppressed measures may indicate "
            "low surgical volume rather than data quality issues."
        ),
    },
    "hosp-unplanned-visits": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10 per measure-hospital row",
        "suppression_notes": (
            "Hospitals with fewer than 25 cases for a measure are "
            "suppressed. Measures include ED visits after outpatient "
            "procedures and unplanned readmissions. Observation stays "
            "may not be captured as 'visits' depending on billing codes, "
            "which can undercount true return rates."
        ),
    },
    "hosp-mspb": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~8 per measure-hospital row",
        "suppression_notes": (
            "Hospitals with fewer than 25 eligible episodes are suppressed. "
            "MSPB is price-standardized to remove geographic wage differences "
            "but does not adjust for case mix beyond the DRG assignment. "
            "Spending includes 3 days pre-admission through 30 days "
            "post-discharge, which captures post-acute care costs."
        ),
    },
    "hosp-cost-report": {
        "join_key": "Provider CCN",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~300+ (financial line items from HCRIS worksheets)",
        "suppression_notes": (
            "Cost reports are self-reported by hospitals and subject to "
            "audit but not systematically verified. Fiscal years vary by "
            "hospital (not all end in December), complicating cross-hospital "
            "comparisons. Approximately 5-10% of hospitals file late or "
            "submit amended reports that may not be reflected in the current "
            "file. Critical access hospitals and some specialty hospitals "
            "use different cost report forms."
        ),
    },
    "hac-reduction": {
        "join_key": "Facility ID (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10",
        "suppression_notes": (
            "The HAC Reduction Program penalizes hospitals in the worst-"
            "performing quartile with a 1% payment reduction. Only IPPS "
            "hospitals are subject to penalties; critical access hospitals "
            "and Maryland waiver hospitals are excluded. The Total HAC Score "
            "is a weighted composite of CMS PSI-90 and CDC NHSN HAI measures. "
            "Hospitals with insufficient measure data may lack a composite score."
        ),
    },
    # ── Phase 2 SNF enrichment datasets ─────────────────────────
    "nh-penalties": {
        "join_key": "Federal Provider Number (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10 per penalty record",
        "suppression_notes": (
            "Not all nursing homes have penalty records — absence of records "
            "indicates no penalties imposed, not missing data. Penalty types "
            "include civil money penalties (fines) and denial of payment for "
            "new admissions. Fine amounts reflect CMS-imposed penalties and "
            "may differ from state-imposed penalties not tracked in this dataset. "
            "Multiple penalties per facility are stored as separate rows."
        ),
    },
    "nh-deficiencies": {
        "join_key": "Federal Provider Number (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~15 per deficiency record",
        "suppression_notes": (
            "Deficiencies are cited during state survey inspections, which "
            "occur on a roughly 12-month cycle (but can vary from 9 to 15 "
            "months). Scope and severity are coded on a grid from A (isolated, "
            "no harm potential) to L (widespread, immediate jeopardy). "
            "Complaint-driven inspections may add deficiency citations outside "
            "the regular survey cycle. The dataset captures the most recent "
            "3 years of standard surveys plus complaint surveys."
        ),
    },
    "nh-ownership": {
        "join_key": "Federal Provider Number (CCN)",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~10 per ownership record",
        "suppression_notes": (
            "Ownership data is self-reported on CMS Form 855A and may not "
            "reflect the full beneficial ownership chain for complex "
            "corporate structures (e.g., private equity or REIT arrangements). "
            "Multiple owners per facility appear as separate rows. Change-of-"
            "ownership events may have a 3-6 month reporting lag. The dataset "
            "captures current ownership only, not ownership history."
        ),
    },
    "snf-cost-report": {
        "join_key": "Provider CCN",
        "join_key_type": "6-digit string, zero-padded",
        "field_count": "~200+ (financial line items from SNF cost report worksheets)",
        "suppression_notes": (
            "Cost reports are self-reported and subject to audit but not "
            "systematically verified. Fiscal years vary by facility. "
            "Freestanding SNFs and hospital-based SNF units use different "
            "cost report forms, complicating comparisons. Approximately "
            "5-10% of facilities file late or submit amendments. Medicaid "
            "day shares can be inaccurate for dual-certified facilities."
        ),
    },
    # ── Phase 3 ACO cross-link datasets ─────────────────────────
    "aco-participants": {
        "join_key": "ACO_ID",
        "join_key_type": "Character string (e.g., A0001)",
        "field_count": "~8 per participant record",
        "suppression_notes": (
            "Participant lists reflect the roster at a point in time and "
            "may not capture mid-year additions or departures. Participants "
            "are identified by TIN (Tax Identification Number), not individual "
            "providers; a single TIN may represent a large multi-provider "
            "group practice. Hospital CCNs are listed for institutional "
            "participants but not all participants are hospitals."
        ),
    },
    "aco-snf-affiliates": {
        "join_key": "ACO_ID",
        "join_key_type": "Character string (e.g., A0001)",
        "field_count": "~6 per affiliate record",
        "suppression_notes": (
            "SNF affiliate lists represent the 3-day SNF waiver program "
            "and may not capture all SNFs that serve ACO beneficiaries. "
            "Not all MSSP ACOs participate in the SNF waiver. Affiliated "
            "SNFs are identified by CCN but the affiliation is with the "
            "ACO, not with a specific hospital within the ACO."
        ),
    },
    "aco-bene-county": {
        "join_key": "ACO_ID + State/County FIPS",
        "join_key_type": "ACO ID (string) + 5-digit FIPS code",
        "field_count": "~5 per ACO-county pair",
        "suppression_notes": (
            "Counties with fewer than 11 assigned beneficiaries for a "
            "given ACO are suppressed per CMS cell-size rules. This "
            "disproportionately affects ACOs with wide geographic spread "
            "and rural counties. The total across suppressed counties is "
            "also suppressed, so summing unsuppressed rows may undercount "
            "the ACO's total assigned beneficiaries."
        ),
    },
    # ── M5 datasets ─────────────────────────────────────────────────
    "partd-drug-spending": {
        "join_key": "Brand Name / Generic Name",
        "join_key_type": "Drug name string (aggregated by generic name, uppercased)",
        "field_count": "~15 per drug record",
        "suppression_notes": (
            "Drugs with fewer than 11 claims are excluded entirely. "
            "Spending data is aggregated across all Part D sponsors and "
            "plans. Generic name aggregation merges all brand-name "
            "formulations under a single generic, which may obscure "
            "price differences between brands. Low-income subsidy "
            "beneficiaries may have different cost-sharing patterns not "
            "visible in this aggregation."
        ),
    },
    "partb-drug-spending": {
        "join_key": "HCPCS Code / Generic Name",
        "join_key_type": "Drug name string (joined to drug entities by generic name)",
        "field_count": "~15 per drug record",
        "suppression_notes": (
            "Part B drug spending covers physician-administered drugs "
            "(infusions, injections) only — oral drugs are excluded. "
            "Drugs with fewer than 11 claims are excluded. HCPCS codes "
            "may map to multiple generic drugs or drug combinations, "
            "complicating the join to Part D drug entities. Average "
            "Spending Per Dosage Unit reflects ASP-based reimbursement, "
            "not acquisition cost."
        ),
    },
    "partb-discarded-units": {
        "join_key": "HCPCS Code / Generic Name",
        "join_key_type": "Drug name string (joined to drug entities by generic name)",
        "field_count": "~10 per drug record",
        "suppression_notes": (
            "Discarded units reporting was mandated by the JW modifier "
            "requirement (2017) and JZ modifier (2023). Compliance with "
            "modifier reporting is imperfect; facilities that fail to "
            "bill JW/JZ modifiers will not appear in this dataset. "
            "Discarded amounts reflect single-dose vial waste and are "
            "higher for drugs with limited vial size options."
        ),
    },
    "nadac": {
        "join_key": "NDC / Drug Name",
        "join_key_type": "Drug name string (matched to drug entities by generic name)",
        "field_count": "~8 per drug-date record",
        "suppression_notes": (
            "NADAC is a Medicaid program, not Medicare — it reflects "
            "pharmacy acquisition costs for retail community pharmacies "
            "surveyed voluntarily. Response rates vary and may not "
            "represent all pharmacy types (specialty, mail-order, 340B). "
            "NADAC is updated weekly; CareGraph uses the most recent "
            "snapshot. Prices reflect ingredient cost only, not dispensing "
            "fees or rebates."
        ),
    },
    "inpatient-by-drg": {
        "join_key": "DRG Code",
        "join_key_type": "3-digit numeric code (extracted from 'NNN - Description' format)",
        "field_count": "~10 per provider-DRG record",
        "suppression_notes": (
            "Only IPPS hospitals are included; critical access hospitals, "
            "Maryland waiver hospitals, and specialty hospitals paid under "
            "other systems are excluded. Provider-DRG combinations with "
            "fewer than 11 discharges are excluded. Charges represent "
            "billed amounts before negotiated discounts — they are not "
            "costs and should not be used as price proxies without "
            "applying a cost-to-charge ratio."
        ),
    },
    # ── Tier A enrichment datasets ─────────────────────────────────
    "cdc-sdoh": {
        "join_key": "FIPS county code (via LocationID)",
        "join_key_type": "5-digit string (state FIPS + county FIPS)",
        "field_count": "~20 per county",
        "suppression_notes": (
            "SDOH measures are compiled from the American Community Survey "
            "(ACS) and other Census Bureau sources with 1-5 year estimates. "
            "Small-population counties use 5-year estimates with wider "
            "margins of error. Some measures (e.g., broadband access, food "
            "desert status) come from different source years and may not "
            "align temporally with health outcome data."
        ),
    },
    "cms-chronic-conditions": {
        "join_key": "FIPS county code",
        "join_key_type": "5-digit string (state FIPS + county FIPS)",
        "field_count": "~30 per county (prevalence rates for 21 chronic conditions)",
        "suppression_notes": (
            "Prevalence rates cover Medicare fee-for-service beneficiaries "
            "only — Medicare Advantage enrollees are excluded, which biases "
            "prevalence downward in markets with high MA penetration. "
            "Counties with fewer than 11 beneficiaries with a given "
            "condition have that prevalence rate suppressed. Conditions "
            "are identified from claims, not clinical records, so "
            "under-coding and under-diagnosis lead to underestimates."
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
