"""
CareGraph ETL — Top-level orchestrator.

Runs the full ETL pipeline:
  1. Acquire raw datasets from data.cms.gov and data.cdc.gov
  2. Build base entity page manifests (hospitals, counties, SNFs, ACOs)
  3. Enrich entities (HRRP, HVBP, FIPS, CDC PLACES)
  4. Build cross-links between entities
  5. Build search index
  6. Copy editorial output to site_data/editorial/
  7. Write output index to site_data/

Usage:
    python etl/run.py
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from datetime import date
from pathlib import Path

# Ensure repo root is on the path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from etl.acquire.download import acquire_all, DATASETS
from etl.build.build_hospitals import build_hospitals
from etl.build.build_counties import build_counties
from etl.build.build_snfs import build_snfs
from etl.build.build_acos import build_acos
from etl.build.enrich_hospitals import enrich_hospitals
from etl.build.enrich_counties import enrich_counties
from etl.build.build_crosslinks import build_crosslinks
from etl.build.build_search_index import build_search_index
from etl.build.build_map_layers import build_map_layers
from etl.build.build_compare_data import build_compare_data


def main() -> None:
    start = time.time()
    print("=" * 60)
    print("CareGraph ETL — Phase 1–4 (M1 + M2 + M3 + M4)")
    print("=" * 60)

    raw_dir = REPO_ROOT / "data" / "raw"
    interim_dir = REPO_ROOT / "data" / "interim"
    site_data_dir = REPO_ROOT / "site_data"

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)
    site_data_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()

    # ── Step 1: Acquire all datasets ────────────────────────────────
    print("\n[Step 1] Acquiring raw datasets...")
    downloaded = acquire_all(raw_dir)
    for ds_id, path in downloaded.items():
        print(f"  {DATASETS[ds_id]['name']}: {path}")

    # ── Step 2: Build hospital manifests (base) ─────────────────────
    print("\n[Step 2] Building hospital page manifests...")
    hospital_out = site_data_dir / "hospital"
    hospital_csv = downloaded["xubh-q36u"]
    hospital_count = build_hospitals(hospital_csv, hospital_out, today)

    # ── Step 3: Build county manifests (base) ───────────────────────
    print("\n[Step 3] Building county page manifests...")
    county_out = site_data_dir / "county"
    county_csv = downloaded["geo-var-county"]
    county_count = build_counties(county_csv, county_out, today)

    # ── Step 4: Build SNF manifests ─────────────────────────────────
    print("\n[Step 4] Building SNF page manifests...")
    snf_out = site_data_dir / "snf"
    snf_csv = downloaded["nh-provider-info"]
    snf_count = build_snfs(snf_csv, snf_out, today)

    # ── Step 5: Build ACO manifests ─────────────────────────────────
    print("\n[Step 5] Building ACO page manifests...")
    aco_out = site_data_dir / "aco"
    aco_csv = downloaded["mssp-performance"]
    aco_count = build_acos(aco_csv, aco_out, today)

    # ── Step 6: Enrich hospitals (HRRP + HVBP + FIPS) ──────────────
    print("\n[Step 6] Enriching hospital manifests...")
    hrrp_csv = downloaded["hrrp"]
    hvbp_csv = downloaded["hvbp-tps"]
    hospital_enriched = enrich_hospitals(
        hospital_dir=hospital_out,
        county_dir=county_out,
        hrrp_csv_path=hrrp_csv,
        hvbp_csv_path=hvbp_csv,
        download_date=today,
    )

    # ── Step 7: Enrich counties (CDC PLACES) ────────────────────────
    print("\n[Step 7] Enriching county manifests with CDC PLACES...")
    places_csv = downloaded["cdc-places"]
    county_enriched = enrich_counties(
        county_dir=county_out,
        places_csv_path=places_csv,
        download_date=today,
    )

    # ── Step 8: Build cross-links ───────────────────────────────────
    print("\n[Step 8] Building cross-links between entities...")
    crosslink_counts = build_crosslinks(site_data_dir)

    # ── Step 9: Build search index ──────────────────────────────────
    print("\n[Step 9] Building search index...")
    search_count = build_search_index(site_data_dir)

    # ── Step 10: Copy editorial output to site_data ──────────────────
    print("\n[Step 10] Copying editorial output to site_data/editorial/...")
    editorial_src = REPO_ROOT / "etl" / "editorial" / "output"
    editorial_dst = site_data_dir / "editorial"
    editorial_dst.mkdir(parents=True, exist_ok=True)
    editorial_count = 0
    if editorial_src.exists():
        for md_file in editorial_src.glob("*.md"):
            shutil.copy2(md_file, editorial_dst / md_file.name)
            editorial_count += 1
    print(f"  -> Copied {editorial_count} editorial files to {editorial_dst}")

    # ── Step 11: Build map layers ──────────────────────────────────
    print("\n[Step 11] Building map layers for choropleth...")
    map_out = site_data_dir / "map"
    map_counts = build_map_layers(county_out, map_out)

    # ── Step 12: Build compare data ─────────────────────────────────
    print("\n[Step 12] Building compare summary data...")
    compare_out = site_data_dir / "compare"
    compare_counts = build_compare_data(site_data_dir, compare_out)

    # ── Step 13: Copy map layers and compare data to site/public/ ───
    print("\n[Step 13] Copying map layers and compare data to site/public/...")
    site_public = REPO_ROOT / "site" / "public"

    # Copy map layers
    map_public = site_public / "map"
    map_public.mkdir(parents=True, exist_ok=True)
    map_copied = 0
    for json_file in map_out.glob("*.json"):
        shutil.copy2(json_file, map_public / json_file.name)
        map_copied += 1
    print(f"  -> Copied {map_copied} map layer files to {map_public}")

    # Copy compare data
    compare_public = site_public / "compare"
    compare_public.mkdir(parents=True, exist_ok=True)
    compare_copied = 0
    for json_file in compare_out.glob("*.json"):
        shutil.copy2(json_file, compare_public / json_file.name)
        compare_copied += 1
    print(f"  -> Copied {compare_copied} compare data files to {compare_public}")

    # ── Step 14: Write manifest index ───────────────────────────────
    print("\n[Step 14] Writing manifest index...")
    index = {
        "generated": today.isoformat(),
        "entities": {
            "hospital": {
                "count": hospital_count,
                "path": "hospital/",
                "dataset": "Hospital General Information",
                "dataset_id": "xubh-q36u",
                "enriched_with": ["hrrp", "hvbp-tps"],
                "enriched_count": hospital_enriched,
            },
            "county": {
                "count": county_count,
                "path": "county/",
                "dataset": "Medicare Geographic Variation by County",
                "dataset_id": "geo-var-county",
                "enriched_with": ["cdc-places"],
                "enriched_count": county_enriched,
            },
            "snf": {
                "count": snf_count,
                "path": "snf/",
                "dataset": "Nursing Home Provider Info",
                "dataset_id": "nh-provider-info",
            },
            "aco": {
                "count": aco_count,
                "path": "aco/",
                "dataset": "MSSP ACO Performance PY2024",
                "dataset_id": "mssp-performance",
            },
        },
        "crosslinks": crosslink_counts,
        "search_index": {
            "count": search_count,
            "path": "search-index.json",
        },
        "map_layers": map_counts,
        "compare_data": compare_counts,
    }
    index_path = site_data_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"  -> {index_path}")

    # ── Summary ──────────────────────────────────────────────────────
    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"ETL complete in {elapsed:.1f}s")
    print(f"  Hospitals: {hospital_count:,} manifests ({hospital_enriched} enriched)")
    print(f"  Counties:  {county_count:,} manifests ({county_enriched} enriched)")
    print(f"  SNFs:      {snf_count:,} manifests")
    print(f"  ACOs:      {aco_count:,} manifests")
    print(f"  Search:    {search_count:,} index entries")
    print(f"  Editorial: {editorial_count} methodology pages")
    print(f"  Map layers: {sum(map_counts.values()):,} total entries across {len(map_counts)} layers")
    print(f"  Compare:   {sum(compare_counts.values()):,} total records across {len(compare_counts)} types")
    print(f"  Output:    {site_data_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
