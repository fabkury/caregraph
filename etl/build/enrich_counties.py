"""
Enrich county manifests with CDC PLACES health measures.

Reads the CDC PLACES CSV (county-level data), groups measures by FIPS,
and merges them into existing county manifests.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_fips
from etl.provenance.envelope import build_provenance


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def _try_float(val: str | None) -> float | None:
    if val is None:
        return None
    val = val.strip().replace(",", "")
    if val in ("", "N/A", "Not Available", ".", "*", "-"):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _find_column(row: dict[str, str], candidates: list[str]) -> str | None:
    """Find the first matching column name from candidates."""
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


def _load_places(
    places_csv_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Load CDC PLACES data grouped by FIPS.

    Filters to county-level data. Returns {fips: [measure_dicts]}.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(places_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    total_rows = len(rows)
    sample = rows[0]

    # Detect column names
    col_fips = _find_column(sample, [
        "locationid",
        "LocationID",
        "CountyFIPS",
        "FIPS",
        "locationname",
    ])
    col_geo_level = _find_column(sample, [
        "geolevel",
        "GeoLevel",
        "Geographic Level",
    ])
    col_measure_id = _find_column(sample, [
        "measureid",
        "MeasureId",
        "Measure ID",
        "Short_Question_Text",
    ])
    col_measure = _find_column(sample, [
        "measure",
        "Measure",
        "MeasureName",
    ])
    col_category = _find_column(sample, [
        "category",
        "Category",
    ])
    col_data_value = _find_column(sample, [
        "data_value",
        "DataValue",
        "Data_Value",
        "data value",
    ])
    col_data_value_type = _find_column(sample, [
        "data_value_type",
        "DataValueType",
        "Data_Value_Type",
    ])
    col_low_ci = _find_column(sample, [
        "low_confidence_limit",
        "LowConfidenceLimit",
        "Low_Confidence_Limit",
    ])
    col_high_ci = _find_column(sample, [
        "high_confidence_limit",
        "HighConfidenceLimit",
        "High_Confidence_Limit",
    ])
    col_totpop = _find_column(sample, [
        "totalpopulation",
        "TotalPopulation",
        "Total_Population",
    ])

    if col_fips is None:
        print("    [warn] Could not find FIPS/LocationID column in PLACES data")
        print(f"    [warn] Available columns: {list(sample.keys())[:15]}...")
        return result

    print(f"    [places] FIPS column: '{col_fips}', Measure column: '{col_measure_id}'")
    print(f"    [places] Total rows: {total_rows:,}")

    county_rows = 0
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

        measure_entry: dict[str, Any] = {}
        if col_measure_id:
            measure_entry["measure_id"] = _clean(row.get(col_measure_id, ""))
        if col_measure:
            measure_entry["measure"] = _clean(row.get(col_measure, ""))
        if col_category:
            measure_entry["category"] = _clean(row.get(col_category, ""))
        if col_data_value:
            measure_entry["value"] = _try_float(row.get(col_data_value))
        if col_data_value_type:
            measure_entry["value_type"] = _clean(row.get(col_data_value_type, ""))
        if col_low_ci:
            measure_entry["low_ci"] = _try_float(row.get(col_low_ci))
        if col_high_ci:
            measure_entry["high_ci"] = _try_float(row.get(col_high_ci))
        if col_totpop:
            measure_entry["total_population"] = _try_float(row.get(col_totpop))

        result.setdefault(fips, []).append(measure_entry)
        county_rows += 1

    print(f"    [places] {county_rows:,} county-level measure rows across {len(result):,} counties")
    return result


def enrich_counties(
    county_dir: Path,
    places_csv_path: Path,
    download_date: date,
) -> int:
    """Enrich county manifests with CDC PLACES health measures.

    Reads existing manifests, adds PLACES measures, and writes back.
    Returns the number of manifests enriched.
    """
    if not county_dir.exists():
        print("  [enrich] No county directory found")
        return 0

    # Load PLACES data
    print("  [enrich] Loading CDC PLACES data...")
    places_data = _load_places(places_csv_path)
    print(f"  [enrich] PLACES: {len(places_data):,} counties with health measures")

    if not places_data:
        print("  [enrich] No PLACES data to merge")
        return 0

    total_measures = sum(len(v) for v in places_data.values())

    enriched = 0
    manifest_files = sorted(county_dir.glob("*.json"))

    for manifest_path in manifest_files:
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        fips = manifest.get("fips", "")
        if fips not in places_data:
            continue

        measures = places_data[fips]

        # Build places dict keyed by measure_id
        places_dict: dict[str, Any] = {}
        for m in measures:
            measure_id = m.get("measure_id", "")
            if measure_id:
                places_dict[measure_id] = {
                    k: v for k, v in m.items()
                    if k != "measure_id"
                }
            else:
                # If no measure_id, use the measure name
                measure_name = m.get("measure", f"measure_{len(places_dict)}")
                places_dict[measure_name] = m

        manifest.setdefault("data", {})["places"] = places_dict

        # Add provenance
        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "cdc-places" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="cdc-places",
                    dataset_name="CDC PLACES County-Level Data",
                    vintage=str(download_date.year),
                    download_date=download_date,
                    row_count=total_measures,
                    source_url="https://data.cdc.gov/resource/swc5-untb",
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    print(f"  [enrich] Enriched {enriched:,} county manifests with PLACES data")
    return enriched
