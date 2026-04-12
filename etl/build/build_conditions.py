"""
Build Condition entity page manifests from CDC PLACES county-level data.

Aggregates across all counties to build condition-level summaries:
national average, min/max counties, top/bottom 10 counties by prevalence.

Output: site_data/condition/{condition_id}.json
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_fips
from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_condition_manifest


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def _try_float(val: str | None) -> float | None:
    """Parse a float, returning None for blanks or non-numeric values."""
    if val is None:
        return None
    val = val.strip().replace(",", "").replace("$", "").replace("%", "")
    if val in ("", "N/A", "Not Available", ".", "*", "-"):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _find_column(row: dict[str, str], candidates: list[str]) -> str | None:
    """Find the first matching column name from candidates.

    Tries exact match, then case-insensitive, then substring.
    """
    row_keys = list(row.keys())
    row_keys_upper = {k.upper(): k for k in row_keys}

    for candidate in candidates:
        if candidate in row:
            return candidate
        if candidate.upper() in row_keys_upper:
            return row_keys_upper[candidate.upper()]

    for candidate in candidates:
        candidate_upper = candidate.upper()
        for key in row_keys:
            if candidate_upper in key.upper():
                return key

    return None


def build_conditions(
    places_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build condition page manifests from CDC PLACES CSV.

    Filters to county-level rows, groups by measureid, and creates one
    condition entity per measure.

    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    with open(places_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"  [build] Processing {total_rows:,} PLACES rows for conditions")

    if not rows:
        print("  [build] No PLACES rows found")
        return 0

    # Detect column names from first row
    sample = rows[0]
    col_fips = _find_column(sample, [
        "locationid", "LocationID", "CountyFIPS", "FIPS",
    ])
    col_location_name = _find_column(sample, [
        "locationname", "LocationName", "Location_Name",
    ])
    col_geo_level = _find_column(sample, [
        "geolevel", "GeoLevel", "Geographic Level",
    ])
    col_measure_id = _find_column(sample, [
        "measureid", "MeasureId", "Measure ID", "Short_Question_Text",
    ])
    col_measure = _find_column(sample, [
        "measure", "Measure", "MeasureName",
    ])
    col_category = _find_column(sample, [
        "category", "Category",
    ])
    col_data_value = _find_column(sample, [
        "data_value", "DataValue", "Data_Value",
    ])
    col_state_abbr = _find_column(sample, [
        "stateabbr", "StateAbbr", "State_Abbr", "state_abbr",
    ])

    if col_measure_id is None:
        print("  [build] ERROR: Could not find measureid column in PLACES data")
        print(f"  [build] Available columns: {list(sample.keys())[:20]}...")
        return 0
    if col_fips is None:
        print("  [build] ERROR: Could not find FIPS/LocationID column in PLACES data")
        return 0

    print(f"  [build] Columns: measure_id='{col_measure_id}', fips='{col_fips}', "
          f"value='{col_data_value}'")

    # Group county-level rows by measure_id
    measure_data: dict[str, dict[str, Any]] = {}  # measure_id -> metadata
    measure_counties: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        # Filter to county-level data
        if col_geo_level:
            geo_level = _clean(row.get(col_geo_level, "")).lower()
            if geo_level and geo_level != "county":
                continue

        raw_fips = row.get(col_fips, "")
        fips = normalize_fips(raw_fips)
        if fips is None or len(fips) != 5:
            continue

        measure_id = _clean(row.get(col_measure_id, "")).upper()
        if not measure_id:
            continue

        value = _try_float(row.get(col_data_value))
        if value is None:
            continue

        # Store measure metadata (first occurrence wins)
        if measure_id not in measure_data:
            measure_data[measure_id] = {
                "measure_name": _clean(row.get(col_measure, "")) if col_measure else measure_id,
                "category": _clean(row.get(col_category, "")) if col_category else "",
            }

        location_name = _clean(row.get(col_location_name, "")) if col_location_name else ""
        state_abbr = _clean(row.get(col_state_abbr, "")) if col_state_abbr else ""

        measure_counties[measure_id].append({
            "fips": fips,
            "name": location_name,
            "state": state_abbr,
            "value": value,
        })

    print(f"  [build] Found {len(measure_data):,} unique conditions across county data")

    # Build one manifest per condition
    for measure_id, meta in measure_data.items():
        counties = measure_counties.get(measure_id, [])
        if not counties:
            errors += 1
            continue

        # Sort by value for top/bottom analysis
        counties_sorted = sorted(counties, key=lambda c: c["value"])

        values = [c["value"] for c in counties_sorted]
        national_avg = round(sum(values) / len(values), 2)

        min_county = counties_sorted[0]
        max_county = counties_sorted[-1]
        bottom_10 = counties_sorted[:10]
        top_10 = counties_sorted[-10:]
        top_10.reverse()  # Highest first

        condition_id = measure_id  # e.g., "DIABETES", "OBESITY"

        manifest: dict[str, Any] = {
            "entity_type": "condition",
            "condition_id": condition_id,
            "condition_name": meta["measure_name"],
            "category": meta["category"],
            "data": {
                "places": {
                    "national_avg": national_avg,
                    "min_county": {
                        "fips": min_county["fips"],
                        "name": min_county["name"],
                        "state": min_county["state"],
                        "value": min_county["value"],
                    },
                    "max_county": {
                        "fips": max_county["fips"],
                        "name": max_county["name"],
                        "state": max_county["state"],
                        "value": max_county["value"],
                    },
                    "top_counties": [
                        {
                            "fips": c["fips"],
                            "name": c["name"],
                            "state": c["state"],
                            "value": c["value"],
                        }
                        for c in top_10
                    ],
                    "bottom_counties": [
                        {
                            "fips": c["fips"],
                            "name": c["name"],
                            "state": c["state"],
                            "value": c["value"],
                        }
                        for c in bottom_10
                    ],
                    "total_counties": len(counties),
                },
            },
            "provenance": [
                build_provenance(
                    dataset_id="cdc-places",
                    dataset_name="CDC PLACES County-Level Data",
                    vintage=str(download_date.year),
                    download_date=download_date,
                    row_count=total_rows,
                    source_url="https://data.cdc.gov/resource/swc5-untb",
                ),
            ],
        }

        # Validate
        try:
            validate_condition_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for condition {condition_id}: {e}")
            continue

        manifest_path = output_dir / f"{condition_id}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} condition manifests ({errors} skipped)")
    return count
