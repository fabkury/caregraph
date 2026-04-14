"""
Build county page manifests from Medicare Geographic Variation data.

Reads the downloaded CSV, filters to county-level rows for the latest year,
normalizes FIPS codes, and emits one JSON manifest per county into
site_data/county/{FIPS}.json.

The label map below expands **every** column of the Medicare Geographic
Variation PUF that we surface on the site. Column naming follows a regular
pattern documented in the CMS data dictionary; rather than parse the PDF
we encode the expansion as TypeScript-friendly labels here and mirror the
groupings in `site/src/config/county-fields.ts`.
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


# ── Beneficiary profile ──────────────────────────────────────────────

BENEFICIARY_METRICS: dict[str, str] = {
    "BENES_TOTAL_CNT": "Total Medicare Beneficiaries",
    "BENES_FFS_CNT": "Fee-for-Service Beneficiaries",
    "BENES_MA_CNT": "Medicare Advantage Beneficiaries",
    "MA_PRTCPTN_RATE": "Medicare Advantage Participation Rate (%)",
    "BENE_AVG_AGE": "Average Beneficiary Age",
    "BENE_AVG_RISK_SCRE": "Average HCC Risk Score",
    "BENE_FEML_PCT": "Female Beneficiaries (%)",
    "BENE_MALE_PCT": "Male Beneficiaries (%)",
    "BENE_RACE_WHT_PCT": "White Beneficiaries (%)",
    "BENE_RACE_BLACK_PCT": "Black Beneficiaries (%)",
    "BENE_RACE_HSPNC_PCT": "Hispanic Beneficiaries (%)",
    "BENE_RACE_OTHR_PCT": "Other Race Beneficiaries (%)",
    "BENE_DUAL_PCT": "Dual Eligible (Medicare + Medicaid) (%)",
}


# ── Service settings for Spending + Utilization ──────────────────────
# (key, label, has_cvrd_stays, has_cvrd_days, visits_verb)
#
# Every service below has a consistent family of columns:
#   {KEY}_MDCR_PYMT_{AMT,PC,PCT,PER_USER}
#   {KEY}_MDCR_STDZD_PYMT_{AMT,PC,PCT,PER_USER}
#   BENES_{KEY}_{CNT,PCT}
#   {KEY}_{EVNTS,CVRD_STAYS,CVRD_DAYS,VISITS,EPISODES}_PER_1000_BENES

SERVICES: list[tuple[str, str, str]] = [
    # (col_prefix, label, unit_verb)
    ("IP",       "Inpatient",                    "stays"),
    ("OP",       "Outpatient Hospital",          "visits"),
    ("ASC",      "Ambulatory Surgery Center",    "events"),
    ("SNF",      "Skilled Nursing Facility",     "stays"),
    ("IRF",      "Inpatient Rehabilitation",     "stays"),
    ("LTCH",     "Long-Term Care Hospital",      "stays"),
    ("HH",       "Home Health",                  "episodes"),
    ("HOSPC",    "Hospice",                      "stays"),
    ("EM",       "Evaluation & Management",      "events"),
    ("PRCDRS",   "Procedures",                   "events"),
    ("TESTS",    "Tests",                        "events"),
    ("IMGNG",    "Imaging",                      "events"),
    ("DME",      "Durable Medical Equipment",    "events"),
    ("OP_DLYS",  "Part B Drugs (Outpatient)",    "visits"),
    ("FQHC_RHC", "FQHC / Rural Health Clinic",   "visits"),
    ("AMBLNC",   "Ambulance",                    "events"),
    ("TRTMNTS",  "Treatments",                   "events"),
]


# ── Top-line spending / utilization (not service-specific) ───────────

TOTAL_METRICS: dict[str, str] = {
    "TOT_MDCR_PYMT_AMT": "Total Medicare Payments (Actual, $)",
    "TOT_MDCR_STDZD_PYMT_AMT": "Total Medicare Payments (Standardized, $)",
    "TOT_MDCR_PYMT_PC": "Total Actual Per Capita Medicare Payment ($)",
    "TOT_MDCR_STDZD_PYMT_PC": "Total Standardized Per Capita Medicare Payment ($)",
    "ACUTE_HOSP_READMSN_CNT": "Acute Hospital Readmissions (count)",
    "ACUTE_HOSP_READMSN_PCT": "Acute Hospital Readmission Rate (%)",
    "BENES_ER_VISITS_CNT": "Beneficiaries with ER Visits",
    "ER_VISITS_PER_1000_BENES": "ER Visits per 1,000 Beneficiaries",
    "BENES_ER_VISITS_PCT": "Beneficiaries with ER Visits (%)",
    "TOT_PBPMT_RDCTN_AMT": "Total Per-Beneficiary Payment Reduction ($)",
    "TOT_PBPMT_RDCTN_PCC": "Per-Beneficiary Payment Reduction per Capita ($)",
    "PTB_OTHR_SRVCS_MDCR_PYMT_AMT": "Part B Other Services Payment ($)",
    "PTB_OTHR_SRVCS_MDCR_STDZD_PYMT": "Part B Other Services Standardized Payment ($)",
}


# ── Preventable admissions — AHRQ PQIs ───────────────────────────────
# Numerator: admissions for the ACSC; denominator: county adult pop
# CMS reports the rate as admissions per 100,000 population (age-stratified).

PQI_METRICS: dict[str, str] = {
    "PQI03_DBTS_AGE_LT_65": "Diabetes Short-Term Complications (<65, per 100k)",
    "PQI03_DBTS_AGE_65_74": "Diabetes Short-Term Complications (65-74, per 100k)",
    "PQI03_DBTS_AGE_GE_75": "Diabetes Short-Term Complications (75+, per 100k)",
    "PQI05_COPD_ASTHMA_AGE_40_64": "COPD / Asthma Older Adults (40-64, per 100k)",
    "PQI05_COPD_ASTHMA_AGE_65_74": "COPD / Asthma Older Adults (65-74, per 100k)",
    "PQI05_COPD_ASTHMA_AGE_GE_75": "COPD / Asthma Older Adults (75+, per 100k)",
    "PQI07_HYPRTNSN_AGE_LT_65": "Hypertension (<65, per 100k)",
    "PQI07_HYPRTNSN_AGE_65_74": "Hypertension (65-74, per 100k)",
    "PQI07_HYPRTNSN_AGE_GE_75": "Hypertension (75+, per 100k)",
    "PQI08_CHF_AGE_LT_65": "Heart Failure (<65, per 100k)",
    "PQI08_CHF_AGE_65_74": "Heart Failure (65-74, per 100k)",
    "PQI08_CHF_AGE_GE_75": "Heart Failure (75+, per 100k)",
    "PQI11_BCTRL_PNA_AGE_LT_65": "Bacterial Pneumonia (<65, per 100k)",
    "PQI11_BCTRL_PNA_AGE_65_74": "Bacterial Pneumonia (65-74, per 100k)",
    "PQI11_BCTRL_PNA_AGE_GE_75": "Bacterial Pneumonia (75+, per 100k)",
    "PQI12_UTI_AGE_LT_65": "Urinary Tract Infection (<65, per 100k)",
    "PQI12_UTI_AGE_65_74": "Urinary Tract Infection (65-74, per 100k)",
    "PQI12_UTI_AGE_GE_75": "Urinary Tract Infection (75+, per 100k)",
    "PQI15_ASTHMA_AGE_LT_40": "Asthma Younger Adults (<40, per 100k)",
    "PQI16_LWRXTRMTY_AMPUTN_AGE_LT_65": "Lower-Extremity Amputation (<65, per 100k)",
    "PQI16_LWRXTRMTY_AMPUTN_AGE_65_74": "Lower-Extremity Amputation (65-74, per 100k)",
    "PQI16_LWRXTRMTY_AMPUTN_AGE_GE_75": "Lower-Extremity Amputation (75+, per 100k)",
}


def _expand_service_metrics() -> dict[str, str]:
    """Expand the consistent family of columns for every service setting."""
    out: dict[str, str] = {}
    for prefix, label, verb in SERVICES:
        # Spending, actual
        out[f"{prefix}_MDCR_PYMT_AMT"]      = f"{label} Payments (Actual, $)"
        out[f"{prefix}_MDCR_PYMT_PCT"]      = f"{label} Share of Total Payments (%)"
        out[f"{prefix}_MDCR_PYMT_PC"]       = f"{label} Per Capita Payment (Actual, $)"
        out[f"{prefix}_MDCR_PYMT_PER_USER"] = f"{label} Payment per User (Actual, $)"
        # Spending, standardized
        out[f"{prefix}_MDCR_STDZD_PYMT_AMT"]      = f"{label} Payments (Standardized, $)"
        out[f"{prefix}_MDCR_STDZD_PYMT_PCT"]      = f"{label} Share of Total Standardized Payments (%)"
        out[f"{prefix}_MDCR_STDZD_PYMT_PC"]       = f"{label} Per Capita Payment (Standardized, $)"
        out[f"{prefix}_MDCR_STDZD_PYMT_PER_USER"] = f"{label} Payment per User (Standardized, $)"
        # Users
        out[f"BENES_{prefix}_CNT"] = f"{label} Users (count)"
        out[f"BENES_{prefix}_PCT"] = f"{label} Users (% of all benes)"
        # Utilization rate — the CMS column uses different verbs per service.
        # We emit the union of possibilities; missing columns simply won't
        # appear in the raw CSV and will be skipped.
        for denom in ("EVNTS", "CVRD_STAYS", "CVRD_DAYS", "VISITS", "EPISODES"):
            col = f"{prefix}_{denom}_PER_1000_BENES"
            # Only emit a nice label — downstream code only picks up columns
            # that actually exist in the row.
            if denom == "CVRD_STAYS":
                pretty = f"{label} Covered Stays per 1,000 Benes"
            elif denom == "CVRD_DAYS":
                pretty = f"{label} Covered Days per 1,000 Benes"
            elif denom == "EPISODES":
                pretty = f"{label} Episodes per 1,000 Benes"
            elif denom == "VISITS":
                pretty = f"{label} Visits per 1,000 Benes"
            else:
                pretty = f"{label} Events per 1,000 Benes"
            out[col] = pretty
    return out


SERVICE_METRICS = _expand_service_metrics()

# One combined map used by build_counties to extract numeric metrics.
ALL_METRICS: dict[str, str] = {
    **BENEFICIARY_METRICS,
    **TOTAL_METRICS,
    **SERVICE_METRICS,
    **PQI_METRICS,
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

        # Extract labelled numeric metrics. Only include columns that
        # actually exist in the source row (the CSV has ~247 columns but
        # a handful vary by vintage).
        metrics: dict[str, Any] = {}
        for col, label in ALL_METRICS.items():
            if col not in row:
                continue
            val = _try_float(row.get(col))
            if val is not None:
                metrics[col] = {
                    "value": val,
                    "label": label,
                }

        # Store all raw fields for provenance / CSV export
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
