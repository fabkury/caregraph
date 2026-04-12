"""
Build summary JSON files for the Compare view.

Reads all entity manifests and extracts flat summary records:
  - site_data/compare/hospitals.json
  - site_data/compare/snfs.json
  - site_data/compare/counties.json
  - site_data/compare/acos.json

Each file is an array of objects with key fields for comparison.
"""

from __future__ import annotations

import json
from pathlib import Path


def _safe_float(val: object) -> float | None:
    """Try to parse a float from various inputs."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip()
        if val in ("", "Not Available", "N/A"):
            return None
        try:
            return float(val)
        except ValueError:
            return None
    return None


def _safe_int(val: object) -> int | None:
    f = _safe_float(val)
    if f is None:
        return None
    return int(round(f))


def _build_hospitals(hospital_dir: Path) -> list[dict]:
    records = []
    for f in sorted(hospital_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        vbp = m.get("data", {}).get("vbp", {})

        # Get aggregate readmission ratio (average across conditions)
        readmissions = m.get("data", {}).get("readmissions", {})
        err_vals = []
        for measure_data in readmissions.values():
            ratio = measure_data.get("excess_readmission_ratio")
            if ratio is not None:
                err_vals.append(ratio)
        avg_err = round(sum(err_vals) / len(err_vals), 4) if err_vals else None

        records.append({
            "id": m.get("ccn", ""),
            "name": m.get("facility_name", ""),
            "state": m.get("state", ""),
            "city": m.get("city", ""),
            "type": m.get("hospital_type", ""),
            "rating": _safe_int(m.get("hospital_overall_rating")),
            "vbp_score": round(vbp["total_performance_score"], 1) if vbp.get("total_performance_score") is not None else None,
            "readmission_ratio": avg_err,
            "emergency": m.get("emergency_services", ""),
        })

    return records


def _build_snfs(snf_dir: Path) -> list[dict]:
    records = []
    for f in sorted(snf_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        records.append({
            "id": m.get("ccn", ""),
            "name": m.get("provider_name", ""),
            "state": m.get("state", ""),
            "city": m.get("city", ""),
            "beds": _safe_int(m.get("beds")),
            "rating": _safe_int(m.get("overall_rating")),
            "health_inspection": _safe_int(m.get("health_inspection_rating")),
            "qm_rating": _safe_int(m.get("qm_rating")),
            "staffing_rating": _safe_int(m.get("staffing_rating")),
            "ownership": m.get("ownership_type", ""),
        })

    return records


def _build_counties(county_dir: Path) -> list[dict]:
    records = []
    for f in sorted(county_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        metrics = (
            m.get("data", {})
            .get("geographic_variation", {})
            .get("metrics", {})
        )
        places = m.get("data", {}).get("places", {})

        def metric_val(key: str) -> float | None:
            v = metrics.get(key, {}).get("value")
            return round(v, 4) if v is not None else None

        records.append({
            "id": m.get("fips", ""),
            "name": f"{m.get('county_name', '')}, {m.get('state', '')}",
            "state": m.get("state", ""),
            "spending": metric_val("TOT_MDCR_STDZD_PYMT_PC"),
            "risk_score": metric_val("BENE_AVG_RISK_SCRE"),
            "readmission": metric_val("ACUTE_HOSP_READMSN_PCT"),
            "dual_pct": metric_val("BENE_DUAL_PCT"),
            "avg_age": metric_val("BENE_AVG_AGE"),
            "diabetes": places.get("DIABETES", {}).get("value"),
        })

    return records


def _build_acos(aco_dir: Path) -> list[dict]:
    records = []
    for f in sorted(aco_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        metrics = (
            m.get("data", {})
            .get("mssp_performance", {})
            .get("metrics", {})
        )

        def metric_val(key: str) -> float | None:
            v = metrics.get(key, {}).get("value")
            return round(v, 2) if v is not None else None

        records.append({
            "id": m.get("aco_id", ""),
            "name": m.get("aco_name", ""),
            "track": m.get("current_track", ""),
            "quality_score": metric_val("QualScore"),
            "savings_rate": metric_val("Sav_rate"),
            "beneficiaries": _safe_int(metrics.get("N_AB", {}).get("value")),
            "per_capita_exp": metric_val("Per_Capita_Exp_TOTAL_PY"),
            "gen_save_loss": metric_val("GenSaveLoss"),
        })

    return records


def build_compare_data(site_data_dir: Path, compare_out_dir: Path) -> dict[str, int]:
    """
    Build compare summary files for all entity types.

    Returns dict of entity_type -> record count.
    """
    compare_out_dir.mkdir(parents=True, exist_ok=True)

    builders = {
        "hospitals": (_build_hospitals, site_data_dir / "hospital"),
        "snfs": (_build_snfs, site_data_dir / "snf"),
        "counties": (_build_counties, site_data_dir / "county"),
        "acos": (_build_acos, site_data_dir / "aco"),
    }

    counts: dict[str, int] = {}
    for name, (builder_fn, entity_dir) in builders.items():
        if not entity_dir.exists():
            print(f"  compare/{name}.json: SKIPPED (no data)")
            counts[name] = 0
            continue

        records = builder_fn(entity_dir)
        out_path = compare_out_dir / f"{name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(records, f, separators=(",", ":"))
        counts[name] = len(records)
        print(f"  compare/{name}.json: {len(records):,} records")

    return counts
