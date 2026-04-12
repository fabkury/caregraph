"""
Enrich SNF manifests with penalties, health deficiencies, and ownership data.

Reads existing SNF manifests from site_data/snf/ and joins:
  a) Penalties — fines and payment denials in the last 3 years
  b) Health Deficiencies — inspection citations with scope/severity
  c) Ownership ��� corporate ownership chain

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
    val = val.strip().replace(",", "").replace("$", "")
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


def _load_penalties(csv_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load penalty data grouped by CCN.

    Returns {ccn: [{penalty_date, penalty_type, fine_amount, ...}]}.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Federal Provider Number",
        "CMS Certification Number (CCN)",
        "Provider Number", "CCN", "Facility ID",
    ])

    if col_ccn is None:
        print("    [warn] Could not find CCN column in penalties data")
        return result

    col_date = _find_column(sample, [
        "Penalty Date", "Fine Date", "penalty_date",
    ])
    col_type = _find_column(sample, [
        "Penalty Type", "penalty_type",
    ])
    col_amount = _find_column(sample, [
        "Fine Amount", "Penalty Amount", "fine_amount",
    ])

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        penalty: dict[str, Any] = {}
        if col_date:
            penalty["penalty_date"] = _clean(row.get(col_date, ""))
        if col_type:
            penalty["penalty_type"] = _clean(row.get(col_type, ""))
        if col_amount:
            penalty["fine_amount"] = _try_float(row.get(col_amount))

        # Include all other non-empty fields
        for k, v in row.items():
            if k == col_ccn or k in (col_date, col_type, col_amount):
                continue
            cleaned = _clean(v)
            if cleaned and cleaned not in ("N/A", "Not Available"):
                penalty[k] = cleaned

        if penalty:
            result.setdefault(ccn, []).append(penalty)

    return result


def _load_deficiencies(csv_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load health deficiency data grouped by CCN.

    Returns {ccn: [{tag, description, scope_severity, inspection_date, ...}]}.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Federal Provider Number",
        "CMS Certification Number (CCN)",
        "Provider Number", "CCN", "Facility ID",
    ])

    if col_ccn is None:
        print("    [warn] Could not find CCN column in deficiencies data")
        return result

    col_tag = _find_column(sample, [
        "Deficiency Tag Number", "Tag", "Survey Deficiency Tag",
        "deficiency_tag_number",
    ])
    col_desc = _find_column(sample, [
        "Deficiency Description", "Tag Description", "Description",
    ])
    col_scope = _find_column(sample, [
        "Scope Severity Code", "Scope/Severity",
        "scope_severity_code", "Scope Severity",
    ])
    col_date = _find_column(sample, [
        "Survey Date", "Inspection Date", "survey_date",
    ])
    col_correction = _find_column(sample, [
        "Correction Date", "correction_date",
    ])

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        deficiency: dict[str, Any] = {}
        if col_tag:
            deficiency["tag"] = _clean(row.get(col_tag, ""))
        if col_desc:
            deficiency["description"] = _clean(row.get(col_desc, ""))
        if col_scope:
            deficiency["scope_severity"] = _clean(row.get(col_scope, ""))
        if col_date:
            deficiency["survey_date"] = _clean(row.get(col_date, ""))
        if col_correction:
            deficiency["correction_date"] = _clean(row.get(col_correction, ""))

        if deficiency:
            result.setdefault(ccn, []).append(deficiency)

    return result


def _load_ownership(csv_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load ownership data grouped by CCN.

    Returns {ccn: [{owner_name, owner_type, ownership_percentage, ...}]}.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Federal Provider Number",
        "CMS Certification Number (CCN)",
        "Provider Number", "CCN", "Facility ID",
    ])

    if col_ccn is None:
        print("    [warn] Could not find CCN column in ownership data")
        return result

    col_name = _find_column(sample, [
        "Owner Name", "Organization Name", "owner_name",
    ])
    col_type = _find_column(sample, [
        "Owner Type", "Role Description", "owner_type",
    ])
    col_pct = _find_column(sample, [
        "Ownership Percentage", "Percentage Ownership",
        "ownership_percentage",
    ])

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        owner: dict[str, Any] = {}
        if col_name:
            owner["owner_name"] = _clean(row.get(col_name, ""))
        if col_type:
            owner["owner_type"] = _clean(row.get(col_type, ""))
        if col_pct:
            owner["ownership_percentage"] = _try_float(row.get(col_pct))

        # Include remaining non-empty fields
        for k, v in row.items():
            if k in (col_ccn, col_name, col_type, col_pct):
                continue
            cleaned = _clean(v)
            if cleaned and cleaned not in ("N/A", "Not Available"):
                owner[k] = cleaned

        if owner:
            result.setdefault(ccn, []).append(owner)

    return result


def enrich_snfs(
    snf_dir: Path,
    download_date: date,
    *,
    penalties_csv: Path | None = None,
    deficiencies_csv: Path | None = None,
    ownership_csv: Path | None = None,
) -> int:
    """Enrich SNF manifests with penalties, deficiencies, and ownership data.

    Reads existing manifests, joins enrichment data, and writes back.
    Returns the number of manifests enriched.
    """
    if not snf_dir.exists():
        print("  [enrich-snf] No SNF directory found")
        return 0

    # Load datasets
    penalties_data: dict[str, list[dict[str, Any]]] = {}
    if penalties_csv and penalties_csv.exists():
        print("  [enrich-snf] Loading penalties data...")
        penalties_data = _load_penalties(penalties_csv)
        print(f"  [enrich-snf] Penalties: {len(penalties_data):,} facilities")

    deficiencies_data: dict[str, list[dict[str, Any]]] = {}
    if deficiencies_csv and deficiencies_csv.exists():
        print("  [enrich-snf] Loading health deficiencies data...")
        deficiencies_data = _load_deficiencies(deficiencies_csv)
        print(f"  [enrich-snf] Deficiencies: {len(deficiencies_data):,} facilities")

    ownership_data: dict[str, list[dict[str, Any]]] = {}
    if ownership_csv and ownership_csv.exists():
        print("  [enrich-snf] Loading ownership data...")
        ownership_data = _load_ownership(ownership_csv)
        print(f"  [enrich-snf] Ownership: {len(ownership_data):,} facilities")

    if not penalties_data and not deficiencies_data and not ownership_data:
        print("  [enrich-snf] No enrichment data available")
        return 0

    DATASETS = [
        ("nh-penalties", "Nursing Home Penalties",
         penalties_data, "penalties"),
        ("nh-deficiencies", "Nursing Home Health Deficiencies",
         deficiencies_data, "deficiencies"),
        ("nh-ownership", "Nursing Home Ownership",
         ownership_data, "ownership"),
    ]

    enriched = 0
    manifest_files = sorted(snf_dir.glob("*.json"))

    for manifest_path in manifest_files:
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ccn = manifest.get("ccn", "")
        modified = False

        for ds_id, ds_name, ds_data, manifest_key in DATASETS:
            if ccn in ds_data:
                manifest.setdefault("data", {})[manifest_key] = ds_data[ccn]
                modified = True

        if modified:
            provenance_list = manifest.get("provenance", [])
            existing_ids = {p.get("dataset_id") for p in provenance_list}

            for ds_id, ds_name, ds_data, manifest_key in DATASETS:
                if ccn in ds_data and ds_id not in existing_ids:
                    provenance_list.append(
                        build_provenance(
                            dataset_id=ds_id,
                            dataset_name=ds_name,
                            vintage=str(download_date.year),
                            download_date=download_date,
                            row_count=sum(len(v) for v in ds_data.values()),
                        )
                    )

            manifest["provenance"] = provenance_list

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            enriched += 1

    print(f"  [enrich-snf] Enriched {enriched:,} SNF manifests")
    return enriched
