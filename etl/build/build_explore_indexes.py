"""
Build lightweight JSON index files for explore pages.

Reads per-entity JSON manifests already in site_data/ and writes compact
array-of-arrays indexes to site_data/explore/. These are copied to
site/public/explore/ so the browser can fetch them at runtime for
virtual-scrolled explore tables.

Column order per entity (array index → field):
  hospitals:  [ccn, name, city, state, type, rating]
  snfs:       [ccn, name, city, state, beds, rating]
  counties:   [fips, name, state, spending, riskScore, readmission]
  acos:       [id, name, state, track, beneficiaries, qualityScore, savingsRate]
  drugs:      [drug_id, generic_name, brand_names, total_spending, total_claims]
  conditions: [condition_id, condition_name, category, national_avg_prevalence]
  drgs:       [drg_code, drg_description, total_discharges, avg_medicare_payment, hospital_count]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


def build_explore_indexes(site_data_dir: Path) -> dict[str, int]:
    """Build explore page indexes for all entity types.

    Returns a dict mapping entity name to row count.
    """
    explore_dir = site_data_dir / "explore"
    explore_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    counts["hospitals"] = _build_index(
        site_data_dir / "hospital",
        explore_dir / "hospitals.json",
        _extract_hospital,
    )
    counts["snfs"] = _build_index(
        site_data_dir / "snf",
        explore_dir / "snfs.json",
        _extract_snf,
    )
    counts["counties"] = _build_index(
        site_data_dir / "county",
        explore_dir / "counties.json",
        _extract_county,
    )
    counts["acos"] = _build_index(
        site_data_dir / "aco",
        explore_dir / "acos.json",
        _extract_aco,
    )
    counts["drugs"] = _build_index(
        site_data_dir / "drug",
        explore_dir / "drugs.json",
        _extract_drug,
    )
    counts["conditions"] = _build_index(
        site_data_dir / "condition",
        explore_dir / "conditions.json",
        _extract_condition,
    )
    counts["drgs"] = _build_index(
        site_data_dir / "drg",
        explore_dir / "drgs.json",
        _extract_drg,
    )

    return counts


def _build_index(
    entity_dir: Path,
    output_path: Path,
    extractor: Callable[[dict[str, Any]], list | None],
) -> int:
    """Read all manifests in entity_dir, extract summary rows, write compact JSON."""
    rows: list[list] = []
    if not entity_dir.exists():
        return 0
    for f in sorted(entity_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text(encoding="utf-8"))
            row = extractor(m)
            if row is not None:
                rows.append(row)
        except (json.JSONDecodeError, KeyError):
            continue

    # Sort by name (column 1) for default display order
    rows.sort(key=lambda r: (r[1] or "").lower())

    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(rows, out, separators=(",", ":"))
    print(f"  -> {output_path.name}: {len(rows):,} rows")
    return len(rows)


def _parse_rating(val: Any) -> int | None:
    """Parse a star rating value to int or None."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("1", "2", "3", "4", "5"):
        return int(s)
    return None


def _extract_hospital(m: dict) -> list | None:
    return [
        m["ccn"],
        m.get("facility_name", ""),
        m.get("city", ""),
        m.get("state", ""),
        m.get("hospital_type", ""),
        _parse_rating(m.get("hospital_overall_rating")),
    ]


def _extract_snf(m: dict) -> list | None:
    return [
        m["ccn"],
        m.get("provider_name", ""),
        m.get("city", ""),
        m.get("state", ""),
        m.get("beds"),
        _parse_rating(m.get("overall_rating")),
    ]


def _extract_county(m: dict) -> list | None:
    metrics = m.get("data", {}).get("geographic_variation", {}).get("metrics", {})
    return [
        m["fips"],
        m.get("county_name", ""),
        m.get("state", ""),
        metrics.get("TOT_MDCR_STDZD_PYMT_PC", {}).get("value"),
        metrics.get("BENE_AVG_RISK_SCRE", {}).get("value"),
        metrics.get("ACUTE_HOSP_READMSN_PCT", {}).get("value"),
    ]


def _extract_aco(m: dict) -> list | None:
    metrics = m.get("data", {}).get("mssp_performance", {}).get("metrics", {})
    return [
        m["aco_id"],
        m.get("aco_name", ""),
        m.get("state", ""),
        m.get("current_track", ""),
        metrics.get("N_AB", {}).get("value"),
        metrics.get("QualScore", {}).get("value"),
        metrics.get("Sav_rate", {}).get("value"),
    ]


def _extract_drug(m: dict) -> list | None:
    metrics = m.get("data", {}).get("partd_spending", {}).get("metrics", {})
    brand_names = m.get("brand_names", [])
    brand_str = ", ".join(brand_names[:5])
    if len(brand_names) > 5:
        brand_str += f" (+{len(brand_names) - 5})"
    return [
        m["drug_id"],
        m.get("generic_name", ""),
        brand_str,
        metrics.get("total_spending", {}).get("value"),
        metrics.get("total_claims", {}).get("value"),
    ]


def _extract_condition(m: dict) -> list | None:
    places = m.get("data", {}).get("places", {})
    return [
        m["condition_id"],
        m.get("condition_name", ""),
        m.get("category", ""),
        places.get("national_avg"),
    ]


def _extract_drg(m: dict) -> list | None:
    metrics = m.get("data", {}).get("inpatient", {}).get("metrics", {})
    return [
        m["drg_code"],
        m.get("drg_description", ""),
        metrics.get("total_discharges", {}).get("value"),
        metrics.get("avg_medicare_payment", {}).get("value"),
        metrics.get("hospital_count", {}).get("value"),
    ]
