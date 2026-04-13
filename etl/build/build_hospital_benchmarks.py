"""
Build national hospital benchmark statistics.

Reads all hospital manifests from site_data/hospital/ and computes percentile
distributions (p10, p25, p50, p75, p90) for every numeric metric across
the VBP, HRRP readmissions, cost report, and star rating data.

Also computes per-hospital percentile ranks so the frontend can display
"p42"-style badges.

Output: site_data/hospital_benchmarks.json
"""

from __future__ import annotations

import bisect
import json
import statistics
from pathlib import Path
from typing import Any


def _try_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace(",", "").replace("$", "").replace("%", "")
        if val in ("", "N/A", "Not Available", ".", "*", "-"):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    return None


def _percentiles(values: list[float]) -> dict[str, float] | None:
    """Compute p10/p25/p50/p75/p90/mean/n for a list of values."""
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
        "mean": round(statistics.mean(values), 4),
        "n": n,
    }


def build_hospital_benchmarks(hospital_dir: Path, output_path: Path) -> int:
    """Build benchmark percentiles from all hospital manifests.

    Returns the number of fields with computed benchmarks.
    """
    # Load all manifests
    manifests: list[dict[str, Any]] = []
    for f in sorted(hospital_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            manifests.append(json.load(fh))

    if not manifests:
        print("  WARNING: No hospital manifests found")
        return 0

    print(f"  Computing hospital benchmarks across {len(manifests)} hospitals...")

    # ── Collect values for each metric ────────────────────────────────

    # 1. VBP domain scores
    vbp_fields = [
        "total_performance_score",
        "clinical_outcomes_score",
        "safety_score",
        "person_community_score",
        "efficiency_score",
    ]
    vbp_values: dict[str, list[float]] = {f: [] for f in vbp_fields}

    # 2. HRRP readmission metrics (per-hospital aggregates)
    #    - worst_err: worst (highest) excess readmission ratio
    #    - avg_err: average ERR across reported conditions
    #    - Per-condition ERRs
    hrrp_conditions = [
        "READM-30-AMI-HRRP",
        "READM-30-HF-HRRP",
        "READM-30-PN-HRRP",
        "READM-30-COPD-HRRP",
        "READM-30-HIP-KNEE-HRRP",
        "READM-30-CABG-HRRP",
    ]
    hrrp_err_values: dict[str, list[float]] = {c: [] for c in hrrp_conditions}
    worst_err_values: list[float] = []
    avg_err_values: list[float] = []

    # 3. Star rating
    star_values: list[float] = []

    # 4. Cost report metrics (if available)
    cost_fields = [
        "operating_margin", "total_margin", "cost_per_discharge",
        "occupancy_rate", "uncompensated_care_pct", "current_ratio",
        "medicare_day_share",
    ]
    cost_values: dict[str, list[float]] = {f: [] for f in cost_fields}

    for m in manifests:
        data = m.get("data", {})

        # VBP
        vbp = data.get("vbp")
        if vbp and isinstance(vbp, dict):
            for field in vbp_fields:
                v = _try_float(vbp.get(field))
                if v is not None:
                    vbp_values[field].append(v)

        # HRRP
        readmissions = data.get("readmissions")
        if readmissions and isinstance(readmissions, dict):
            errs: list[float] = []
            for condition in hrrp_conditions:
                cdata = readmissions.get(condition, {})
                err = _try_float(cdata.get("excess_readmission_ratio") if isinstance(cdata, dict) else None)
                if err is not None:
                    hrrp_err_values[condition].append(err)
                    errs.append(err)
            if errs:
                worst_err_values.append(max(errs))
                avg_err_values.append(statistics.mean(errs))

        # Star rating
        rating = _try_float(m.get("hospital_overall_rating"))
        if rating is not None and 1 <= rating <= 5:
            star_values.append(rating)

        # Cost report
        cost = data.get("cost_report")
        if cost and isinstance(cost, dict):
            for field in cost_fields:
                v = _try_float(cost.get(field))
                if v is not None:
                    cost_values[field].append(v)

    # ── Compute percentiles ───────────────────────────────────────────

    benchmarks: dict[str, dict] = {}

    # VBP benchmarks
    for field in vbp_fields:
        pcts = _percentiles(vbp_values[field])
        if pcts:
            benchmarks[f"vbp.{field}"] = pcts

    # HRRP per-condition benchmarks
    for condition in hrrp_conditions:
        pcts = _percentiles(hrrp_err_values[condition])
        if pcts:
            benchmarks[f"hrrp.{condition}"] = pcts

    # HRRP aggregate benchmarks
    pcts = _percentiles(worst_err_values)
    if pcts:
        benchmarks["hrrp.worst_err"] = pcts
    pcts = _percentiles(avg_err_values)
    if pcts:
        benchmarks["hrrp.avg_err"] = pcts

    # Star rating
    pcts = _percentiles(star_values)
    if pcts:
        benchmarks["star_rating"] = pcts

    # Cost report
    for field in cost_fields:
        pcts = _percentiles(cost_values[field])
        if pcts:
            benchmarks[f"cost.{field}"] = pcts

    # ── Compute per-hospital percentile ranks ─────────────────────────

    # Fields to rank hospitals on
    rank_config: list[tuple[str, str]] = [
        # (benchmark_key, description)
        ("vbp.total_performance_score", "VBP TPS"),
        ("vbp.clinical_outcomes_score", "VBP Clinical Outcomes"),
        ("vbp.safety_score", "VBP Safety"),
        ("vbp.person_community_score", "VBP Person & Community"),
        ("vbp.efficiency_score", "VBP Efficiency"),
        ("hrrp.worst_err", "Worst Readmission Ratio"),
        ("hrrp.avg_err", "Average Readmission Ratio"),
        ("star_rating", "Star Rating"),
    ]
    # Add per-condition HRRP
    for c in hrrp_conditions:
        rank_config.append((f"hrrp.{c}", c))
    # Add cost fields
    for cf in cost_fields:
        rank_config.append((f"cost.{cf}", cf))

    # First, build sorted value lists for each metric
    def _extract_value(manifest: dict, key: str) -> float | None:
        """Extract a value from a manifest given a benchmark key."""
        data = manifest.get("data", {})
        if key.startswith("vbp."):
            field = key[4:]
            vbp = data.get("vbp", {})
            return _try_float(vbp.get(field)) if isinstance(vbp, dict) else None
        elif key.startswith("hrrp."):
            suffix = key[5:]
            readmissions = data.get("readmissions", {})
            if not isinstance(readmissions, dict):
                return None
            if suffix == "worst_err":
                errs = []
                for c in hrrp_conditions:
                    cd = readmissions.get(c, {})
                    err = _try_float(cd.get("excess_readmission_ratio") if isinstance(cd, dict) else None)
                    if err is not None:
                        errs.append(err)
                return max(errs) if errs else None
            elif suffix == "avg_err":
                errs = []
                for c in hrrp_conditions:
                    cd = readmissions.get(c, {})
                    err = _try_float(cd.get("excess_readmission_ratio") if isinstance(cd, dict) else None)
                    if err is not None:
                        errs.append(err)
                return statistics.mean(errs) if errs else None
            else:
                cd = readmissions.get(suffix, {})
                return _try_float(cd.get("excess_readmission_ratio") if isinstance(cd, dict) else None)
        elif key == "star_rating":
            return _try_float(manifest.get("hospital_overall_rating"))
        elif key.startswith("cost."):
            field = key[5:]
            cost = data.get("cost_report", {})
            return _try_float(cost.get(field)) if isinstance(cost, dict) else None
        return None

    hospital_ranks: dict[str, dict[str, int]] = {}

    for bkey, _desc in rank_config:
        if bkey not in benchmarks:
            continue

        # Build sorted list of all values for this metric
        sorted_vals: list[float] = []
        for m in manifests:
            v = _extract_value(m, bkey)
            if v is not None:
                sorted_vals.append(v)
        sorted_vals.sort()

        if len(sorted_vals) < 10:
            continue

        # Compute rank for each hospital
        for m in manifests:
            ccn = m.get("ccn", "")
            v = _extract_value(m, bkey)
            if v is None:
                continue
            idx = bisect.bisect_left(sorted_vals, v)
            if idx >= len(sorted_vals):
                idx = len(sorted_vals) - 1
            pct = int((idx / max(len(sorted_vals) - 1, 1)) * 100)
            hospital_ranks.setdefault(ccn, {})[bkey] = pct

    # ── Assemble output ───────────────────────────────────────────────

    output = {
        "metadata": {
            "hospital_count": len(manifests),
            "field_count": len(benchmarks),
            "rank_fields": [k for k, _ in rank_config if k in benchmarks],
        },
        "benchmarks": benchmarks,
        "hospital_ranks": hospital_ranks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"  -> {output_path} ({len(benchmarks)} fields benchmarked, "
          f"{len(hospital_ranks)} hospitals ranked)")
    return len(benchmarks)
