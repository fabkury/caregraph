"""
Focused county-page rebuild.

Runs only the steps needed to rebuild county manifests after the county-page
redesign. Avoids re-downloading unrelated datasets.
"""

from __future__ import annotations

import shutil
import sys
import time
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from etl.build.build_counties import build_counties
from etl.build.enrich_counties import enrich_counties
from etl.build.enrich_tier_a import enrich_counties_sdoh
from etl.build.build_county_benchmarks import build_county_benchmarks
from etl.build.build_crosslinks import build_crosslinks
from etl.build.build_search_index import build_search_index
from etl.build.build_map_layers import build_map_layers
from etl.build.build_compare_data import build_compare_data
from etl.build.build_explore_indexes import build_explore_indexes


def main() -> None:
    start = time.time()
    today = date(2026, 4, 13)  # match existing raw downloads
    raw_dir = REPO_ROOT / "data" / "raw"
    site_data_dir = REPO_ROOT / "site_data"
    county_out = site_data_dir / "county"

    print("[1/8] Rebuilding county manifests from Geographic Variation...")
    count = build_counties(
        raw_dir / f"geo-var-county_{today.isoformat()}.csv",
        county_out,
        today,
    )
    print(f"  -> {count} counties")

    print("[2/8] Enriching counties with CDC PLACES...")
    enriched_places = enrich_counties(
        county_dir=county_out,
        places_csv_path=raw_dir / f"cdc-places_{today.isoformat()}.csv",
        download_date=today,
    )
    print(f"  -> {enriched_places} enriched with PLACES")

    print("[3/8] Enriching counties with CDC SDOH...")
    enriched_sdoh = enrich_counties_sdoh(
        county_dir=county_out,
        sdoh_csv=raw_dir / f"cdc-sdoh_{today.isoformat()}.csv",
        download_date=today,
    )
    print(f"  -> {enriched_sdoh} enriched with SDOH")

    print("[4/8] Building county benchmarks...")
    benchmarks_path = site_data_dir / "county_benchmarks.json"
    bench_count = build_county_benchmarks(county_out, benchmarks_path)
    print(f"  -> {bench_count} fields benchmarked")

    print("[5/8] Rebuilding crosslinks...")
    counts = build_crosslinks(site_data_dir)
    print(f"  -> crosslinks: {counts}")

    print("[6/8] Rebuilding search index...")
    search_count = build_search_index(site_data_dir)
    print(f"  -> {search_count} search entries")

    print("[7/8] Rebuilding map layers / compare / explore indexes...")
    map_out = site_data_dir / "map"
    map_counts = build_map_layers(county_out, map_out)
    compare_out = site_data_dir / "compare"
    compare_counts = build_compare_data(site_data_dir, compare_out)
    explore_counts = build_explore_indexes(site_data_dir)
    print(f"  -> map {map_counts}")
    print(f"  -> compare {compare_counts}")
    print(f"  -> explore {explore_counts}")

    print("[8/8] Copying regenerated files to site/public/...")
    site_public = REPO_ROOT / "site" / "public"
    for sub in ("map", "compare", "explore"):
        src = site_data_dir / sub
        dst = site_public / sub
        if not src.exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        copied = 0
        for jf in src.glob("*.json"):
            shutil.copy2(jf, dst / jf.name)
            copied += 1
        print(f"    -> {sub}: {copied} files")

    elapsed = time.time() - start
    print(f"Done in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
