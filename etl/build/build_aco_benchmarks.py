"""
Build MSSP-wide ACO benchmark statistics.

Reads all ACO manifests from site_data/aco/ and computes percentile
distributions (p10, p25, p50, p75, p90) for every numeric field in
the raw MSSP performance data.  Also computes MSSP-wide medians for
spending composition percentages.

Output: site_data/aco_benchmarks.json
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path


def _parse_float(val: str | None) -> float | None:
    if not val or val in ("*", "-", ".", "", " ", "N/A"):
        return None
    try:
        return float(val.replace(",", "").replace("$", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


def _percentiles(values: list[float]) -> dict[str, float] | None:
    if len(values) < 10:
        return None
    values.sort()
    n = len(values)
    return {
        "p10": values[int(n * 0.10)],
        "p25": values[int(n * 0.25)],
        "p50": values[int(n * 0.50)],
        "p75": values[int(n * 0.75)],
        "p90": values[int(n * 0.90)],
        "mean": statistics.mean(values),
        "n": n,
    }


def build_aco_benchmarks(aco_dir: Path, output_path: Path) -> int:
    """Build benchmark percentiles from all ACO manifests.

    Returns the number of fields with computed benchmarks.
    """
    # Load all manifests
    manifests = []
    for f in sorted(aco_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            manifests.append(json.load(fh))

    if not manifests:
        print("  WARNING: No ACO manifests found")
        return 0

    print(f"  Computing benchmarks across {len(manifests)} ACOs...")

    # Collect all numeric field values
    field_values: dict[str, list[float]] = {}
    for m in manifests:
        raw = m.get("data", {}).get("mssp_performance", {}).get("raw", {})
        for key, val in raw.items():
            num = _parse_float(val)
            if num is not None:
                field_values.setdefault(key, []).append(num)

    # Compute percentiles for each field
    field_benchmarks: dict[str, dict] = {}
    for key, vals in field_values.items():
        pcts = _percentiles(vals)
        if pcts:
            field_benchmarks[key] = pcts

    # Compute spending composition medians (% of total per-capita spending)
    spending_fields = [
        "CapAnn_INP_All", "CapAnn_HSP", "CapAnn_SNF",
        "CapAnn_OPD", "CapAnn_PB", "CapAnn_AmbPay",
        "CapAnn_HHA", "CapAnn_DME",
    ]
    composition_pcts: dict[str, list[float]] = {sf: [] for sf in spending_fields}
    for m in manifests:
        raw = m.get("data", {}).get("mssp_performance", {}).get("raw", {})
        total = sum(
            _parse_float(raw.get(sf)) or 0 for sf in spending_fields
        )
        if total <= 0:
            continue
        for sf in spending_fields:
            v = _parse_float(raw.get(sf))
            if v is not None:
                composition_pcts[sf].append(v / total * 100)

    spending_composition_medians: dict[str, float] = {}
    for sf, vals in composition_pcts.items():
        if len(vals) >= 10:
            vals.sort()
            spending_composition_medians[sf] = vals[len(vals) // 2]

    # Compute per-ACO percentile ranks for key metrics
    # (stored separately so the frontend can show "p42" badges)
    rank_fields = [
        "Sav_rate", "Per_Capita_Exp_TOTAL_PY", "QualScore", "N_AB",
        "ADM", "P_EDV_Vis", "P_EM_PCP_Vis", "P_EM_SP_Vis",
        "CapAnn_INP_All", "CapAnn_SNF", "CapAnn_OPD", "CapAnn_PB",
        "CAHPS_1", "CAHPS_2", "CAHPS_3", "CAHPS_4", "CAHPS_5",
        "CAHPS_6", "CAHPS_7", "CAHPS_8", "CAHPS_9", "CAHPS_11",
        "Measure_479", "Measure_484",
        "QualityID_318", "QualityID_110", "QualityID_226",
        "QualityID_113", "QualityID_112", "QualityID_438", "QualityID_370",
        "QualityID_001_WI", "QualityID_134_WI", "QualityID_236_WI",
        "Perc_Dual", "Perc_LTI",
        "CMS_HCC_RiskScore_AGND_PY", "CMS_HCC_RiskScore_DIS_PY",
        "CMS_HCC_RiskScore_AGDU_PY", "CMS_HCC_RiskScore_ESRD_PY",
        "UpdatedBnchmk", "HistBnchmk",
        "SNF_LOS", "SNF_PayperStay",
        "P_CT_VIS", "P_MRI_VIS", "P_Nurse_Vis", "P_FQHC_RHC_Vis",
    ]
    # For each ACO, compute percentile rank in each field
    aco_ranks: dict[str, dict[str, int]] = {}
    for rf in rank_fields:
        sorted_vals = sorted(field_values.get(rf, []))
        if len(sorted_vals) < 10:
            continue
        # Build value → percentile mapping
        val_to_pct: dict[float, int] = {}
        for i, v in enumerate(sorted_vals):
            val_to_pct[v] = int((i / (len(sorted_vals) - 1)) * 100)

        for m in manifests:
            aco_id = m.get("aco_id", "")
            raw = m.get("data", {}).get("mssp_performance", {}).get("raw", {})
            num = _parse_float(raw.get(rf))
            if num is None:
                continue
            # Find closest value in sorted list
            import bisect
            idx = bisect.bisect_left(sorted_vals, num)
            if idx >= len(sorted_vals):
                idx = len(sorted_vals) - 1
            pct = int((idx / max(len(sorted_vals) - 1, 1)) * 100)
            aco_ranks.setdefault(aco_id, {})[rf] = pct

    # Assemble output
    output = {
        "metadata": {
            "aco_count": len(manifests),
            "field_count": len(field_benchmarks),
            "rank_fields": rank_fields,
        },
        "benchmarks": field_benchmarks,
        "spending_composition_medians": spending_composition_medians,
        "aco_ranks": aco_ranks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"  -> {output_path} ({len(field_benchmarks)} fields benchmarked)")
    return len(field_benchmarks)
