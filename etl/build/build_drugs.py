"""
Build Drug entity page manifests from Medicare Part D Spending, Part B Spending,
and Part B Discarded Drug Units data.

A drug is identified by its generic name (Gnrc_Name from Part D).
Each drug entity aggregates brand names, spending metrics, and discarded unit data.

Output: site_data/drug/{drug_id}.json
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_drug_manifest


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


def _slugify(name: str) -> str:
    """Slugify a generic drug name: lowercase, replace non-alphanumeric with hyphens."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def _load_partd_data(
    csv_path: Path,
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Load Part D Drug Spending CSV grouped by generic name.

    Returns ({generic_name_upper: [row_dicts]}, total_row_count).
    """
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return dict(result), 0

    total_rows = len(rows)
    sample = rows[0]

    col_gnrc = _find_column(sample, [
        "Gnrc_Name", "gnrc_name", "Generic_Name", "Generic Name",
    ])
    col_brnd = _find_column(sample, [
        "Brnd_Name", "brnd_name", "Brand_Name", "Brand Name",
    ])
    col_mftr = _find_column(sample, [
        "Mftr_Name", "mftr_name", "Manufacturer_Name", "Manufacturer Name",
    ])
    col_tot_spndng = _find_column(sample, [
        "Tot_Spndng_2023", "Tot_Spndng",
    ])
    col_tot_dsg_unts = _find_column(sample, [
        "Tot_Dsg_Unts_2023", "Tot_Dsg_Unts",
    ])
    col_tot_clms = _find_column(sample, [
        "Tot_Clms_2023", "Tot_Clms",
    ])
    col_tot_benes = _find_column(sample, [
        "Tot_Benes_2023", "Tot_Benes",
    ])
    col_avg_spnd_dsg = _find_column(sample, [
        "Avg_Spnd_Per_Dsg_Unt_Wghtd_2023", "Avg_Spnd_Per_Dsg_Unt_Wghtd",
    ])
    col_avg_spnd_clm = _find_column(sample, [
        "Avg_Spnd_Per_Clm_2023", "Avg_Spnd_Per_Clm",
    ])
    col_outlier = _find_column(sample, [
        "Outlier_Flag_2023", "Outlier_Flag",
    ])

    if col_gnrc is None:
        print("  [build] ERROR: Could not find Gnrc_Name column in Part D data")
        print(f"  [build] Available columns: {list(sample.keys())[:20]}...")
        return dict(result), total_rows

    print(f"  [build] Part D columns: gnrc='{col_gnrc}', brnd='{col_brnd}'")

    for row in rows:
        gnrc = _clean(row.get(col_gnrc, "")).upper()
        if not gnrc:
            continue

        entry: dict[str, Any] = {}
        if col_brnd:
            entry["brand_name"] = _clean(row.get(col_brnd, ""))
        if col_mftr:
            entry["manufacturer"] = _clean(row.get(col_mftr, ""))
        if col_tot_spndng:
            entry["total_spending"] = _try_float(row.get(col_tot_spndng))
        if col_tot_dsg_unts:
            entry["total_dosage_units"] = _try_float(row.get(col_tot_dsg_unts))
        if col_tot_clms:
            entry["total_claims"] = _try_float(row.get(col_tot_clms))
        if col_tot_benes:
            entry["total_beneficiaries"] = _try_float(row.get(col_tot_benes))
        if col_avg_spnd_dsg:
            entry["avg_spend_per_dosage_unit"] = _try_float(row.get(col_avg_spnd_dsg))
        if col_avg_spnd_clm:
            entry["avg_spend_per_claim"] = _try_float(row.get(col_avg_spnd_clm))
        if col_outlier:
            entry["outlier_flag"] = _clean(row.get(col_outlier, ""))

        result[gnrc].append(entry)

    return dict(result), total_rows


def _load_partb_data(
    csv_path: Path,
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Load Part B Drug Spending CSV grouped by generic name.

    Returns ({generic_name_upper: [row_dicts]}, total_row_count).
    """
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return dict(result), 0

    total_rows = len(rows)
    sample = rows[0]

    col_gnrc = _find_column(sample, [
        "Gnrc_Name", "gnrc_name", "Generic_Name", "Generic Name",
    ])
    col_brnd = _find_column(sample, [
        "Brnd_Name", "brnd_name", "Brand_Name", "Brand Name",
    ])
    col_hcpcs = _find_column(sample, [
        "HCPCS_Cd", "hcpcs_cd", "HCPCS_Code", "HCPCS Code",
    ])
    col_hcpcs_desc = _find_column(sample, [
        "HCPCS_Desc", "hcpcs_desc", "HCPCS_Description", "HCPCS Description",
    ])
    col_tot_spndng = _find_column(sample, [
        "Tot_Spndng_2023", "Tot_Spndng",
    ])
    col_tot_clms = _find_column(sample, [
        "Tot_Clms_2023", "Tot_Clms",
    ])

    if col_gnrc is None:
        print("  [build] WARN: Could not find Gnrc_Name column in Part B data")
        print(f"  [build] Available columns: {list(sample.keys())[:20]}...")
        return dict(result), total_rows

    print(f"  [build] Part B columns: gnrc='{col_gnrc}', hcpcs='{col_hcpcs}'")

    for row in rows:
        gnrc = _clean(row.get(col_gnrc, "")).upper()
        if not gnrc:
            continue

        entry: dict[str, Any] = {}
        if col_brnd:
            entry["brand_name"] = _clean(row.get(col_brnd, ""))
        if col_hcpcs:
            entry["hcpcs_code"] = _clean(row.get(col_hcpcs, ""))
        if col_hcpcs_desc:
            entry["hcpcs_description"] = _clean(row.get(col_hcpcs_desc, ""))
        if col_tot_spndng:
            entry["total_spending"] = _try_float(row.get(col_tot_spndng))
        if col_tot_clms:
            entry["total_claims"] = _try_float(row.get(col_tot_clms))

        result[gnrc].append(entry)

    return dict(result), total_rows


def _load_discarded_data(
    csv_path: Path,
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Load Part B Discarded Drug Units CSV grouped by generic name.

    Returns ({generic_name_upper: [row_dicts]}, total_row_count).
    """
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return dict(result), 0

    total_rows = len(rows)
    sample = rows[0]

    col_gnrc = _find_column(sample, [
        "Gnrc_Name", "gnrc_name", "Generic_Name", "Generic Name",
    ])
    col_brnd = _find_column(sample, [
        "Brnd_Name", "brnd_name", "Brand_Name", "Brand Name",
    ])
    col_hcpcs = _find_column(sample, [
        "HCPCS_Cd", "hcpcs_cd", "HCPCS_Code", "HCPCS Code",
    ])
    col_alowd = _find_column(sample, [
        "Tot_Mdcr_Alowd_Amt", "tot_mdcr_alowd_amt",
    ])
    col_dscrd_amt = _find_column(sample, [
        "Tot_Mdcr_Alowd_Dscrd_Amt", "tot_mdcr_alowd_dscrd_amt",
    ])
    col_pct_dscrd = _find_column(sample, [
        "PCT_Dscrd_Units", "pct_dscrd_units", "Pct_Dscrd_Units",
    ])

    if col_gnrc is None:
        print("  [build] WARN: Could not find Gnrc_Name column in Discarded Units data")
        print(f"  [build] Available columns: {list(sample.keys())[:20]}...")
        return dict(result), total_rows

    print(f"  [build] Discarded columns: gnrc='{col_gnrc}', hcpcs='{col_hcpcs}'")

    for row in rows:
        gnrc = _clean(row.get(col_gnrc, "")).upper()
        if not gnrc:
            continue

        entry: dict[str, Any] = {}
        if col_brnd:
            entry["brand_name"] = _clean(row.get(col_brnd, ""))
        if col_hcpcs:
            entry["hcpcs_code"] = _clean(row.get(col_hcpcs, ""))
        if col_alowd:
            entry["total_allowed_amount"] = _try_float(row.get(col_alowd))
        if col_dscrd_amt:
            entry["total_discarded_amount"] = _try_float(row.get(col_dscrd_amt))
        if col_pct_dscrd:
            entry["pct_discarded_units"] = _try_float(row.get(col_pct_dscrd))

        result[gnrc].append(entry)

    return dict(result), total_rows


def _aggregate_partd(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Part D rows for a single generic drug."""
    total_spending = 0.0
    total_dosage_units = 0.0
    total_claims = 0.0
    total_benes = 0.0
    brand_names: set[str] = set()
    manufacturers: set[str] = set()
    outlier_flags: set[str] = set()
    weighted_spend_sum = 0.0
    weighted_spend_weight = 0.0

    for e in entries:
        brnd = e.get("brand_name", "")
        if brnd:
            brand_names.add(brnd)
        mftr = e.get("manufacturer", "")
        if mftr:
            manufacturers.add(mftr)

        sp = e.get("total_spending")
        if sp is not None:
            total_spending += sp
        du = e.get("total_dosage_units")
        if du is not None:
            total_dosage_units += du
        cl = e.get("total_claims")
        if cl is not None:
            total_claims += cl
        bn = e.get("total_beneficiaries")
        if bn is not None:
            total_benes += bn

        avg_dsg = e.get("avg_spend_per_dosage_unit")
        if avg_dsg is not None and du is not None and du > 0:
            weighted_spend_sum += avg_dsg * du
            weighted_spend_weight += du

        flag = e.get("outlier_flag", "")
        if flag:
            outlier_flags.add(flag)

    avg_spend_per_dosage_unit = (
        round(weighted_spend_sum / weighted_spend_weight, 2)
        if weighted_spend_weight > 0 else None
    )

    metrics: dict[str, Any] = {
        "total_spending": {
            "value": round(total_spending, 2) if total_spending else None,
            "label": "Total Part D Spending ($)",
        },
        "total_dosage_units": {
            "value": round(total_dosage_units, 0) if total_dosage_units else None,
            "label": "Total Dosage Units",
        },
        "total_claims": {
            "value": round(total_claims, 0) if total_claims else None,
            "label": "Total Claims",
        },
        "total_beneficiaries": {
            "value": round(total_benes, 0) if total_benes else None,
            "label": "Total Beneficiaries",
        },
        "avg_spend_per_dosage_unit": {
            "value": avg_spend_per_dosage_unit,
            "label": "Avg Spend per Dosage Unit ($)",
        },
    }

    return {
        "metrics": metrics,
        "brand_names": sorted(brand_names),
        "manufacturers": sorted(manufacturers),
        "outlier_flags": sorted(outlier_flags),
    }


def _aggregate_partb(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Part B rows for a single generic drug."""
    total_spending = 0.0
    total_claims = 0.0
    hcpcs_codes: list[dict[str, Any]] = []

    for e in entries:
        sp = e.get("total_spending")
        if sp is not None:
            total_spending += sp
        cl = e.get("total_claims")
        if cl is not None:
            total_claims += cl

        hcpcs = e.get("hcpcs_code", "")
        if hcpcs:
            hcpcs_codes.append({
                "code": hcpcs,
                "description": e.get("hcpcs_description", ""),
                "spending": sp,
                "claims": cl,
            })

    metrics: dict[str, Any] = {
        "total_spending": {
            "value": round(total_spending, 2) if total_spending else None,
            "label": "Total Part B Spending ($)",
        },
        "total_claims": {
            "value": round(total_claims, 0) if total_claims else None,
            "label": "Total Part B Claims",
        },
    }

    return {
        "metrics": metrics,
        "hcpcs_codes": hcpcs_codes,
    }


def _aggregate_discarded(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate discarded drug unit rows for a single generic drug."""
    total_allowed = 0.0
    total_discarded = 0.0
    details: list[dict[str, Any]] = []

    for e in entries:
        amt = e.get("total_allowed_amount")
        if amt is not None:
            total_allowed += amt
        dsc = e.get("total_discarded_amount")
        if dsc is not None:
            total_discarded += dsc

        hcpcs = e.get("hcpcs_code", "")
        if hcpcs:
            details.append({
                "code": hcpcs,
                "brand_name": e.get("brand_name", ""),
                "allowed_amount": amt,
                "discarded_amount": dsc,
                "pct_discarded": e.get("pct_discarded_units"),
            })

    pct_overall = (
        round(total_discarded / total_allowed * 100, 2)
        if total_allowed > 0 else None
    )

    metrics: dict[str, Any] = {
        "total_allowed_amount": {
            "value": round(total_allowed, 2) if total_allowed else None,
            "label": "Total Medicare Allowed Amount ($)",
        },
        "total_discarded_amount": {
            "value": round(total_discarded, 2) if total_discarded else None,
            "label": "Total Discarded Amount ($)",
        },
        "pct_discarded": {
            "value": pct_overall,
            "label": "Percent Discarded (%)",
        },
    }

    return {
        "metrics": metrics,
        "details": details,
    }


def build_drugs(
    partd_csv_path: Path,
    partb_csv_path: Path,
    discarded_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build drug page manifests from Part D, Part B, and Discarded Units CSVs.

    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    errors = 0

    # Load all three datasets
    print("  [build] Loading Part D drug spending data...")
    partd_data, partd_rows = _load_partd_data(partd_csv_path)
    print(f"  [build] Part D: {len(partd_data):,} generic drugs from {partd_rows:,} rows")

    print("  [build] Loading Part B drug spending data...")
    partb_data, partb_rows = _load_partb_data(partb_csv_path)
    print(f"  [build] Part B: {len(partb_data):,} generic drugs from {partb_rows:,} rows")

    print("  [build] Loading Part B discarded units data...")
    discarded_data, discarded_rows = _load_discarded_data(discarded_csv_path)
    print(f"  [build] Discarded: {len(discarded_data):,} generic drugs from {discarded_rows:,} rows")

    # Primary entity list comes from Part D
    for gnrc_name, partd_entries in partd_data.items():
        drug_id = _slugify(gnrc_name)
        if not drug_id:
            errors += 1
            continue

        # Aggregate Part D
        partd_agg = _aggregate_partd(partd_entries)

        # Build data section
        data: dict[str, Any] = {
            "partd_spending": {
                "metrics": partd_agg["metrics"],
                "raw": {
                    "manufacturers": partd_agg["manufacturers"],
                    "outlier_flags": partd_agg["outlier_flags"],
                },
            },
        }

        # Join Part B
        if gnrc_name in partb_data:
            partb_agg = _aggregate_partb(partb_data[gnrc_name])
            data["partb_spending"] = partb_agg

        # Join Discarded Units
        if gnrc_name in discarded_data:
            discarded_agg = _aggregate_discarded(discarded_data[gnrc_name])
            data["discarded_units"] = discarded_agg

        # Collect all brand names across all datasets
        all_brand_names: set[str] = set(partd_agg["brand_names"])
        if gnrc_name in partb_data:
            for e in partb_data[gnrc_name]:
                bn = e.get("brand_name", "")
                if bn:
                    all_brand_names.add(bn)
        if gnrc_name in discarded_data:
            for e in discarded_data[gnrc_name]:
                bn = e.get("brand_name", "")
                if bn:
                    all_brand_names.add(bn)

        # Build provenance
        provenance = [
            build_provenance(
                dataset_id="partd-drug-spending",
                dataset_name="Medicare Part D Spending by Drug",
                vintage="2023",
                download_date=download_date,
                row_count=partd_rows,
                source_url="https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-medicaid-opioid-prescribing-rates/medicare-part-d-spending-by-drug",
            ),
        ]
        if gnrc_name in partb_data:
            provenance.append(
                build_provenance(
                    dataset_id="partb-drug-spending",
                    dataset_name="Medicare Part B Spending by Drug",
                    vintage="2023",
                    download_date=download_date,
                    row_count=partb_rows,
                    source_url="https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-service-type-reports/medicare-part-b-spending-by-drug",
                ),
            )
        if gnrc_name in discarded_data:
            provenance.append(
                build_provenance(
                    dataset_id="partb-discarded-units",
                    dataset_name="Medicare Part B Discarded Drug Units",
                    vintage="2023",
                    download_date=download_date,
                    row_count=discarded_rows,
                    source_url="https://data.cms.gov/summary-statistics-on-use-and-payments/medicare-service-type-reports/medicare-part-b-discarded-drug-units",
                ),
            )

        manifest: dict[str, Any] = {
            "entity_type": "drug",
            "drug_id": drug_id,
            "generic_name": gnrc_name,
            "brand_names": sorted(all_brand_names),
            "data": data,
            "provenance": provenance,
        }

        # Validate
        try:
            validate_drug_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for drug {drug_id}: {e}")
            continue

        manifest_path = output_dir / f"{drug_id}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} drug manifests ({errors} skipped)")
    return count
