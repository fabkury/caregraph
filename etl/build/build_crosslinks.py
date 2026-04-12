"""
Build cross-links between all entity types.

After all entities are built and enriched, this module creates bidirectional
relationship links so that each entity page can link to related entities.

Relationships:
  - Hospital <-> County (via FIPS)
  - SNF <-> County (via county name + state -> FIPS)
  - Hospital <-> SNF (co-located in same county)
  - ACO -> Counties (limited: by state for now)
  - County -> Hospitals, SNFs, Conditions
  - DRG -> Hospitals (top hospitals already in manifest)
  - Hospital -> DRGs (top DRGs by discharge volume)
  - Condition -> Counties (top counties by prevalence)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_manifests(entity_dir: Path) -> dict[str, dict[str, Any]]:
    """Load all JSON manifests from a directory. Returns {filename_stem: manifest}."""
    manifests: dict[str, dict[str, Any]] = {}
    if not entity_dir.exists():
        return manifests
    for path in sorted(entity_dir.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                manifests[path.stem] = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
    return manifests


def _save_manifest(entity_dir: Path, entity_id: str, manifest: dict[str, Any]) -> None:
    """Write a manifest back to disk."""
    path = entity_dir / f"{entity_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def _make_link(
    entity_type: str,
    entity_id: str,
    name: str,
    context: str = "",
) -> dict[str, str]:
    """Create a related-entity link entry."""
    link: dict[str, str] = {
        "type": entity_type,
        "id": entity_id,
        "name": name,
    }
    if context:
        link["context"] = context
    return link


def _hospital_context(manifest: dict[str, Any]) -> str:
    """One-line summary metric for a hospital link."""
    rating = manifest.get("hospital_overall_rating")
    if rating and rating not in ("Not Available", ""):
        return f"{rating}-star overall rating"
    return ""


def _snf_context(manifest: dict[str, Any]) -> str:
    """One-line summary metric for a SNF link."""
    rating = manifest.get("overall_rating")
    beds = manifest.get("beds")
    parts = []
    if rating:
        parts.append(f"{rating}-star")
    if beds:
        parts.append(f"{beds} beds")
    return ", ".join(parts)


def _county_context(manifest: dict[str, Any]) -> str:
    """One-line summary metric for a county link."""
    geo_data = manifest.get("data", {}).get("geographic_variation", {})
    metrics = geo_data.get("metrics", {})
    bene_count = metrics.get("BENES_TOTAL_CNT", {})
    if bene_count:
        val = bene_count.get("value")
        if val is not None:
            return f"{int(val):,} Medicare beneficiaries"
    return ""


def _aco_context(manifest: dict[str, Any]) -> str:
    """One-line summary metric for an ACO link."""
    perf = manifest.get("data", {}).get("mssp_performance", {})
    metrics = perf.get("metrics", {})
    qual = metrics.get("QualScore", {})
    if qual:
        val = qual.get("value")
        if val is not None:
            return f"Quality score: {val}"
    return ""


def _build_fips_from_county_name(
    state: str,
    county_name: str,
    county_manifests: dict[str, dict[str, Any]],
) -> str | None:
    """Derive FIPS from state + county name by scanning county manifests."""
    state_upper = state.strip().upper()
    county_upper = county_name.strip().upper()
    if not state_upper or not county_upper:
        return None

    for fips, manifest in county_manifests.items():
        m_state = manifest.get("state", "").strip().upper()
        m_county = manifest.get("county_name", "").strip().upper()
        if m_state == state_upper:
            if m_county == county_upper:
                return fips
            # Fuzzy: check if one contains the other
            if county_upper in m_county or m_county in county_upper:
                return fips

    return None


def _drg_context(manifest: dict[str, Any]) -> str:
    """One-line summary metric for a DRG link."""
    metrics = manifest.get("data", {}).get("inpatient", {}).get("metrics", {})
    discharges = metrics.get("total_discharges", {}).get("value")
    if discharges is not None:
        return f"{int(discharges):,} total discharges"
    return ""


def _condition_context(manifest: dict[str, Any]) -> str:
    """One-line summary metric for a condition link."""
    avg = manifest.get("data", {}).get("places", {}).get("national_avg")
    if avg is not None:
        return f"National avg: {avg}%"
    return ""


def build_crosslinks(
    site_data_dir: Path,
) -> dict[str, int]:
    """Build cross-links between all entity types.

    Reads all manifests, computes relationships, and writes updated manifests.
    Returns {entity_type: count_of_manifests_with_links}.
    """
    hospital_dir = site_data_dir / "hospital"
    snf_dir = site_data_dir / "snf"
    county_dir = site_data_dir / "county"
    aco_dir = site_data_dir / "aco"
    drg_dir = site_data_dir / "drg"
    condition_dir = site_data_dir / "condition"

    print("  [crosslinks] Loading all manifests...")
    hospitals = _load_manifests(hospital_dir)
    snfs = _load_manifests(snf_dir)
    counties = _load_manifests(county_dir)
    acos = _load_manifests(aco_dir)
    drgs = _load_manifests(drg_dir)
    conditions = _load_manifests(condition_dir)

    print(f"  [crosslinks] Loaded: {len(hospitals)} hospitals, {len(snfs)} SNFs, "
          f"{len(counties)} counties, {len(acos)} ACOs, "
          f"{len(drgs)} DRGs, {len(conditions)} conditions")

    # ── Build indexes ───────────────────────────────────────────────
    # FIPS -> list of hospital IDs
    fips_to_hospitals: dict[str, list[str]] = {}
    for h_id, h in hospitals.items():
        fips = h.get("fips")
        if fips:
            fips_to_hospitals.setdefault(fips, []).append(h_id)

    # FIPS -> list of SNF IDs (derive FIPS from county name lookup)
    snf_fips_map: dict[str, str] = {}  # snf_id -> fips
    fips_to_snfs: dict[str, list[str]] = {}
    for s_id, s in snfs.items():
        # Try the existing fips field first
        fips = s.get("fips")
        if not fips:
            # Derive from county name
            state = s.get("state", "")
            county_name = s.get("county_name", "")
            fips = _build_fips_from_county_name(state, county_name, counties)
        if fips:
            snf_fips_map[s_id] = fips
            fips_to_snfs.setdefault(fips, []).append(s_id)

    # State -> list of county FIPS (for ACO -> county links)
    state_to_fips: dict[str, list[str]] = {}
    for c_id, c in counties.items():
        state = c.get("state", "").strip().upper()
        if state:
            state_to_fips.setdefault(state, []).append(c_id)

    # ── Cross-link hospitals ────────────────────────────────────────
    hospital_linked = 0
    for h_id, h in hospitals.items():
        related: list[dict[str, str]] = []
        fips = h.get("fips")

        # Link to county
        if fips and fips in counties:
            county = counties[fips]
            related.append(_make_link(
                "county", fips,
                f"{county.get('county_name', '')}, {county.get('state', '')}",
                _county_context(county),
            ))

        # Link to SNFs in same county
        if fips and fips in fips_to_snfs:
            for s_id in fips_to_snfs[fips]:
                snf = snfs[s_id]
                related.append(_make_link(
                    "snf", s_id,
                    snf.get("provider_name", ""),
                    _snf_context(snf),
                ))

        if related:
            h["related"] = related
            _save_manifest(hospital_dir, h_id, h)
            hospital_linked += 1

    # ── Cross-link SNFs ─────────────────────────────────────────────
    snf_linked = 0
    for s_id, s in snfs.items():
        related: list[dict[str, str]] = []
        fips = snf_fips_map.get(s_id)

        # Store derived FIPS on the manifest
        if fips and not s.get("fips"):
            s["fips"] = fips

        # Link to county
        if fips and fips in counties:
            county = counties[fips]
            related.append(_make_link(
                "county", fips,
                f"{county.get('county_name', '')}, {county.get('state', '')}",
                _county_context(county),
            ))

        # Link to hospitals in same county
        if fips and fips in fips_to_hospitals:
            for h_id in fips_to_hospitals[fips]:
                hosp = hospitals[h_id]
                related.append(_make_link(
                    "hospital", h_id,
                    hosp.get("facility_name", ""),
                    _hospital_context(hosp),
                ))

        if related:
            s["related"] = related
            _save_manifest(snf_dir, s_id, s)
            snf_linked += 1

    # ── Cross-link counties ─────────────────────────────────────────
    county_linked = 0
    for c_id, c in counties.items():
        related: list[dict[str, str]] = []

        # Link to hospitals in this county
        if c_id in fips_to_hospitals:
            for h_id in fips_to_hospitals[c_id]:
                hosp = hospitals[h_id]
                related.append(_make_link(
                    "hospital", h_id,
                    hosp.get("facility_name", ""),
                    _hospital_context(hosp),
                ))

        # Link to SNFs in this county
        if c_id in fips_to_snfs:
            for s_id in fips_to_snfs[c_id]:
                snf = snfs[s_id]
                related.append(_make_link(
                    "snf", s_id,
                    snf.get("provider_name", ""),
                    _snf_context(snf),
                ))

        if related:
            c["related"] = related
            _save_manifest(county_dir, c_id, c)
            county_linked += 1

    # ── Cross-link ACOs ─────────────────────────────────────────────
    aco_linked = 0
    for a_id, a in acos.items():
        related: list[dict[str, str]] = []
        aco_state = a.get("state", "").strip().upper()

        # Link to counties in the same state (limited cross-link)
        if aco_state and aco_state in state_to_fips:
            county_fips_list = state_to_fips[aco_state]
            # Limit to first 20 counties to avoid massive link lists
            for c_fips in county_fips_list[:20]:
                if c_fips in counties:
                    county = counties[c_fips]
                    related.append(_make_link(
                        "county", c_fips,
                        f"{county.get('county_name', '')}, {county.get('state', '')}",
                        _county_context(county),
                    ))

        if related:
            a["related"] = related
            _save_manifest(aco_dir, a_id, a)
            aco_linked += 1

    # ── Cross-link DRGs ──────────────────────────────────────────────
    # DRG -> hospitals: already embedded via top_hospitals in the manifest.
    # Add explicit related links for navigation.
    drg_linked = 0
    for d_id, d in drgs.items():
        related: list[dict[str, str]] = []
        top_hospitals = d.get("data", {}).get("inpatient", {}).get("top_hospitals", [])
        for th in top_hospitals[:10]:
            ccn = th.get("ccn", "")
            if ccn and ccn in hospitals:
                hosp = hospitals[ccn]
                related.append(_make_link(
                    "hospital", ccn,
                    hosp.get("facility_name", ""),
                    _hospital_context(hosp),
                ))

        if related:
            d["related"] = related
            _save_manifest(drg_dir, d_id, d)
            drg_linked += 1

    # ── Cross-link hospitals with DRGs ─────────────────────────────
    # Build CCN -> list of (drg_code, discharges) from DRG manifests
    ccn_to_drgs: dict[str, list[tuple[str, int, str]]] = {}
    for d_id, d in drgs.items():
        desc = d.get("drg_description", "")
        top_hospitals = d.get("data", {}).get("inpatient", {}).get("top_hospitals", [])
        for th in top_hospitals:
            ccn = th.get("ccn", "")
            dschrgs = th.get("discharges", 0) or 0
            if ccn:
                ccn_to_drgs.setdefault(ccn, []).append((d_id, dschrgs, desc))

    for h_id, h in hospitals.items():
        drg_list = ccn_to_drgs.get(h_id, [])
        if not drg_list:
            continue
        # Sort by discharges descending, take top 10
        drg_list.sort(key=lambda x: x[1], reverse=True)
        drg_links: list[dict[str, str]] = []
        for drg_code, dschrgs, desc in drg_list[:10]:
            context = f"{dschrgs:,} discharges" if dschrgs else ""
            drg_links.append(_make_link("drg", drg_code, desc, context))

        existing = h.get("related", [])
        existing.extend(drg_links)
        h["related"] = existing
        _save_manifest(hospital_dir, h_id, h)

    # ── Cross-link conditions ──────────────────────────────────────
    # Condition -> counties: top counties by prevalence
    condition_linked = 0
    for cond_id, cond in conditions.items():
        related: list[dict[str, str]] = []
        top_counties = cond.get("data", {}).get("places", {}).get("top_counties", [])
        for tc in top_counties[:10]:
            fips = tc.get("fips", "")
            if fips and fips in counties:
                county = counties[fips]
                related.append(_make_link(
                    "county", fips,
                    f"{county.get('county_name', '')}, {county.get('state', '')}",
                    f"Prevalence: {tc.get('value', '')}%",
                ))

        if related:
            cond["related"] = related
            _save_manifest(condition_dir, cond_id, cond)
            condition_linked += 1

    # ── Cross-link counties with conditions ────────────────────────
    # Build FIPS -> list of (condition_id, value, name) from condition manifests
    fips_to_conditions: dict[str, list[tuple[str, float, str]]] = {}
    for cond_id, cond in conditions.items():
        cond_name = cond.get("condition_name", "")
        top_counties = cond.get("data", {}).get("places", {}).get("top_counties", [])
        bottom_counties = cond.get("data", {}).get("places", {}).get("bottom_counties", [])
        all_notable = top_counties + bottom_counties
        for tc in all_notable:
            fips = tc.get("fips", "")
            val = tc.get("value", 0.0)
            if fips:
                fips_to_conditions.setdefault(fips, []).append((cond_id, val, cond_name))

    for c_id, c in counties.items():
        cond_list = fips_to_conditions.get(c_id, [])
        if not cond_list:
            continue
        cond_links: list[dict[str, str]] = []
        for cond_id, val, cond_name in cond_list[:10]:
            cond_links.append(_make_link(
                "condition", cond_id, cond_name, f"Prevalence: {val}%",
            ))
        existing = c.get("related", [])
        existing.extend(cond_links)
        c["related"] = existing
        _save_manifest(county_dir, c_id, c)

    result = {
        "hospital": hospital_linked,
        "snf": snf_linked,
        "county": county_linked,
        "aco": aco_linked,
        "drg": drg_linked,
        "condition": condition_linked,
    }

    print(f"  [crosslinks] Linked: {hospital_linked} hospitals, {snf_linked} SNFs, "
          f"{county_linked} counties, {aco_linked} ACOs, "
          f"{drg_linked} DRGs, {condition_linked} conditions")
    return result
