"""
Build lightweight JSON lookup files for the choropleth map.

Reads county manifests and outputs:
  - site_data/map/spending.json      — standardized per capita spending
  - site_data/map/readmission.json   — readmission rate per county
  - site_data/map/risk_score.json    — average HCC risk score per county
  - site_data/map/diabetes.json      — diabetes prevalence from PLACES data
  - site_data/map/dual_eligible.json — dual-eligible percentage

Each file is a simple {fips: numeric_value} dictionary.
"""

from __future__ import annotations

import json
from pathlib import Path


def build_map_layers(county_dir: Path, map_out_dir: Path) -> dict[str, int]:
    """
    Read all county manifests and extract map layer data.

    Returns dict of layer_name -> count of counties with data.
    """
    map_out_dir.mkdir(parents=True, exist_ok=True)

    # Accumulators for each layer
    spending: dict[str, float] = {}
    readmission: dict[str, float] = {}
    risk_score: dict[str, float] = {}
    diabetes: dict[str, float] = {}
    dual_eligible: dict[str, float] = {}

    county_files = sorted(county_dir.glob("*.json"))
    for cf in county_files:
        try:
            manifest = json.loads(cf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        fips = manifest.get("fips", "")
        if not fips:
            continue

        # Geographic variation metrics
        metrics = (
            manifest.get("data", {})
            .get("geographic_variation", {})
            .get("metrics", {})
        )

        # Spending: TOT_MDCR_STDZD_PYMT_PC
        m = metrics.get("TOT_MDCR_STDZD_PYMT_PC")
        if m and m.get("value") is not None:
            spending[fips] = round(m["value"], 1)

        # Readmission: ACUTE_HOSP_READMSN_PCT
        m = metrics.get("ACUTE_HOSP_READMSN_PCT")
        if m and m.get("value") is not None:
            readmission[fips] = round(m["value"], 4)

        # Risk score: BENE_AVG_RISK_SCRE
        m = metrics.get("BENE_AVG_RISK_SCRE")
        if m and m.get("value") is not None:
            risk_score[fips] = round(m["value"], 3)

        # Dual eligible: BENE_DUAL_PCT
        m = metrics.get("BENE_DUAL_PCT")
        if m and m.get("value") is not None:
            dual_eligible[fips] = round(m["value"], 4)

        # PLACES data: diabetes
        places = manifest.get("data", {}).get("places", {})
        dm = places.get("DIABETES")
        if dm and dm.get("value") is not None:
            diabetes[fips] = round(dm["value"], 1)

    # Write each layer
    layers = {
        "spending": spending,
        "readmission": readmission,
        "risk_score": risk_score,
        "diabetes": diabetes,
        "dual_eligible": dual_eligible,
    }

    counts: dict[str, int] = {}
    for name, data in layers.items():
        out_path = map_out_dir / f"{name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
        counts[name] = len(data)
        print(f"  map/{name}.json: {len(data):,} counties")

    return counts
