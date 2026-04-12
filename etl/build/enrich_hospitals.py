"""
Enrich hospital manifests with HRRP, HVBP, and FIPS data.

Reads existing hospital manifests from site_data/hospital/ and joins:
  a) HRRP (Hospital Readmissions Reduction Program) — readmission measures
  b) HVBP TPS (Hospital Value-Based Purchasing) — total performance scores
  c) FIPS codes — derived from county manifests

Updated manifests are written back in place.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_ccn
from etl.provenance.envelope import build_provenance


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def _try_float(val: str | None) -> float | None:
    if val is None:
        return None
    val = val.strip().replace(",", "")
    if val in ("", "N/A", "Not Available", ".", "*", "-", "Too Few to Report"):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _try_int(val: str | None) -> int | None:
    f = _try_float(val)
    if f is None:
        return None
    return int(f)


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


def _build_fips_lookup(county_dir: Path) -> dict[tuple[str, str], str]:
    """Build a (state, county_name_upper) -> FIPS lookup from county manifests."""
    lookup: dict[tuple[str, str], str] = {}
    if not county_dir.exists():
        return lookup

    for manifest_path in county_dir.glob("*.json"):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            state = manifest.get("state", "").strip().upper()
            county_name = manifest.get("county_name", "").strip().upper()
            fips = manifest.get("fips", "")
            if state and county_name and fips:
                lookup[(state, county_name)] = fips
                # Also store without common suffixes for fuzzy matching
                for suffix in (" COUNTY", " PARISH", " BOROUGH", " CENSUS AREA",
                               " MUNICIPALITY", " CITY AND BOROUGH", " CITY"):
                    if county_name.endswith(suffix):
                        lookup[(state, county_name[:-len(suffix)])] = fips
        except (json.JSONDecodeError, OSError):
            continue

    return lookup


def _lookup_fips(
    state: str,
    county_name: str,
    fips_lookup: dict[tuple[str, str], str],
) -> str | None:
    """Look up FIPS code from state + county name."""
    state_upper = state.strip().upper()
    county_upper = county_name.strip().upper()
    if not state_upper or not county_upper:
        return None

    # Direct lookup
    fips = fips_lookup.get((state_upper, county_upper))
    if fips:
        return fips

    # Try with/without "County" suffix
    for suffix in (" COUNTY", " PARISH", ""):
        key = (state_upper, county_upper + suffix)
        fips = fips_lookup.get(key)
        if fips:
            return fips

    # Try stripping common suffixes
    for suffix in (" COUNTY", " PARISH", " BOROUGH"):
        if county_upper.endswith(suffix):
            key = (state_upper, county_upper[:-len(suffix)])
            fips = fips_lookup.get(key)
            if fips:
                return fips

    return None


def _load_hrrp(
    hrrp_csv_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Load HRRP data grouped by CCN.

    Returns {ccn: [row_dicts]} where each row is a condition-level measure.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(hrrp_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Facility ID",
        "Hospital CCN",
        "Provider Number",
        "Facility Id",
        "CCN",
    ])
    col_measure = _find_column(sample, [
        "Measure Name",
        "Measure ID",
        "HRRP Measure Name",
        "Measure name",
    ])
    col_excess_ratio = _find_column(sample, [
        "Excess Readmission Ratio",
        "Excess readmission ratio",
    ])
    col_predicted = _find_column(sample, [
        "Predicted Readmission Rate",
        "Predicted readmission rate",
    ])
    col_expected = _find_column(sample, [
        "Expected Readmission Rate",
        "Expected readmission rate",
    ])
    col_num_readmissions = _find_column(sample, [
        "Number of Readmissions",
        "Number of readmissions",
        "Num Readmissions",
    ])
    col_num_discharges = _find_column(sample, [
        "Number of Discharges",
        "Number of discharges",
        "Num Discharges",
    ])

    if col_ccn is None:
        print("    [warn] Could not find CCN column in HRRP data")
        return result

    print(f"    [hrrp] CCN column: '{col_ccn}', Measure column: '{col_measure}'")

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        measure_data: dict[str, Any] = {}
        if col_measure:
            measure_data["measure_name"] = _clean(row.get(col_measure, ""))
        if col_excess_ratio:
            measure_data["excess_readmission_ratio"] = _try_float(row.get(col_excess_ratio))
        if col_predicted:
            measure_data["predicted_readmission_rate"] = _try_float(row.get(col_predicted))
        if col_expected:
            measure_data["expected_readmission_rate"] = _try_float(row.get(col_expected))
        if col_num_readmissions:
            measure_data["num_readmissions"] = _try_int(row.get(col_num_readmissions))
        if col_num_discharges:
            measure_data["num_discharges"] = _try_int(row.get(col_num_discharges))

        result.setdefault(ccn, []).append(measure_data)

    return result


def _load_hvbp(
    hvbp_csv_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load HVBP TPS data keyed by CCN.

    Returns {ccn: {scores}}.
    """
    result: dict[str, dict[str, Any]] = {}

    with open(hvbp_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Facility ID",
        "Hospital CCN",
        "Provider Number",
        "Facility Id",
        "CCN",
    ])
    col_tps = _find_column(sample, [
        "Total Performance Score",
        "Total performance score",
        "TPS",
    ])
    col_clinical = _find_column(sample, [
        "Clinical Outcomes Domain Score",
        "Clinical outcomes domain score",
        "Weighted Clinical Outcomes Domain Score",
    ])
    col_safety = _find_column(sample, [
        "Safety Domain Score",
        "Safety domain score",
        "Weighted Safety Domain Score",
    ])
    col_person = _find_column(sample, [
        "Person and Community Engagement Domain Score",
        "Person & Community Engagement Domain Score",
        "Weighted Person and Community Engagement Domain Score",
        "Person Community Domain Score",
    ])
    col_efficiency = _find_column(sample, [
        "Efficiency and Cost Reduction Domain Score",
        "Efficiency domain score",
        "Weighted Efficiency and Cost Reduction Domain Score",
        "Efficiency Domain Score",
    ])

    if col_ccn is None:
        print("    [warn] Could not find CCN column in HVBP data")
        return result

    print(f"    [hvbp] CCN column: '{col_ccn}', TPS column: '{col_tps}'")

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        scores: dict[str, Any] = {}
        if col_tps:
            scores["total_performance_score"] = _try_float(row.get(col_tps))
        if col_clinical:
            scores["clinical_outcomes_score"] = _try_float(row.get(col_clinical))
        if col_safety:
            scores["safety_score"] = _try_float(row.get(col_safety))
        if col_person:
            scores["person_community_score"] = _try_float(row.get(col_person))
        if col_efficiency:
            scores["efficiency_score"] = _try_float(row.get(col_efficiency))

        result[ccn] = scores

    return result


def enrich_hospitals(
    hospital_dir: Path,
    county_dir: Path,
    hrrp_csv_path: Path,
    hvbp_csv_path: Path,
    download_date: date,
) -> int:
    """Enrich hospital manifests with HRRP, HVBP, and FIPS data.

    Reads existing manifests, joins enrichment data, and writes back.
    Returns the number of manifests enriched.
    """
    if not hospital_dir.exists():
        print("  [enrich] No hospital directory found")
        return 0

    # Load enrichment data
    print("  [enrich] Loading HRRP data...")
    hrrp_data = _load_hrrp(hrrp_csv_path)
    print(f"  [enrich] HRRP: {len(hrrp_data):,} hospitals with readmission data")

    print("  [enrich] Loading HVBP data...")
    hvbp_data = _load_hvbp(hvbp_csv_path)
    print(f"  [enrich] HVBP: {len(hvbp_data):,} hospitals with VBP scores")

    print("  [enrich] Building FIPS lookup from county manifests...")
    fips_lookup = _build_fips_lookup(county_dir)
    print(f"  [enrich] FIPS lookup: {len(fips_lookup):,} entries")

    # Count HRRP/HVBP rows for provenance
    hrrp_row_count = sum(len(v) for v in hrrp_data.values())
    hvbp_row_count = len(hvbp_data)

    enriched = 0
    manifest_files = sorted(hospital_dir.glob("*.json"))

    for manifest_path in manifest_files:
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ccn = manifest.get("ccn", "")
        modified = False

        # a) HRRP join
        if ccn in hrrp_data:
            measures = hrrp_data[ccn]
            readmissions: dict[str, Any] = {}
            for m in measures:
                measure_name = m.get("measure_name", "")
                if measure_name:
                    readmissions[measure_name] = {
                        k: v for k, v in m.items()
                        if k != "measure_name"
                    }
            if readmissions:
                manifest.setdefault("data", {})["readmissions"] = readmissions
                modified = True

        # b) HVBP join
        if ccn in hvbp_data:
            manifest.setdefault("data", {})["vbp"] = hvbp_data[ccn]
            modified = True

        # c) FIPS lookup
        if not manifest.get("fips"):
            state = manifest.get("state", "")
            county_name = manifest.get("county_name", "")
            fips = _lookup_fips(state, county_name, fips_lookup)
            if fips:
                manifest["fips"] = fips
                modified = True

        # Add enrichment provenance
        if modified:
            provenance_list = manifest.get("provenance", [])
            existing_ids = {p.get("dataset_id") for p in provenance_list}

            if ccn in hrrp_data and "hrrp" not in existing_ids:
                provenance_list.append(
                    build_provenance(
                        dataset_id="hrrp",
                        dataset_name="Hospital Readmissions Reduction Program",
                        vintage="FY2026",
                        download_date=download_date,
                        row_count=hrrp_row_count,
                    )
                )

            if ccn in hvbp_data and "hvbp-tps" not in existing_ids:
                provenance_list.append(
                    build_provenance(
                        dataset_id="hvbp-tps",
                        dataset_name="Hospital Value-Based Purchasing TPS",
                        vintage="FY2026",
                        download_date=download_date,
                        row_count=hvbp_row_count,
                    )
                )

            manifest["provenance"] = provenance_list

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            enriched += 1

    print(f"  [enrich] Enriched {enriched:,} hospital manifests")
    return enriched
