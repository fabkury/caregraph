"""
Build a unified search index across all entity types.

Iterates all manifests in site_data/{hospital,snf,county,aco}/ and produces
a single JSON array for client-side search at site_data/search-index.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _clean(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def _build_hospital_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for a hospital."""
    city = _clean(manifest.get("city"))
    state = _clean(manifest.get("state"))
    secondary = f"{city}, {state}" if city and state else city or state
    return {
        "id": f"hospital/{entity_id}",
        "type": "hospital",
        "name": _clean(manifest.get("facility_name")),
        "secondary": secondary,
        "identifier": entity_id,
    }


def _build_snf_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for a SNF."""
    city = _clean(manifest.get("city"))
    state = _clean(manifest.get("state"))
    secondary = f"{city}, {state}" if city and state else city or state
    return {
        "id": f"snf/{entity_id}",
        "type": "snf",
        "name": _clean(manifest.get("provider_name")),
        "secondary": secondary,
        "identifier": entity_id,
    }


def _build_county_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for a county."""
    county_name = _clean(manifest.get("county_name"))
    state = _clean(manifest.get("state"))
    secondary = state
    return {
        "id": f"county/{entity_id}",
        "type": "county",
        "name": county_name,
        "secondary": secondary,
        "identifier": entity_id,
    }


def _build_aco_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for an ACO."""
    state = _clean(manifest.get("state"))
    track = _clean(manifest.get("current_track"))
    secondary = f"{state} | {track}" if state and track else state or track
    return {
        "id": f"aco/{entity_id}",
        "type": "aco",
        "name": _clean(manifest.get("aco_name")),
        "secondary": secondary,
        "identifier": entity_id,
    }


def _build_drug_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for a drug."""
    brand_names = manifest.get("brand_names", [])
    secondary = ", ".join(brand_names[:5]) if brand_names else ""
    if len(brand_names) > 5:
        secondary += f" (+{len(brand_names) - 5} more)"
    return {
        "id": f"drug/{entity_id}",
        "type": "drug",
        "name": _clean(manifest.get("generic_name")),
        "secondary": secondary,
        "identifier": entity_id,
    }


def _build_condition_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for a condition."""
    category = _clean(manifest.get("category"))
    national_avg = manifest.get("data", {}).get("places", {}).get("national_avg")
    secondary = category
    if national_avg is not None:
        secondary = f"{category} | Avg: {national_avg}%" if category else f"Avg: {national_avg}%"
    return {
        "id": f"condition/{entity_id}",
        "type": "condition",
        "name": _clean(manifest.get("condition_name")),
        "secondary": secondary,
        "identifier": entity_id,
    }


def _build_drg_entry(manifest: dict[str, Any], entity_id: str) -> dict[str, str]:
    """Build a search index entry for a DRG."""
    metrics = manifest.get("data", {}).get("inpatient", {}).get("metrics", {})
    total_dschrgs = metrics.get("total_discharges", {}).get("value")
    secondary = f"DRG {entity_id}"
    if total_dschrgs is not None:
        secondary += f" | {int(total_dschrgs):,} discharges"
    return {
        "id": f"drg/{entity_id}",
        "type": "drg",
        "name": _clean(manifest.get("drg_description")),
        "secondary": secondary,
        "identifier": entity_id,
    }


# Map entity types to their builder functions and name fields
ENTITY_CONFIG = {
    "hospital": _build_hospital_entry,
    "snf": _build_snf_entry,
    "county": _build_county_entry,
    "aco": _build_aco_entry,
    "drug": _build_drug_entry,
    "condition": _build_condition_entry,
    "drg": _build_drg_entry,
}


def build_search_index(site_data_dir: Path) -> int:
    """Build a unified search index from all entity manifests.

    Writes site_data/search-index.json.
    Returns the total number of entries.
    """
    entries: list[dict[str, str]] = []

    for entity_type, builder_fn in ENTITY_CONFIG.items():
        entity_dir = site_data_dir / entity_type
        if not entity_dir.exists():
            continue

        for manifest_path in sorted(entity_dir.glob("*.json")):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            entity_id = manifest_path.stem
            entry = builder_fn(manifest, entity_id)

            # Skip entries with no name
            if entry.get("name"):
                entries.append(entry)

    # Sort by type then name for stable output
    entries.sort(key=lambda e: (e["type"], e["name"]))

    output_path = site_data_dir / "search-index.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)

    print(f"  [search] Built search index with {len(entries):,} entries -> {output_path}")
    return len(entries)
