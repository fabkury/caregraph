"""
Build DRG entity page manifests from Medicare Inpatient by Provider & Service data.

Groups rows by DRG code and aggregates discharge volumes, payment statistics,
and identifies top hospitals for each DRG.

Output: site_data/drg/{drg_code}.json
"""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_drg_manifest


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


def _try_int(val: str | None) -> int | None:
    """Parse an integer, returning None for blanks or non-numeric values."""
    f = _try_float(val)
    if f is None:
        return None
    return int(round(f))


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


def build_drgs(
    inpatient_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build DRG page manifests from Medicare Inpatient by Provider & Service CSV.

    Each row in the CSV is one hospital + one DRG. We group by DRG code
    and aggregate across all hospitals.

    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    with open(inpatient_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"  [build] Processing {total_rows:,} inpatient rows for DRGs")

    if not rows:
        print("  [build] No inpatient rows found")
        return 0

    # Detect column names from first row
    sample = rows[0]
    col_drg_cd = _find_column(sample, [
        "DRG_Cd", "drg_cd", "DRG_Code", "DRG Code", "Drg_Cd",
    ])
    col_drg_desc = _find_column(sample, [
        "DRG_Desc", "drg_desc", "DRG_Description", "DRG Description", "Drg_Desc",
    ])
    col_ccn = _find_column(sample, [
        "Rndrng_Prvdr_CCN", "rndrng_prvdr_ccn", "Provider_CCN",
        "Rndrng_Prvdr_Org_Name",  # fallback
    ])
    col_prvdr_name = _find_column(sample, [
        "Rndrng_Prvdr_Org_Name", "rndrng_prvdr_org_name",
        "Provider_Name", "Provider Name",
    ])
    col_discharges = _find_column(sample, [
        "Tot_Dschrgs", "tot_dschrgs", "Total_Discharges", "Total Discharges",
    ])
    col_avg_cvrd_chrg = _find_column(sample, [
        "Avg_Submtd_Cvrd_Chrg", "avg_submtd_cvrd_chrg",
        "Avg_Covered_Charge", "Average Covered Charges",
    ])
    col_avg_tot_pymt = _find_column(sample, [
        "Avg_Tot_Pymt_Amt", "avg_tot_pymt_amt",
        "Avg_Total_Payment", "Average Total Payments",
    ])
    col_avg_mdcr_pymt = _find_column(sample, [
        "Avg_Mdcr_Pymt_Amt", "avg_mdcr_pymt_amt",
        "Avg_Medicare_Payment", "Average Medicare Payments",
    ])

    if col_drg_cd is None:
        print("  [build] ERROR: Could not find DRG_Cd column in inpatient data")
        print(f"  [build] Available columns: {list(sample.keys())[:20]}...")
        return 0

    print(f"  [build] DRG columns: code='{col_drg_cd}', desc='{col_drg_desc}', "
          f"discharges='{col_discharges}'")

    # Group rows by DRG code
    drg_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    drg_desc_map: dict[str, str] = {}

    for row in rows:
        raw_drg = _clean(row.get(col_drg_cd, ""))
        if not raw_drg:
            continue

        # Extract the numeric DRG code (strip leading text like "XXX - ")
        # Some datasets format as "470 - MAJOR HIP AND KNEE..."
        drg_code = raw_drg.split("-")[0].strip() if "-" in raw_drg else raw_drg.strip()
        # Remove non-numeric characters for the code
        drg_code_clean = "".join(c for c in drg_code if c.isdigit())
        if not drg_code_clean:
            continue

        # Store description
        if drg_code_clean not in drg_desc_map:
            desc = _clean(row.get(col_drg_desc, "")) if col_drg_desc else ""
            if not desc and "-" in raw_drg:
                # Description might be embedded in the code column
                desc = raw_drg.split("-", 1)[1].strip()
            drg_desc_map[drg_code_clean] = desc

        discharges = _try_int(row.get(col_discharges)) if col_discharges else None
        avg_cvrd = _try_float(row.get(col_avg_cvrd_chrg)) if col_avg_cvrd_chrg else None
        avg_tot = _try_float(row.get(col_avg_tot_pymt)) if col_avg_tot_pymt else None
        avg_mdcr = _try_float(row.get(col_avg_mdcr_pymt)) if col_avg_mdcr_pymt else None

        ccn = _clean(row.get(col_ccn, "")) if col_ccn else ""
        prvdr_name = _clean(row.get(col_prvdr_name, "")) if col_prvdr_name else ""

        drg_rows[drg_code_clean].append({
            "ccn": ccn,
            "name": prvdr_name,
            "discharges": discharges,
            "avg_covered_charge": avg_cvrd,
            "avg_total_payment": avg_tot,
            "avg_medicare_payment": avg_mdcr,
        })

    print(f"  [build] Found {len(drg_rows):,} unique DRG codes")

    # Build one manifest per DRG
    for drg_code, hospital_entries in drg_rows.items():
        drg_description = drg_desc_map.get(drg_code, "")

        # Aggregate metrics
        total_discharges = 0
        hospital_count = 0
        weighted_mdcr_sum = 0.0
        weighted_mdcr_weight = 0
        weighted_tot_sum = 0.0
        weighted_tot_weight = 0
        weighted_cvrd_sum = 0.0
        weighted_cvrd_weight = 0
        mdcr_payments: list[float] = []

        for entry in hospital_entries:
            d = entry.get("discharges")
            if d is not None and d > 0:
                total_discharges += d
                hospital_count += 1

                mdcr = entry.get("avg_medicare_payment")
                if mdcr is not None:
                    weighted_mdcr_sum += mdcr * d
                    weighted_mdcr_weight += d
                    mdcr_payments.append(mdcr)

                tot = entry.get("avg_total_payment")
                if tot is not None:
                    weighted_tot_sum += tot * d
                    weighted_tot_weight += d

                cvrd = entry.get("avg_covered_charge")
                if cvrd is not None:
                    weighted_cvrd_sum += cvrd * d
                    weighted_cvrd_weight += d

        avg_medicare_payment = (
            round(weighted_mdcr_sum / weighted_mdcr_weight, 2)
            if weighted_mdcr_weight > 0 else None
        )
        avg_total_payment = (
            round(weighted_tot_sum / weighted_tot_weight, 2)
            if weighted_tot_weight > 0 else None
        )
        avg_covered_charge = (
            round(weighted_cvrd_sum / weighted_cvrd_weight, 2)
            if weighted_cvrd_weight > 0 else None
        )

        # Payment range statistics
        payment_range: dict[str, Any] = {}
        if mdcr_payments:
            mdcr_sorted = sorted(mdcr_payments)
            payment_range = {
                "min": round(mdcr_sorted[0], 2),
                "max": round(mdcr_sorted[-1], 2),
                "p25": round(mdcr_sorted[len(mdcr_sorted) // 4], 2) if len(mdcr_sorted) >= 4 else None,
                "median": round(statistics.median(mdcr_sorted), 2),
                "p75": round(mdcr_sorted[3 * len(mdcr_sorted) // 4], 2) if len(mdcr_sorted) >= 4 else None,
            }

        # Top 20 hospitals by discharge volume
        hospitals_with_discharges = [
            e for e in hospital_entries
            if e.get("discharges") is not None and e["discharges"] > 0
        ]
        hospitals_with_discharges.sort(key=lambda e: e["discharges"], reverse=True)
        top_hospitals = [
            {
                "ccn": e["ccn"],
                "name": e["name"],
                "discharges": e["discharges"],
                "avg_payment": e.get("avg_medicare_payment"),
            }
            for e in hospitals_with_discharges[:20]
        ]

        metrics: dict[str, Any] = {
            "total_discharges": {
                "value": total_discharges if total_discharges else None,
                "label": "Total Discharges",
            },
            "avg_medicare_payment": {
                "value": avg_medicare_payment,
                "label": "Avg Medicare Payment ($)",
            },
            "avg_total_payment": {
                "value": avg_total_payment,
                "label": "Avg Total Payment ($)",
            },
            "avg_covered_charge": {
                "value": avg_covered_charge,
                "label": "Avg Covered Charge ($)",
            },
            "hospital_count": {
                "value": hospital_count if hospital_count else None,
                "label": "Number of Hospitals",
            },
        }

        manifest: dict[str, Any] = {
            "entity_type": "drg",
            "drg_code": drg_code,
            "drg_description": drg_description,
            "data": {
                "inpatient": {
                    "metrics": metrics,
                    "top_hospitals": top_hospitals,
                    "payment_range": payment_range,
                },
            },
            "provenance": [
                build_provenance(
                    dataset_id="inpatient-by-drg",
                    dataset_name="Medicare Inpatient Hospitals by Provider and Service (DRG)",
                    vintage="2023",
                    download_date=download_date,
                    row_count=total_rows,
                    source_url="https://data.cms.gov/provider-summary-by-type-of-service/medicare-inpatient-hospitals/medicare-inpatient-hospitals-by-provider-and-service",
                ),
            ],
        }

        # Validate
        try:
            validate_drg_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for DRG {drg_code}: {e}")
            continue

        manifest_path = output_dir / f"{drg_code}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} DRG manifests ({errors} skipped)")
    return count
