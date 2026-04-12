"""
Build hospital page manifests from normalized Hospital General Information.

Reads the downloaded CSV, normalizes join keys, and emits one JSON manifest
per hospital into site_data/hospital/{CCN}.json.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_ccn
from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_hospital_manifest


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def build_hospitals(
    raw_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build hospital page manifests from Hospital General Information CSV.

    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    with open(raw_csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"  [build] Processing {total_rows:,} hospital rows")

    for row in rows:
        # The Provider Data CSV uses human-readable column names
        raw_ccn = row.get("Facility ID", "")
        ccn = normalize_ccn(raw_ccn)
        if ccn is None:
            errors += 1
            continue

        rating_raw = _clean(row.get("Hospital overall rating"))

        manifest: dict[str, Any] = {
            "entity_type": "hospital",
            "ccn": ccn,
            "facility_name": _clean(row.get("Facility Name")),
            "address": _clean(row.get("Address")),
            "city": _clean(row.get("City/Town")),
            "state": _clean(row.get("State")),
            "zip_code": _clean(row.get("ZIP Code")),
            "county_name": _clean(row.get("County/Parish")),
            "phone_number": _clean(row.get("Telephone Number")),
            "hospital_type": _clean(row.get("Hospital Type")),
            "hospital_ownership": _clean(row.get("Hospital Ownership")),
            "emergency_services": _clean(row.get("Emergency Services")),
            "hospital_overall_rating": rating_raw if rating_raw else None,
            "data": {
                "general_info": {
                    k: _clean(v) for k, v in row.items()
                    if k and v is not None
                },
            },
            "provenance": [
                build_provenance(
                    dataset_id="xubh-q36u",
                    dataset_name="Hospital General Information",
                    vintage=str(download_date.year),
                    download_date=download_date,
                    row_count=total_rows,
                ),
            ],
        }

        # Validate
        try:
            validate_hospital_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for CCN {ccn}: {e}")
            continue

        manifest_path = output_dir / f"{ccn}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} hospital manifests ({errors} skipped)")
    return count
