"""
Build county page manifests from Medicare Geographic Variation data.

Reads the downloaded CSV, filters to county-level rows for the latest year,
normalizes FIPS codes, and emits one JSON manifest per county into
site_data/county/{FIPS}.json.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_fips
from etl.provenance.envelope import build_provenance
from etl.validate.schemas import validate_county_manifest

# Key metrics to extract. Column names are uppercase in the source CSV.
METRIC_LABELS = {
    "BENE_AVG_RISK_SCRE": "Average HCC Risk Score",
    "BENE_AVG_AGE": "Average Beneficiary Age",
    "BENE_FEML_PCT": "Female Beneficiaries (%)",
    "BENE_MALE_PCT": "Male Beneficiaries (%)",
    "BENE_RACE_WHT_PCT": "White Beneficiaries (%)",
    "BENE_RACE_BLACK_PCT": "Black Beneficiaries (%)",
    "BENE_RACE_HSPNC_PCT": "Hispanic Beneficiaries (%)",
    "BENE_DUAL_PCT": "Dual Eligible Beneficiaries (%)",
    "TOT_MDCR_STDZD_PYMT_PC": "Total Standardized Per Capita Medicare Payment ($)",
    "TOT_MDCR_PYMT_PC": "Total Actual Per Capita Medicare Payment ($)",
    "IP_MDCR_STDZD_PYMT_PC": "Inpatient Standardized Per Capita Payment ($)",
    "IP_MDCR_PYMT_PC": "Inpatient Actual Per Capita Payment ($)",
    "OP_MDCR_STDZD_PYMT_PC": "Outpatient Standardized Per Capita Payment ($)",
    "OP_MDCR_PYMT_PC": "Outpatient Actual Per Capita Payment ($)",
    "SNF_MDCR_STDZD_PYMT_PC": "SNF Standardized Per Capita Payment ($)",
    "SNF_MDCR_PYMT_PC": "SNF Actual Per Capita Payment ($)",
    "HH_MDCR_STDZD_PYMT_PC": "Home Health Standardized Per Capita Payment ($)",
    "HH_MDCR_PYMT_PC": "Home Health Actual Per Capita Payment ($)",
    "HOSPC_MDCR_STDZD_PYMT_PC": "Hospice Standardized Per Capita Payment ($)",
    "HOSPC_MDCR_PYMT_PC": "Hospice Actual Per Capita Payment ($)",
    "ACUTE_HOSP_READMSN_PCT": "Acute Hospital Readmission Rate (%)",
    "ER_VISITS_PER_1000_BENES": "ER Visits per 1,000 Beneficiaries",
    "MA_PRTCPTN_RATE": "Medicare Advantage Participation Rate (%)",
    "BENES_FFS_CNT": "FFS Beneficiary Count",
    "BENES_TOTAL_CNT": "Total Beneficiary Count",
}


def _try_float(val: str | None) -> float | None:
    if val is None or val.strip() in ("", "*", ".", "N/A", "Not Available"):
        return None
    try:
        return float(val.strip().replace(",", ""))
    except ValueError:
        return None


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def build_counties(
    raw_csv_path: Path,
    output_dir: Path,
    download_date: date,
) -> int:
    """Build county page manifests from Geographic Variation CSV.

    Filters to county-level rows (BENE_GEO_LVL == 'County') with
    BENE_AGE_LVL == 'All' for the latest available year.
    Returns the number of manifests written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(raw_csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)
    print(f"  [build] Processing {total_rows:,} total rows")

    # Filter to county-level, all-ages rows
    county_rows = [
        r for r in rows
        if r.get("BENE_GEO_LVL") == "County"
        and r.get("BENE_AGE_LVL") == "All"
    ]
    print(f"  [build] {len(county_rows):,} county-level 'All' age rows")

    if not county_rows:
        print("  [build] No county rows found")
        return 0

    # Find the latest year
    years = sorted(set(r.get("YEAR", "") for r in county_rows))
    latest_year = years[-1] if years else ""
    print(f"  [build] Available years: {', '.join(years)}. Using latest: {latest_year}")

    # Filter to latest year
    latest_rows = [r for r in county_rows if r.get("YEAR") == latest_year]
    print(f"  [build] {len(latest_rows):,} rows for year {latest_year}")

    count = 0
    errors = 0

    for row in latest_rows:
        raw_fips = row.get("BENE_GEO_CD", "")
        fips = normalize_fips(raw_fips)
        if fips is None or len(fips) != 5:
            errors += 1
            continue

        # Parse county name from BENE_GEO_DESC (format: "ST-County Name")
        geo_desc = _clean(row.get("BENE_GEO_DESC", ""))
        if "-" in geo_desc:
            state_abbr, county_name = geo_desc.split("-", 1)
            state = state_abbr.strip()
            county_name = county_name.strip()
        else:
            county_name = geo_desc
            state = ""

        # Extract metrics
        metrics: dict[str, Any] = {}
        for col, label in METRIC_LABELS.items():
            val = _try_float(row.get(col))
            if val is not None:
                metrics[col] = {
                    "value": val,
                    "label": label,
                }

        # Store all raw fields for table view
        raw_data = {k: _clean(v) for k, v in row.items() if k}

        manifest: dict[str, Any] = {
            "entity_type": "county",
            "fips": fips,
            "county_name": county_name,
            "state": state,
            "data": {
                "geographic_variation": {
                    "metrics": metrics,
                    "raw": raw_data,
                    "year": latest_year,
                },
            },
            "provenance": [
                build_provenance(
                    dataset_id="geo-var-county",
                    dataset_name="Medicare Geographic Variation by County",
                    vintage=latest_year,
                    download_date=download_date,
                    row_count=total_rows,
                ),
            ],
        }

        # Validate
        try:
            validate_county_manifest(manifest)
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"    [warn] Validation failed for FIPS {fips}: {e}")
            continue

        manifest_path = output_dir / f"{fips}.json"
        with open(manifest_path, "w", encoding="utf-8") as out:
            json.dump(manifest, out, indent=2)
        count += 1

    print(f"  [build] Wrote {count:,} county manifests ({errors} skipped)")
    return count
