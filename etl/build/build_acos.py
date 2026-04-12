"""
Build ACO page manifests from MSSP Performance data.

Reads the downloaded CSV, normalizes ACO IDs, and emits one JSON manifest
per ACO into site_data/aco/{ACO_ID}.json.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_aco_id
from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_aco_manifest


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


# Key metrics to extract from MSSP Performance data
MSSP_METRIC_LABELS = {
    "N_AB": "Assigned Beneficiaries",
    "Sav_rate": "Savings Rate",
    "GenSaveLoss": "Generated Savings/Losses ($)",
    "EarnSaveLoss": "Earned Savings/Losses ($)",
    "QualScore": "Quality Score",
    "Per_Capita_Exp_TOTAL_PY": "Per Capita Expenditure, Total ($)",
    "Per_Capita_Exp_TOTAL_BY": "Per Capita Expenditure, Benchmark ($)",
    "UpdatedBnchmk": "Updated Benchmark ($)",
    "ABtotben": "Total Assigned Beneficiary Benchmark ($)",
    "TotalExpnd": "Total Expenditures ($)",
}


def build_acos(
    raw_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build ACO page manifests from MSSP Performance CSV.

    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    with open(raw_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"  [build] Processing {total_rows:,} ACO rows")

    if not rows:
        print("  [build] No ACO rows found")
        return 0

    # Detect column names from the first row
    sample = rows[0]
    col_aco_id = _find_column(sample, [
        "ACO_ID",
        "ACO_Num",
        "ACO_NUM",
        "aco_id",
        "ACO ID",
        "ACO Number",
    ])
    col_aco_name = _find_column(sample, [
        "ACO_Name",
        "ACO_NAME",
        "ACO Name",
        "aco_name",
    ])
    col_track = _find_column(sample, [
        "Current_Track",
        "Cur_Track_1",
        "Current Track",
        "Initial_Track_1",
        "Track",
        "AgreementPeriodNum",
    ])
    col_state = _find_column(sample, [
        "ACO_State",
        "ACO_ST",
        "State",
        "ACO State",
    ])

    if col_aco_id is None:
        print("  [build] ERROR: Could not find ACO ID column in MSSP data")
        print(f"  [build] Available columns: {list(sample.keys())[:20]}...")
        return 0

    print(f"  [build] ACO ID column: '{col_aco_id}'")
    print(f"  [build] ACO Name column: '{col_aco_name}'")

    for row in rows:
        raw_id = row.get(col_aco_id, "")
        aco_id = normalize_aco_id(raw_id)
        if aco_id is None:
            errors += 1
            continue

        # Extract key metrics
        metrics: dict[str, Any] = {}
        for col, label in MSSP_METRIC_LABELS.items():
            actual_col = _find_column(row, [col])
            if actual_col:
                val = _try_float(row.get(actual_col))
                if val is not None:
                    metrics[col] = {
                        "value": val,
                        "label": label,
                    }

        # Raw data for full table view
        raw_data = {k: _clean(v) for k, v in row.items() if k}

        manifest: dict[str, Any] = {
            "entity_type": "aco",
            "aco_id": aco_id,
            "aco_name": _clean(row.get(col_aco_name, "")) if col_aco_name else "",
            "current_track": _clean(row.get(col_track, "")) if col_track else "",
            "state": _clean(row.get(col_state, "")) if col_state else "",
            "data": {
                "mssp_performance": {
                    "metrics": metrics,
                    "raw": raw_data,
                },
            },
            "provenance": [
                build_provenance(
                    dataset_id="mssp-performance",
                    dataset_name="MSSP ACO Performance PY2024",
                    vintage="PY2024",
                    download_date=download_date,
                    row_count=total_rows,
                ),
            ],
        }

        # Validate
        try:
            validate_aco_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for ACO {aco_id}: {e}")
            continue

        manifest_path = output_dir / f"{aco_id}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} ACO manifests ({errors} skipped)")
    return count
