"""
Tier-A enrichment module: Cost Reports, HAC Reduction, ACO County
Beneficiaries, SDOH, Chronic Conditions, and NADAC.

Contains seven enrichment functions that read downloaded CSVs and merge
derived metrics into existing entity manifests:

  1. enrich_hospitals_cost_report — hospital financial metrics from cost reports
  2. enrich_snfs_cost_report — SNF financial metrics from cost reports
  3. enrich_hospitals_hac — HAC Reduction Program scores
  4. enrich_acos_county_benes — ACO-to-county beneficiary cross-links
  5. enrich_counties_sdoh — CDC SDOH measures
  6. enrich_drugs_nadac — NADAC drug acquisition costs

Updated manifests are written back in place.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

from etl.normalize.keys import normalize_aco_id, normalize_ccn, normalize_fips
from etl.provenance.envelope import build_provenance


# ── Shared helpers ────────────────────────────────────────────────────


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def _try_float(val: str | None) -> float | None:
    if val is None:
        return None
    val = val.strip().replace(",", "").replace("$", "").replace("%", "")
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


def _read_csv(csv_path: Path) -> list[dict[str, str]]:
    """Read a CSV into a list of row dicts, handling encoding issues."""
    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _safe_divide(numerator: float | None, denominator: float | None) -> float | None:
    """Safe division returning None when inputs are missing or denominator is zero."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def _safe_sum(*parts: float | None) -> float | None:
    """Sum parts, treating None as 0 but requiring at least one non-None input."""
    present = [p for p in parts if p is not None]
    if not present:
        return None
    return sum(present)


def _clip_to_range(
    value: float | None,
    low: float,
    high: float,
) -> float | None:
    """Drop implausible values from a computed metric.

    CMS cost reports contain filings with data-entry errors and divisions
    by near-zero denominators. Rather than propagating an obvious outlier
    (e.g. a 9,000% margin, or a negative current ratio), we drop the
    metric so the page shows "—" instead of a misleading number.
    """
    if value is None:
        return None
    if value < low or value > high:
        return None
    return value


# ═══════════════════════════════════════════════════════════════════════
# 1. Hospital Cost Report
# ═══════════════════════════════════════════════════════════════════════


def _load_hospital_cost_report(
    csv_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load hospital cost report data keyed by CCN.

    Returns {ccn: {raw field values}}.
    """
    result: dict[str, dict[str, Any]] = {}
    rows = _read_csv(csv_path)
    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Provider CCN", "Provider_CCN", "CCN",
        "Facility ID", "provider_ccn",
    ])
    if col_ccn is None:
        print("    [warn] Could not find CCN column in hospital cost report")
        return result

    # Financial columns — use _find_column for flexible matching
    COL_MAP = {
        "net_income_service": [
            "Net Income from Service to Patients",
            "Net Income from service to patients",
            "net_income_from_service_to_patients",
        ],
        "net_patient_revenue": [
            "Net Patient Revenue", "net_patient_revenue",
        ],
        "net_income": [
            "Net Income", "net_income",
        ],
        "total_income": [
            "Total Income", "total_income",
        ],
        "total_other_income": [
            "Total Other Income", "total_other_income",
        ],
        "total_costs": [
            "Total Costs", "total_costs",
        ],
        "total_discharges": [
            "Total Discharges all", "Total Discharges",
            "total_discharges_all", "Total_Discharges",
        ],
        "total_days": [
            "Total Days all", "Total Days",
            "total_days_all",
        ],
        "total_bed_days": [
            "Total Bed Days Available", "total_bed_days_available",
            "Total Bed Days",
        ],
        "uncompensated_care": [
            "Cost of Uncompensated Care",
            "cost_of_uncompensated_care",
        ],
        "current_assets": [
            "Total Current Assets", "total_current_assets",
        ],
        "current_liabilities": [
            "Total Current Liabilities", "total_current_liabilities",
        ],
        "medicare_days": [
            "Total Days Title XVIII", "total_days_title_xviii",
            "Medicare Days",
        ],
        "cost_to_charge_ratio": [
            "Cost-to-Charge Ratio", "Cost to Charge Ratio",
            "cost_to_charge_ratio",
        ],
        "fte_employees": [
            "FTE - Employees on Payroll", "FTE Employees on Payroll",
            "fte_employees_on_payroll", "FTE",
        ],
        "number_of_beds": [
            "Number of Beds", "number_of_beds", "Beds",
        ],
        "total_assets": [
            "Total Assets", "total_assets",
        ],
        "total_liabilities": [
            "Total Liabilities", "total_liabilities",
        ],
        "fund_balance": [
            "Fund Balance", "fund_balance", "Total Fund Balance",
        ],
        "fiscal_year": [
            "Fiscal Year End Date", "Fiscal Year", "fiscal_year",
            "FYE", "Report Period",
        ],
    }

    resolved: dict[str, str | None] = {}
    for key, candidates in COL_MAP.items():
        resolved[key] = _find_column(sample, candidates)

    print(f"    [cost-report-hosp] CCN column: '{col_ccn}'")

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        vals: dict[str, Any] = {}
        for key, col in resolved.items():
            if col is not None:
                if key == "fiscal_year":
                    vals[key] = _clean(row.get(col, ""))
                else:
                    vals[key] = _try_float(row.get(col))

        result[ccn] = vals

    return result


def enrich_hospitals_cost_report(
    hospital_dir: Path,
    cost_report_csv: Path,
    download_date: date,
) -> int:
    """Enrich hospital manifests with cost-report financial metrics.

    Returns the number of manifests enriched.
    """
    if not hospital_dir.exists():
        print("  [enrich-cost-hosp] No hospital directory found")
        return 0

    print("  [enrich-cost-hosp] Loading hospital cost report data...")
    cr_data = _load_hospital_cost_report(cost_report_csv)
    print(f"  [enrich-cost-hosp] Cost report: {len(cr_data):,} hospitals")

    if not cr_data:
        return 0

    enriched = 0
    for manifest_path in sorted(hospital_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ccn = manifest.get("ccn", "")
        if ccn not in cr_data:
            continue

        vals = cr_data[ccn]
        metrics: dict[str, dict[str, Any]] = {}

        # Derived ratios. Each is clipped to a plausible range so bad
        # filings (divisions by near-zero, decimal misplacement, non-
        # operating entities on the same file) don't leak onto the page.
        op_margin = _clip_to_range(
            _safe_divide(vals.get("net_income_service"), vals.get("net_patient_revenue")),
            -1.0, 1.0,
        )
        if op_margin is not None:
            metrics["operating_margin"] = {
                "value": round(op_margin * 100, 2),
                "label": "Operating Margin (%)",
            }

        # Total margin = Net Income / Total Revenue, where Total Revenue
        # is Net Patient Revenue + Total Other Income. The previous
        # implementation used the "Total Income" column as denominator,
        # which is CMS's bottom-line (≈ Net Income) for most filers,
        # yielding a meaningless 100% ratio on the majority of rows.
        total_rev = _safe_sum(
            vals.get("net_patient_revenue"),
            vals.get("total_other_income"),
        )
        tot_margin = _clip_to_range(
            _safe_divide(vals.get("net_income"), total_rev),
            -1.0, 1.0,
        )
        if tot_margin is not None:
            metrics["total_margin"] = {
                "value": round(tot_margin * 100, 2),
                "label": "Total Margin (%)",
            }

        cpd = _clip_to_range(
            _safe_divide(vals.get("total_costs"), vals.get("total_discharges")),
            100.0, 1_000_000.0,
        )
        if cpd is not None:
            metrics["cost_per_discharge"] = {
                "value": round(cpd, 0),
                "label": "Cost per Discharge ($)",
            }

        occ = _clip_to_range(
            _safe_divide(vals.get("total_days"), vals.get("total_bed_days")),
            0.0, 1.0,
        )
        if occ is not None:
            metrics["occupancy_rate"] = {
                "value": round(occ * 100, 2),
                "label": "Occupancy Rate (%)",
            }

        unc = _clip_to_range(
            _safe_divide(vals.get("uncompensated_care"), vals.get("total_costs")),
            0.0, 1.0,
        )
        if unc is not None:
            metrics["uncompensated_care_pct"] = {
                "value": round(unc * 100, 2),
                "label": "Uncompensated Care (%)",
            }

        cr = _clip_to_range(
            _safe_divide(vals.get("current_assets"), vals.get("current_liabilities")),
            0.0, 50.0,
        )
        if cr is not None:
            metrics["current_ratio"] = {
                "value": round(cr, 2),
                "label": "Current Ratio",
            }

        mds = _clip_to_range(
            _safe_divide(vals.get("medicare_days"), vals.get("total_days")),
            0.0, 1.0,
        )
        if mds is not None:
            metrics["medicare_day_share"] = {
                "value": round(mds * 100, 2),
                "label": "Medicare Day Share (%)",
            }

        # Direct columns. CCR must be in (0, 1]; a non-zero filing of
        # exactly 0 or a value > 1 is a known bad-row signal.
        ccr = _clip_to_range(vals.get("cost_to_charge_ratio"), 0.001, 1.0)
        if ccr is not None:
            metrics["cost_to_charge_ratio"] = {
                "value": round(ccr, 2),
                "label": "Cost-to-Charge Ratio",
            }

        epb = _clip_to_range(
            _safe_divide(vals.get("fte_employees"), vals.get("number_of_beds")),
            0.1, 50.0,
        )
        if epb is not None:
            metrics["employees_per_bed"] = {
                "value": round(epb, 2),
                "label": "Employees per Bed",
            }

        for key, label in [
            ("net_patient_revenue", "Net Patient Revenue ($)"),
            ("net_income", "Net Income ($)"),
            ("total_costs", "Total Costs ($)"),
            ("total_assets", "Total Assets ($)"),
            ("total_liabilities", "Total Liabilities ($)"),
            ("fund_balance", "Fund Balance ($)"),
        ]:
            v = vals.get(key)
            if v is not None:
                metrics[key] = {"value": round(v, 0), "label": label}

        if not metrics:
            continue

        # Extract fiscal year from the data
        fiscal_year = vals.get("fiscal_year", "")
        if fiscal_year and len(fiscal_year) >= 4:
            # Try to extract the year from date strings like "12/31/2023"
            match = re.search(r"(20\d{2})", str(fiscal_year))
            fiscal_year = match.group(1) if match else str(fiscal_year)[:4]
        else:
            fiscal_year = "2023"

        manifest.setdefault("data", {})["cost_report"] = {
            "fiscal_year": fiscal_year,
            "metrics": metrics,
        }

        # Provenance
        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "hosp-cost-report" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="hosp-cost-report",
                    dataset_name="Hospital Provider Cost Report",
                    vintage=fiscal_year,
                    download_date=download_date,
                    row_count=len(cr_data),
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    print(f"  [enrich-cost-hosp] Enriched {enriched:,} hospital manifests")
    return enriched


# ═══════════════════════════════════════════════════════════════════════
# 2. SNF Cost Report
# ═══════════════════════════════════════════════════════════════════════


def _load_snf_cost_report(
    csv_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load SNF cost report data keyed by CCN.

    Returns {ccn: {raw field values}}.
    """
    result: dict[str, dict[str, Any]] = {}
    rows = _read_csv(csv_path)
    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "Provider CCN", "Provider_CCN", "CCN",
        "Facility ID", "provider_ccn",
    ])
    if col_ccn is None:
        print("    [warn] Could not find CCN column in SNF cost report")
        return result

    COL_MAP = {
        "net_income_service": [
            "Net Income from service to patients",
            "Net Income from Service to Patients",
            "net_income_from_service_to_patients",
        ],
        "net_patient_revenue": [
            "Net Patient Revenue", "net_patient_revenue",
        ],
        "net_income": [
            "Net Income", "net_income",
        ],
        "total_income": [
            "Total Income", "total_income",
        ],
        "total_other_income": [
            "Total Other Income", "total_other_income",
        ],
        "total_costs": [
            "Total Costs", "total_costs",
        ],
        "total_days": [
            "Total Days Total", "Total Days",
            "total_days_total", "total_days",
        ],
        "total_bed_days": [
            "Total Bed Days Available", "total_bed_days_available",
        ],
        "medicare_days": [
            "Total Days Title XVIII", "total_days_title_xviii",
        ],
        "medicaid_days": [
            "Total Days Title XIX", "total_days_title_xix",
        ],
        "current_assets": [
            "Total Current Assets", "total_current_assets",
        ],
        "current_liabilities": [
            "Total current liabilities", "Total Current Liabilities",
            "total_current_liabilities",
        ],
        "total_assets": [
            "Total Assets", "total_assets",
        ],
        "total_liabilities": [
            "Total liabilities", "Total Liabilities",
            "total_liabilities",
        ],
        "fund_balance": [
            "Total fund balances", "Fund Balance",
            "total_fund_balances", "fund_balance",
        ],
        "fiscal_year": [
            "Fiscal Year End Date", "Fiscal Year", "fiscal_year",
            "FYE", "Report Period",
        ],
    }

    resolved: dict[str, str | None] = {}
    for key, candidates in COL_MAP.items():
        resolved[key] = _find_column(sample, candidates)

    print(f"    [cost-report-snf] CCN column: '{col_ccn}'")

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        vals: dict[str, Any] = {}
        for key, col in resolved.items():
            if col is not None:
                if key == "fiscal_year":
                    vals[key] = _clean(row.get(col, ""))
                else:
                    vals[key] = _try_float(row.get(col))

        result[ccn] = vals

    return result


def enrich_snfs_cost_report(
    snf_dir: Path,
    cost_report_csv: Path,
    download_date: date,
) -> int:
    """Enrich SNF manifests with cost-report financial metrics.

    Returns the number of manifests enriched.
    """
    if not snf_dir.exists():
        print("  [enrich-cost-snf] No SNF directory found")
        return 0

    print("  [enrich-cost-snf] Loading SNF cost report data...")
    cr_data = _load_snf_cost_report(cost_report_csv)
    print(f"  [enrich-cost-snf] Cost report: {len(cr_data):,} SNFs")

    if not cr_data:
        return 0

    enriched = 0
    for manifest_path in sorted(snf_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ccn = manifest.get("ccn", "")
        if ccn not in cr_data:
            continue

        vals = cr_data[ccn]
        metrics: dict[str, dict[str, Any]] = {}

        # Derived ratios — clipped to plausible ranges; see the matching
        # hospital block for rationale.
        op_margin = _clip_to_range(
            _safe_divide(vals.get("net_income_service"), vals.get("net_patient_revenue")),
            -1.0, 1.0,
        )
        if op_margin is not None:
            metrics["operating_margin"] = {
                "value": round(op_margin * 100, 2),
                "label": "Operating Margin (%)",
            }

        total_rev = _safe_sum(
            vals.get("net_patient_revenue"),
            vals.get("total_other_income"),
        )
        tot_margin = _clip_to_range(
            _safe_divide(vals.get("net_income"), total_rev),
            -1.0, 1.0,
        )
        if tot_margin is not None:
            metrics["total_margin"] = {
                "value": round(tot_margin * 100, 2),
                "label": "Total Margin (%)",
            }

        cprd = _clip_to_range(
            _safe_divide(vals.get("total_costs"), vals.get("total_days")),
            20.0, 10_000.0,
        )
        if cprd is not None:
            metrics["cost_per_resident_day"] = {
                "value": round(cprd, 0),
                "label": "Cost per Resident Day ($)",
            }

        occ = _clip_to_range(
            _safe_divide(vals.get("total_days"), vals.get("total_bed_days")),
            0.0, 1.0,
        )
        if occ is not None:
            metrics["occupancy_rate"] = {
                "value": round(occ * 100, 2),
                "label": "Occupancy Rate (%)",
            }

        mds = _clip_to_range(
            _safe_divide(vals.get("medicare_days"), vals.get("total_days")),
            0.0, 1.0,
        )
        if mds is not None:
            metrics["medicare_day_share"] = {
                "value": round(mds * 100, 2),
                "label": "Medicare Day Share (%)",
            }

        mcds = _clip_to_range(
            _safe_divide(vals.get("medicaid_days"), vals.get("total_days")),
            0.0, 1.0,
        )
        if mcds is not None:
            metrics["medicaid_day_share"] = {
                "value": round(mcds * 100, 2),
                "label": "Medicaid Day Share (%)",
            }

        cr = _clip_to_range(
            _safe_divide(vals.get("current_assets"), vals.get("current_liabilities")),
            0.0, 50.0,
        )
        if cr is not None:
            metrics["current_ratio"] = {
                "value": round(cr, 2),
                "label": "Current Ratio",
            }

        # Direct columns
        for key, label in [
            ("net_patient_revenue", "Net Patient Revenue ($)"),
            ("net_income", "Net Income ($)"),
            ("total_costs", "Total Costs ($)"),
            ("total_assets", "Total Assets ($)"),
            ("total_liabilities", "Total Liabilities ($)"),
            ("fund_balance", "Total Fund Balances ($)"),
        ]:
            v = vals.get(key)
            if v is not None:
                metrics[key] = {"value": round(v, 0), "label": label}

        if not metrics:
            continue

        fiscal_year = vals.get("fiscal_year", "")
        if fiscal_year and len(str(fiscal_year)) >= 4:
            match = re.search(r"(20\d{2})", str(fiscal_year))
            fiscal_year = match.group(1) if match else str(fiscal_year)[:4]
        else:
            fiscal_year = "2023"

        manifest.setdefault("data", {})["cost_report"] = {
            "fiscal_year": fiscal_year,
            "metrics": metrics,
        }

        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "snf-cost-report" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="snf-cost-report",
                    dataset_name="Skilled Nursing Facility Cost Report",
                    vintage=fiscal_year,
                    download_date=download_date,
                    row_count=len(cr_data),
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    print(f"  [enrich-cost-snf] Enriched {enriched:,} SNF manifests")
    return enriched


# ═══════════════════════════════════════════════════════════════════════
# 3. Hospital-Acquired Condition (HAC) Reduction Program
# ═══════════════════════════════════════════════════════════════════════


def _load_hac_data(
    csv_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load HAC Reduction Program data keyed by CCN.

    Returns {ccn: {payment_reduction, total_hac_score, measures, ...}}.
    """
    result: dict[str, dict[str, Any]] = {}
    rows = _read_csv(csv_path)
    if not rows:
        return result

    sample = rows[0]
    col_ccn = _find_column(sample, [
        "facility_id", "Facility ID", "Facility Id",
        "Hospital CCN", "CCN", "Provider Number",
    ])
    if col_ccn is None:
        print("    [warn] Could not find CCN column in HAC data")
        return result

    col_payment = _find_column(sample, [
        "payment_reduction", "Payment Reduction",
        "Payment_Reduction", "HAC Payment Reduction",
    ])
    col_total_score = _find_column(sample, [
        "total_hac_score", "Total HAC Score",
        "Total_HAC_Score", "Total Score",
    ])

    # Measure columns — SIR and weighted z-score for each
    MEASURE_COLS = {
        "psi_90": {
            "sir": ["psi_90_sir", "PSI_90_SIR", "PSI-90 SIR"],
            "w_z_score": [
                "psi_90_w_z_score", "PSI_90_W_Z_Score",
                "PSI-90 Weighted Z-Score",
            ],
        },
        "clabsi": {
            "sir": ["clabsi_sir", "CLABSI_SIR", "CLABSI SIR"],
            "w_z_score": [
                "clabsi_w_z_score", "CLABSI_W_Z_Score",
                "CLABSI Weighted Z-Score",
            ],
        },
        "cauti": {
            "sir": ["cauti_sir", "CAUTI_SIR", "CAUTI SIR"],
            "w_z_score": [
                "cauti_w_z_score", "CAUTI_W_Z_Score",
                "CAUTI Weighted Z-Score",
            ],
        },
        "ssi": {
            "sir": ["ssi_sir", "SSI_SIR", "SSI SIR"],
            "w_z_score": [
                "ssi_w_z_score", "SSI_W_Z_Score",
                "SSI Weighted Z-Score",
            ],
        },
        "cdi": {
            "sir": ["cdi_sir", "CDI_SIR", "CDI SIR", "C.diff SIR"],
            "w_z_score": [
                "cdi_w_z_score", "CDI_W_Z_Score",
                "CDI Weighted Z-Score", "C.diff Weighted Z-Score",
            ],
        },
        "mrsa": {
            "sir": ["mrsa_sir", "MRSA_SIR", "MRSA SIR"],
            "w_z_score": [
                "mrsa_w_z_score", "MRSA_W_Z_Score",
                "MRSA Weighted Z-Score",
            ],
        },
    }

    resolved_measures: dict[str, dict[str, str | None]] = {}
    for measure_key, sub_cols in MEASURE_COLS.items():
        resolved_measures[measure_key] = {
            "sir": _find_column(sample, sub_cols["sir"]),
            "w_z_score": _find_column(sample, sub_cols["w_z_score"]),
        }

    # Measurement period columns
    col_psi90_start = _find_column(sample, [
        "psi_90_start_date", "PSI-90 Start Date",
        "PSI_90_Measurement_Period_Start",
    ])
    col_psi90_end = _find_column(sample, [
        "psi_90_end_date", "PSI-90 End Date",
        "PSI_90_Measurement_Period_End",
    ])
    col_hai_start = _find_column(sample, [
        "hai_start_date", "HAI Start Date",
        "HAI_Measurement_Period_Start",
    ])
    col_hai_end = _find_column(sample, [
        "hai_end_date", "HAI End Date",
        "HAI_Measurement_Period_End",
    ])

    print(f"    [hac] CCN column: '{col_ccn}'")

    for row in rows:
        ccn = normalize_ccn(row.get(col_ccn, ""))
        if ccn is None:
            continue

        entry: dict[str, Any] = {}

        # Payment reduction flag
        if col_payment:
            pr_val = _clean(row.get(col_payment, "")).lower()
            entry["payment_reduction"] = pr_val in ("y", "yes", "1", "true")

        # Total HAC score
        if col_total_score:
            entry["total_hac_score"] = _try_float(row.get(col_total_score))

        # Individual measures
        measures: dict[str, dict[str, Any]] = {}
        for measure_key, cols in resolved_measures.items():
            measure_data: dict[str, Any] = {}
            if cols["sir"]:
                sir_val = _try_float(row.get(cols["sir"]))
                if sir_val is not None:
                    measure_data["sir"] = round(sir_val, 2)
            if cols["w_z_score"]:
                wz_val = _try_float(row.get(cols["w_z_score"]))
                if wz_val is not None:
                    measure_data["w_z_score"] = round(wz_val, 2)
            if measure_data:
                measures[measure_key] = measure_data

        if measures:
            entry["measures"] = measures

        # Measurement periods
        measurement_period: dict[str, dict[str, str]] = {}
        if col_psi90_start or col_psi90_end:
            psi_period: dict[str, str] = {}
            if col_psi90_start:
                psi_period["start"] = _clean(row.get(col_psi90_start, ""))
            if col_psi90_end:
                psi_period["end"] = _clean(row.get(col_psi90_end, ""))
            if any(psi_period.values()):
                measurement_period["psi_90"] = psi_period

        if col_hai_start or col_hai_end:
            hai_period: dict[str, str] = {}
            if col_hai_start:
                hai_period["start"] = _clean(row.get(col_hai_start, ""))
            if col_hai_end:
                hai_period["end"] = _clean(row.get(col_hai_end, ""))
            if any(hai_period.values()):
                measurement_period["hai"] = hai_period

        if measurement_period:
            entry["measurement_period"] = measurement_period

        if entry:
            result[ccn] = entry

    return result


def enrich_hospitals_hac(
    hospital_dir: Path,
    hac_csv: Path,
    download_date: date,
) -> int:
    """Enrich hospital manifests with HAC Reduction Program scores.

    Returns the number of manifests enriched.
    """
    if not hospital_dir.exists():
        print("  [enrich-hac] No hospital directory found")
        return 0

    print("  [enrich-hac] Loading HAC Reduction Program data...")
    hac_data = _load_hac_data(hac_csv)
    print(f"  [enrich-hac] HAC: {len(hac_data):,} hospitals")

    if not hac_data:
        return 0

    enriched = 0
    for manifest_path in sorted(hospital_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        ccn = manifest.get("ccn", "")
        if ccn not in hac_data:
            continue

        hac_entry = hac_data[ccn]
        hac_entry["fiscal_year"] = "2026"

        manifest.setdefault("data", {})["hac_reduction"] = hac_entry

        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "hac-reduction" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="hac-reduction",
                    dataset_name="Hospital-Acquired Condition (HAC) Reduction Program",
                    vintage="FY2026",
                    download_date=download_date,
                    row_count=len(hac_data),
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    print(f"  [enrich-hac] Enriched {enriched:,} hospital manifests")
    return enriched


# ═══════════════════════════════════════════════════════════════════════
# 4. ACO Assigned Beneficiaries by County
# ═══════════════════════════════════════════════════════════════════════


def _build_fips_lookup_from_counties(
    county_dir: Path,
) -> tuple[dict[tuple[str, str], str], dict[str, dict[str, Any]]]:
    """Build (state_upper, county_name_upper) -> FIPS and fips -> manifest info
    lookups from existing county manifests.

    Returns (name_to_fips, fips_to_info).
    """
    name_to_fips: dict[tuple[str, str], str] = {}
    fips_to_info: dict[str, dict[str, Any]] = {}

    if not county_dir.exists():
        return name_to_fips, fips_to_info

    for manifest_path in county_dir.glob("*.json"):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        state = manifest.get("state", "").strip().upper()
        county_name = manifest.get("county_name", "").strip().upper()
        fips = manifest.get("fips", "")

        if state and county_name and fips:
            name_to_fips[(state, county_name)] = fips
            fips_to_info[fips] = {
                "path": str(manifest_path),
                "county_name": manifest.get("county_name", ""),
                "state": manifest.get("state", ""),
            }
            # Also store without common suffixes
            for suffix in (
                " COUNTY", " PARISH", " BOROUGH", " CENSUS AREA",
                " MUNICIPALITY", " CITY AND BOROUGH", " CITY",
            ):
                if county_name.endswith(suffix):
                    name_to_fips[(state, county_name[: -len(suffix)])] = fips

    return name_to_fips, fips_to_info


def _load_aco_county_benes(
    csv_path: Path,
    name_to_fips: dict[tuple[str, str], str],
) -> dict[str, list[dict[str, Any]]]:
    """Load ACO Assigned Beneficiaries by County data grouped by ACO_ID.

    Uses State_Name + County_Name matching against county manifests to
    derive FIPS codes, since the CSV uses SSA codes that may not have a
    full crosswalk available.

    Returns {aco_id: [{fips, county_name, state, total_beneficiaries}]}.
    """
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows = _read_csv(csv_path)
    if not rows:
        return dict(result)

    sample = rows[0]

    col_aco = _find_column(sample, [
        "ACO_ID", "ACO ID", "ACO_Num", "aco_id",
    ])
    col_state_name = _find_column(sample, [
        "State_Name", "State Name", "state_name", "State",
    ])
    col_county_name = _find_column(sample, [
        "County_Name", "County Name", "county_name", "County",
    ])
    col_total_benes = _find_column(sample, [
        "Tot_Benes", "Total_Beneficiaries", "total_beneficiaries",
        "Total Beneficiaries", "Tot_AB",
    ])
    col_state_id = _find_column(sample, [
        "State_ID", "State ID", "state_id",
    ])
    col_county_id = _find_column(sample, [
        "County_ID", "County ID", "county_id",
    ])

    if col_aco is None:
        print("    [warn] Could not find ACO ID column in county bene data")
        return dict(result)

    print(f"    [aco-bene] ACO column: '{col_aco}', State: '{col_state_name}', "
          f"County: '{col_county_name}'")

    matched = 0
    unmatched = 0

    for row in rows:
        aco_id = normalize_aco_id(row.get(col_aco, ""))
        if aco_id is None:
            continue

        state_name = _clean(row.get(col_state_name, "")) if col_state_name else ""
        county_name = _clean(row.get(col_county_name, "")) if col_county_name else ""

        # Parse total beneficiaries — handle suppressed values
        raw_benes = _clean(row.get(col_total_benes, "")) if col_total_benes else ""
        if raw_benes in ("*", ".", ""):
            total_benes = None
        else:
            total_benes = _try_int(raw_benes)

        # Try to match FIPS via state+county name
        fips = None
        state_upper = state_name.upper()
        county_upper = county_name.upper()

        if state_upper and county_upper:
            fips = name_to_fips.get((state_upper, county_upper))
            if fips is None:
                # Try with/without "County" suffix
                for sfx in (" COUNTY", " PARISH", ""):
                    fips = name_to_fips.get((state_upper, county_upper + sfx))
                    if fips:
                        break
            if fips is None:
                for sfx in (" COUNTY", " PARISH", " BOROUGH"):
                    if county_upper.endswith(sfx):
                        fips = name_to_fips.get(
                            (state_upper, county_upper[: -len(sfx)])
                        )
                        if fips:
                            break

        if fips:
            matched += 1
        else:
            unmatched += 1

        entry: dict[str, Any] = {
            "county_name": county_name,
            "state": state_name,
            "total_beneficiaries": total_benes,
        }
        if fips:
            entry["fips"] = fips

        result[aco_id].append(entry)

    print(f"    [aco-bene] FIPS matched: {matched:,}, unmatched: {unmatched:,}")
    return dict(result)


def enrich_acos_county_benes(
    aco_dir: Path,
    county_dir: Path,
    bene_csv: Path,
    download_date: date,
) -> int:
    """Enrich ACO manifests with county-level beneficiary data and
    create bidirectional ACO-County cross-links.

    Returns the number of ACO manifests enriched.
    """
    if not aco_dir.exists():
        print("  [enrich-aco-bene] No ACO directory found")
        return 0

    print("  [enrich-aco-bene] Building FIPS lookup from county manifests...")
    name_to_fips, fips_to_info = _build_fips_lookup_from_counties(county_dir)
    print(f"  [enrich-aco-bene] FIPS lookup: {len(name_to_fips):,} name entries, "
          f"{len(fips_to_info):,} FIPS entries")

    print("  [enrich-aco-bene] Loading ACO county beneficiary data...")
    bene_data = _load_aco_county_benes(bene_csv, name_to_fips)
    print(f"  [enrich-aco-bene] Beneficiary data: {len(bene_data):,} ACOs")

    if not bene_data:
        return 0

    total_rows = sum(len(v) for v in bene_data.values())

    # Track county -> ACO links for reverse linking
    county_aco_links: dict[str, list[dict[str, Any]]] = defaultdict(list)

    enriched = 0
    for manifest_path in sorted(aco_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        aco_id = manifest.get("aco_id", "")
        aco_name = manifest.get("aco_name", "")
        if aco_id not in bene_data:
            continue

        county_entries = bene_data[aco_id]

        # Sort by total_beneficiaries descending (None sorts last)
        county_entries.sort(
            key=lambda x: x.get("total_beneficiaries") or 0, reverse=True
        )

        manifest.setdefault("data", {})["county_beneficiaries"] = county_entries

        # Update related county links — replace existing county links
        # with precise links from this data
        related = manifest.get("related", [])
        # Remove old county links
        related = [r for r in related if r.get("type") != "county"]

        # Add top 20 counties by beneficiary count
        county_link_count = 0
        for entry in county_entries:
            if county_link_count >= 20:
                break
            fips = entry.get("fips")
            if not fips:
                continue
            benes = entry.get("total_beneficiaries")
            context = (
                f"{benes:,} assigned beneficiaries" if benes is not None
                else "Assigned beneficiaries (suppressed)"
            )
            related.append({
                "type": "county",
                "id": fips,
                "name": f"{entry.get('county_name', '')}, {entry.get('state', '')}",
                "context": context,
            })
            county_link_count += 1

        manifest["related"] = related

        # Build reverse links: county -> ACO
        # Get the ACO quality score for context if available
        quality_score = None
        aco_data = manifest.get("data", {})
        # Try common ACO quality score fields
        for score_key in ("quality_score", "quality_performance_score"):
            if score_key in aco_data:
                quality_score = aco_data[score_key]
                break

        for entry in county_entries:
            fips = entry.get("fips")
            if not fips or fips not in fips_to_info:
                continue
            benes = entry.get("total_beneficiaries")
            context_parts = []
            if benes is not None:
                context_parts.append(f"{benes:,} beneficiaries assigned")
            if quality_score is not None:
                context_parts.append(f"quality score: {quality_score}")
            context = ", ".join(context_parts) if context_parts else "ACO link"

            county_aco_links[fips].append({
                "type": "aco",
                "id": aco_id,
                "name": aco_name,
                "context": context,
            })

        # Provenance
        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "aco-bene-county" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="aco-bene-county",
                    dataset_name="ACO Assigned Beneficiaries by County",
                    vintage="2023",
                    download_date=download_date,
                    row_count=total_rows,
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    # ── Write reverse links onto county manifests ─────────────────
    county_linked = 0
    if county_dir.exists():
        for fips, aco_links in county_aco_links.items():
            info = fips_to_info.get(fips)
            if not info:
                continue
            manifest_path = Path(info["path"])
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            related = manifest.get("related", [])
            existing_aco_ids = {
                r["id"] for r in related if r.get("type") == "aco"
            }

            added = False
            for link in aco_links:
                if link["id"] not in existing_aco_ids:
                    related.append(link)
                    added = True

            if added:
                manifest["related"] = related
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                county_linked += 1

    print(f"  [enrich-aco-bene] Linked {county_linked:,} counties to ACOs")
    print(f"  [enrich-aco-bene] Enriched {enriched:,} ACO manifests")
    return enriched


# ═══════════════════════════════════════════════════════════════════════
# 5. CDC Social Determinants of Health (SDOH)
# ═══════════════════════════════════════════════════════════════════════

# Map CDC SDOH MeasureIDs / Short_Question_Text fragments to our keys
_SDOH_MEASURE_MAP: dict[str, tuple[str, str, str]] = {
    # (our_key, label, domain)
    # Key patterns matched against MeasureID or Short_Question_Text (case-insensitive)
}

_SDOH_TEXT_PATTERNS: list[tuple[str, str, str, str]] = [
    # (pattern_fragment, our_key, label, domain)
    ("poverty", "POVERTY", "Below 150% FPL (%)", "Economic Stability"),
    ("below 150", "POVERTY", "Below 150% FPL (%)", "Economic Stability"),
    ("fpl", "POVERTY", "Below 150% FPL (%)", "Economic Stability"),
    ("unemploy", "UNEMPLOYMENT", "Unemployment (%)", "Economic Stability"),
    ("no high school", "NO_DIPLOMA", "No High School Diploma (%)", "Education"),
    ("no diploma", "NO_DIPLOMA", "No High School Diploma (%)", "Education"),
    ("less than high school", "NO_DIPLOMA", "No High School Diploma (%)", "Education"),
    ("broadband", "NO_BROADBAND", "No Broadband (%)", "Education"),
    ("internet", "NO_BROADBAND", "No Broadband (%)", "Education"),
    ("housing cost", "HOUSING_BURDEN", "Housing Cost Burden (%)", "Housing"),
    ("housing burden", "HOUSING_BURDEN", "Housing Cost Burden (%)", "Housing"),
    ("crowding", "CROWDING", "Crowded Housing (%)", "Housing"),
    ("crowded", "CROWDING", "Crowded Housing (%)", "Housing"),
    ("single parent", "SINGLE_PARENT", "Single-Parent Households (%)", "Housing"),
    ("single-parent", "SINGLE_PARENT", "Single-Parent Households (%)", "Housing"),
    ("minority", "MINORITY", "Racial/Ethnic Minority (%)", "Demographics"),
    ("racial", "MINORITY", "Racial/Ethnic Minority (%)", "Demographics"),
    ("age 65", "AGE_65_PLUS", "Age 65+ (%)", "Demographics"),
    ("65 and over", "AGE_65_PLUS", "Age 65+ (%)", "Demographics"),
    ("elderly", "AGE_65_PLUS", "Age 65+ (%)", "Demographics"),
]


def _classify_sdoh_measure(
    measure_id: str,
    measure_text: str,
) -> tuple[str, str, str] | None:
    """Classify an SDOH measure into our standard key.

    Returns (our_key, label, domain) or None if no match.
    """
    combined = f"{measure_id} {measure_text}".lower()

    for pattern, key, label, domain in _SDOH_TEXT_PATTERNS:
        if pattern in combined:
            return (key, label, domain)

    return None


def _load_sdoh_data(
    csv_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load CDC SDOH data grouped by FIPS.

    Returns {fips: {measures dict, year, total_population}}.
    """
    result: dict[str, dict[str, Any]] = {}
    rows = _read_csv(csv_path)
    if not rows:
        return result

    sample = rows[0]

    col_fips = _find_column(sample, [
        "LocationID", "locationid", "CountyFIPS", "FIPS",
        "Location ID", "location_id",
    ])
    col_measure_id = _find_column(sample, [
        "MeasureID", "Measure_ID", "measureid",
        "Measure ID",
    ])
    col_measure_text = _find_column(sample, [
        "Short_Question_Text", "short_question_text",
        "MeasureName", "Measure", "Description",
    ])
    col_value = _find_column(sample, [
        "Value", "Data_Value", "data_value",
        "DataValue", "Estimate",
    ])
    col_moe = _find_column(sample, [
        "MOE", "Margin_of_Error", "margin_of_error",
        "Low_Confidence_Limit",  # fallback
    ])
    col_year = _find_column(sample, [
        "Year", "year", "Data_Year", "ReportYear",
        "TimeFrame",
    ])
    col_pop = _find_column(sample, [
        "TotalPopulation", "Total_Population",
        "total_population", "totalpopulation",
    ])

    if col_fips is None:
        print("    [warn] Could not find FIPS column in SDOH data")
        return result

    print(f"    [sdoh] FIPS column: '{col_fips}', Measure: '{col_measure_id or col_measure_text}'")

    # First pass: group rows by FIPS
    fips_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        raw_fips = row.get(col_fips, "")
        fips = normalize_fips(raw_fips)
        if fips is None or len(fips) != 5:
            continue
        fips_rows[fips].append(row)

    # Second pass: classify measures for each FIPS
    for fips, county_rows in fips_rows.items():
        measures: dict[str, dict[str, Any]] = {}
        year_str = ""
        total_pop = None

        for row in county_rows:
            mid = _clean(row.get(col_measure_id, "")) if col_measure_id else ""
            mtext = _clean(row.get(col_measure_text, "")) if col_measure_text else ""

            classification = _classify_sdoh_measure(mid, mtext)
            if classification is None:
                continue

            our_key, label, domain = classification

            value = _try_float(row.get(col_value, "")) if col_value else None
            moe = _try_float(row.get(col_moe, "")) if col_moe else None

            if value is None:
                continue

            # Only store the first match for each key (avoid duplicates)
            if our_key not in measures:
                entry: dict[str, Any] = {
                    "value": round(value, 2),
                    "label": label,
                    "domain": domain,
                }
                if moe is not None:
                    entry["moe"] = round(moe, 2)
                measures[our_key] = entry

            if not year_str and col_year:
                year_str = _clean(row.get(col_year, ""))

            if total_pop is None and col_pop:
                total_pop = _try_float(row.get(col_pop, ""))

        if measures:
            entry_data: dict[str, Any] = {
                "year": year_str or "ACS 2017-2021",
                "measures": measures,
            }
            if total_pop is not None:
                entry_data["total_population"] = round(total_pop, 0)
            result[fips] = entry_data

    return result


def enrich_counties_sdoh(
    county_dir: Path,
    sdoh_csv: Path,
    download_date: date,
) -> int:
    """Enrich county manifests with CDC SDOH measures.

    Returns the number of manifests enriched.
    """
    if not county_dir.exists():
        print("  [enrich-sdoh] No county directory found")
        return 0

    print("  [enrich-sdoh] Loading CDC SDOH data...")
    sdoh_data = _load_sdoh_data(sdoh_csv)
    print(f"  [enrich-sdoh] SDOH: {len(sdoh_data):,} counties with measures")

    if not sdoh_data:
        return 0

    enriched = 0
    for manifest_path in sorted(county_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        fips = manifest.get("fips", "")
        if fips not in sdoh_data:
            continue

        manifest.setdefault("data", {})["sdoh"] = sdoh_data[fips]

        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "cdc-sdoh" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="cdc-sdoh",
                    dataset_name="CDC SDOH Measures for County",
                    vintage=sdoh_data[fips].get("year", str(download_date.year)),
                    download_date=download_date,
                    row_count=len(sdoh_data),
                    source_url="https://data.cdc.gov/resource/i6u4-y3g4",
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    print(f"  [enrich-sdoh] Enriched {enriched:,} county manifests")
    return enriched


# ═══════════════════════════════════════════════════════════════════════
# 6. NADAC — National Average Drug Acquisition Cost
# ═══════════════════════════════════════════════════════════════════════


def _extract_generic_name(ndc_description: str) -> str | None:
    """Extract the generic drug name from an NDC description.

    NADAC descriptions look like "LISINOPRIL 10 MG TABLET" — extract
    the word(s) before dosage info (digits + units like MG, ML, MCG, etc.).

    Returns the uppercase generic name, or None if unparseable.
    """
    desc = ndc_description.strip().upper()
    if not desc:
        return None

    # Split on dosage patterns: number followed by unit
    # Common pattern: "DRUGNAME 10 MG TABLET" or "DRUG NAME HCL 0.5 MG/ML SOLUTION"
    match = re.match(
        r"^(.*?)\s+\d+(?:\.\d+)?\s*(?:MG|ML|MCG|MEQ|UNIT|GM|%|IU|MG/ML|MCG/ML)",
        desc,
    )
    if match:
        name = match.group(1).strip()
        if name:
            return name

    # Fallback: take everything before the first digit
    match = re.match(r"^([A-Z][A-Z\s/\-]+?)(?:\s+\d)", desc)
    if match:
        name = match.group(1).strip()
        if name:
            return name

    # Last resort: take the first word
    first_word = desc.split()[0] if desc.split() else None
    return first_word


def _load_nadac_data(
    csv_path: Path,
) -> dict[str, dict[str, Any]]:
    """Load NADAC data, aggregate by generic name.

    Returns {generic_name_upper: {nadac_per_unit, classification, otc,
    effective_date, matching_ndc_count}}.
    """
    rows = _read_csv(csv_path)
    if not rows:
        return {}

    sample = rows[0]

    col_ndc_desc = _find_column(sample, [
        "ndc_description", "NDC_Description", "NDC Description",
        "Drug Name", "drug_name",
    ])
    col_nadac = _find_column(sample, [
        "nadac_per_unit", "NADAC_Per_Unit", "NADAC Per Unit",
    ])
    col_class = _find_column(sample, [
        "classification_for_rate_setting",
        "Classification_for_Rate_Setting",
        "Classification for Rate Setting",
        "classification",
    ])
    col_otc = _find_column(sample, [
        "otc", "OTC", "Over_the_Counter",
    ])
    col_date = _find_column(sample, [
        "effective_date", "Effective_Date", "Effective Date",
        "as_of_date",
    ])

    if col_ndc_desc is None or col_nadac is None:
        print("    [warn] Could not find required columns in NADAC data")
        print(f"    [warn] Available columns: {list(sample.keys())[:15]}...")
        return {}

    print(f"    [nadac] Description: '{col_ndc_desc}', NADAC: '{col_nadac}'")

    # Group by extracted generic name
    name_nadacs: dict[str, list[float]] = defaultdict(list)
    name_classes: dict[str, list[str]] = defaultdict(list)
    name_otc: dict[str, list[str]] = defaultdict(list)
    name_dates: dict[str, str] = {}

    for row in rows:
        desc = _clean(row.get(col_ndc_desc, ""))
        generic = _extract_generic_name(desc)
        if generic is None:
            continue

        nadac_val = _try_float(row.get(col_nadac, ""))
        if nadac_val is not None:
            name_nadacs[generic].append(nadac_val)

        if col_class:
            cls = _clean(row.get(col_class, ""))
            if cls:
                name_classes[generic].append(cls)

        if col_otc:
            otc_val = _clean(row.get(col_otc, ""))
            if otc_val:
                name_otc[generic].append(otc_val)

        if col_date and generic not in name_dates:
            dt = _clean(row.get(col_date, ""))
            if dt:
                name_dates[generic] = dt

    # Aggregate
    result: dict[str, dict[str, Any]] = {}
    for generic in name_nadacs:
        vals = name_nadacs[generic]
        if not vals:
            continue

        med_nadac = round(median(vals), 2) if len(vals) == 1 else round(median(vals), 2)

        # Most common classification
        classes = name_classes.get(generic, [])
        if classes:
            counter = Counter(classes)
            classification = counter.most_common(1)[0][0]
        else:
            classification = None

        # OTC flag — True if any matching record has "Y"
        otc_vals = name_otc.get(generic, [])
        is_otc = any(v.upper() in ("Y", "YES", "1", "TRUE") for v in otc_vals)

        eff_date = name_dates.get(generic, "")

        result[generic] = {
            "nadac_per_unit": med_nadac,
            "classification": classification,
            "otc": is_otc,
            "effective_date": eff_date,
            "matching_ndc_count": len(vals),
        }

    return result


def enrich_drugs_nadac(
    drug_dir: Path,
    nadac_csv: Path,
    download_date: date,
) -> int:
    """Enrich drug manifests with NADAC acquisition cost data.

    Matches NADAC generic names to drug manifests by comparing the extracted
    generic name against the manifest's generic_name field.

    Returns the number of manifests enriched.
    """
    if not drug_dir.exists():
        print("  [enrich-nadac] No drug directory found")
        return 0

    print("  [enrich-nadac] Loading NADAC data...")
    nadac_data = _load_nadac_data(nadac_csv)
    print(f"  [enrich-nadac] NADAC: {len(nadac_data):,} generic names")

    if not nadac_data:
        return 0

    # Build a lookup of generic_name_upper -> NADAC entry
    # The NADAC keys are already uppercase from _extract_generic_name
    nadac_lookup = nadac_data

    enriched = 0
    for manifest_path in sorted(drug_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        generic_name = manifest.get("generic_name", "").upper()
        if not generic_name:
            continue

        # Try exact match first
        nadac_entry = nadac_lookup.get(generic_name)

        # Try partial match: NADAC name might be a prefix of the manifest name
        # or vice versa (e.g. "LISINOPRIL" matches "LISINOPRIL HCL")
        if nadac_entry is None:
            for nadac_name, entry in nadac_lookup.items():
                if generic_name.startswith(nadac_name) or nadac_name.startswith(generic_name):
                    nadac_entry = entry
                    break

        if nadac_entry is None:
            continue

        # Build the NADAC data section
        nadac_section: dict[str, Any] = {
            "nadac_per_unit": nadac_entry["nadac_per_unit"],
            "classification": nadac_entry.get("classification"),
            "otc": nadac_entry.get("otc", False),
            "effective_date": nadac_entry.get("effective_date", ""),
            "matching_ndc_count": nadac_entry.get("matching_ndc_count", 0),
        }

        # Compute markup ratio if Part D spending data is available
        partd_data = manifest.get("data", {}).get("partd_spending", {})
        metrics = partd_data.get("metrics", {})
        avg_spend_entry = metrics.get("avg_spend_per_dosage_unit", {})
        avg_spend = avg_spend_entry.get("value")

        nadac_unit = nadac_entry["nadac_per_unit"]
        if avg_spend is not None and nadac_unit and nadac_unit > 0:
            nadac_section["markup_ratio"] = round(avg_spend / nadac_unit, 2)

        manifest.setdefault("data", {})["nadac"] = nadac_section

        provenance_list = manifest.get("provenance", [])
        existing_ids = {p.get("dataset_id") for p in provenance_list}
        if "nadac" not in existing_ids:
            provenance_list.append(
                build_provenance(
                    dataset_id="nadac",
                    dataset_name="NADAC National Average Drug Acquisition Cost",
                    vintage=nadac_entry.get("effective_date", str(download_date.year)),
                    download_date=download_date,
                    row_count=len(nadac_data),
                    source_url="https://data.medicaid.gov/dataset/fbb83258-11c7-47f5-8b18-5f8e79f7e704",
                )
            )
            manifest["provenance"] = provenance_list

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        enriched += 1

    print(f"  [enrich-nadac] Enriched {enriched:,} drug manifests")
    return enriched
