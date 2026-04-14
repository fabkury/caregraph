"""
Build SNF (Skilled Nursing Facility) page manifests from Nursing Home Provider Info.

Reads the downloaded CSV, normalizes CCN keys, and emits one JSON manifest
per SNF into site_data/snf/{CCN}.json.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_ccn
from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_snf_manifest


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def _int_or_none(val: str | None) -> int | None:
    """Parse an integer, returning None for blanks or non-numeric values.

    Floats are rounded to the nearest integer (88.6 → 89) rather than
    truncated, so fields like average daily census aren't systematically
    under-reported.
    """
    if val is None:
        return None
    val = val.strip().replace(",", "")
    if val in ("", "N/A", "Not Available", ".", "*"):
        return None
    try:
        return round(float(val))
    except (ValueError, TypeError):
        return None


def _rating_or_none(val: str | None) -> str | None:
    """Parse a 1-5 star rating. Returns string '1'-'5' or None."""
    if val is None:
        return None
    val = val.strip()
    if val in ("1", "2", "3", "4", "5"):
        return val
    return None


def _find_column(row: dict[str, str], candidates: list[str]) -> str | None:
    """Find the first matching column name from a list of candidates.

    Tries exact match first, then case-insensitive match, then substring match.
    """
    row_keys = list(row.keys())
    row_keys_upper = {k.upper(): k for k in row_keys}

    for candidate in candidates:
        # Exact match
        if candidate in row:
            return candidate
        # Case-insensitive match
        if candidate.upper() in row_keys_upper:
            return row_keys_upper[candidate.upper()]

    # Substring match (less strict)
    for candidate in candidates:
        candidate_upper = candidate.upper()
        for key in row_keys:
            if candidate_upper in key.upper():
                return key

    return None


def build_snfs(
    raw_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build SNF page manifests from Nursing Home Provider Info CSV.

    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    with open(raw_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"  [build] Processing {total_rows:,} SNF rows")

    if not rows:
        print("  [build] No SNF rows found")
        return 0

    # Detect column names from the first row
    sample = rows[0]
    col_ccn = _find_column(sample, [
        "CMS Certification Number (CCN)",
        "Federal Provider Number",
        "CMS Certification Number",
        "Facility ID",
        "CCN",
        "Provider Number",
    ])
    col_name = _find_column(sample, [
        "Provider Name",
        "Facility Name",
        "Provider name",
    ])
    col_address = _find_column(sample, [
        "Provider Address",
        "Address",
        "Provider address",
    ])
    col_city = _find_column(sample, [
        "Provider City",
        "City/Town",
        "City",
        "Provider city",
    ])
    col_state = _find_column(sample, [
        "Provider State",
        "State",
        "Provider state",
    ])
    col_zip = _find_column(sample, [
        "Provider Zip Code",
        "ZIP Code",
        "Zip Code",
        "Provider zip code",
    ])
    col_county = _find_column(sample, [
        "Provider County Name",
        "County/Parish",
        "County Name",
        "Provider county name",
    ])
    col_beds = _find_column(sample, [
        "Number of Certified Beds",
        "Certified Beds",
        "Total Number of Beds",
    ])
    col_avg_residents = _find_column(sample, [
        "Average Number of Residents per Day",
        "Average Number of Residents Per Day",
        "Avg Residents per Day",
    ])
    col_overall = _find_column(sample, [
        "Overall Rating",
        "Overall rating",
    ])
    col_health = _find_column(sample, [
        "Health Inspection Rating",
        "Health inspection rating",
    ])
    col_qm = _find_column(sample, [
        "QM Rating",
        "Quality Measure Rating",
        "Qm rating",
    ])
    col_staffing = _find_column(sample, [
        "Staffing Rating",
        "Staffing rating",
    ])
    col_ownership = _find_column(sample, [
        "Ownership Type",
        "Ownership type",
    ])
    col_in_hospital = _find_column(sample, [
        "Provider Resides in Hospital",
        "Provider resides in hospital",
        "Located in Hospital",
    ])

    if col_ccn is None:
        print("  [build] ERROR: Could not find CCN column in SNF data")
        print(f"  [build] Available columns: {list(sample.keys())[:15]}...")
        return 0

    print(f"  [build] CCN column: '{col_ccn}'")
    print(f"  [build] Name column: '{col_name}'")

    for row in rows:
        raw_ccn = row.get(col_ccn, "")
        ccn = normalize_ccn(raw_ccn)
        if ccn is None:
            errors += 1
            continue

        manifest: dict[str, Any] = {
            "entity_type": "snf",
            "ccn": ccn,
            "provider_name": _clean(row.get(col_name, "")) if col_name else "",
            "address": _clean(row.get(col_address, "")) if col_address else "",
            "city": _clean(row.get(col_city, "")) if col_city else "",
            "state": _clean(row.get(col_state, "")) if col_state else "",
            "zip_code": _clean(row.get(col_zip, "")) if col_zip else "",
            "county_name": _clean(row.get(col_county, "")) if col_county else "",
            "beds": _int_or_none(row.get(col_beds)) if col_beds else None,
            "average_residents_per_day": (
                _int_or_none(row.get(col_avg_residents))
                if col_avg_residents else None
            ),
            "overall_rating": _rating_or_none(row.get(col_overall)) if col_overall else None,
            "health_inspection_rating": _rating_or_none(row.get(col_health)) if col_health else None,
            "qm_rating": _rating_or_none(row.get(col_qm)) if col_qm else None,
            "staffing_rating": _rating_or_none(row.get(col_staffing)) if col_staffing else None,
            "ownership_type": _clean(row.get(col_ownership, "")) if col_ownership else "",
            "provider_resides_in_hospital": (
                _clean(row.get(col_in_hospital, ""))
                if col_in_hospital else ""
            ),
            "data": {
                "provider_info": {
                    k: _clean(v) for k, v in row.items()
                    if k and v is not None
                },
            },
            "provenance": [
                build_provenance(
                    dataset_id="nh-provider-info",
                    dataset_name="Nursing Home Provider Info",
                    vintage=str(download_date.year),
                    download_date=download_date,
                    row_count=total_rows,
                ),
            ],
        }

        # Validate
        try:
            validate_snf_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for CCN {ccn}: {e}")
            continue

        manifest_path = output_dir / f"{ccn}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} SNF manifests ({errors} skipped)")
    return count
