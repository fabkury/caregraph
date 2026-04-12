"""
CareGraph ETL — Top-level orchestrator.

Runs the full ETL pipeline:
  1. Acquire raw datasets from data.cms.gov
  2. Build entity page manifests (normalize + validate + provenance)
  3. Write output to site_data/ for the Astro frontend build

Usage:
    python etl/run.py
"""

from __future__ import annotations

import json
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


def main() -> None:
    start = time.time()
    print("=" * 60)
    print("CareGraph ETL — M1 Skeleton")
    print("=" * 60)

    raw_dir = REPO_ROOT / "data" / "raw"
    interim_dir = REPO_ROOT / "data" / "interim"
    site_data_dir = REPO_ROOT / "site_data"

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    interim_dir.mkdir(parents=True, exist_ok=True)
    site_data_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()

    # ── Step 1: Acquire ──────────────────────────────────────────
    print("\n[Step 1] Acquiring raw datasets...")
    downloaded = acquire_all(raw_dir)
    for ds_id, path in downloaded.items():
        print(f"  {DATASETS[ds_id]['name']}: {path}")

    # ── Step 2: Build hospital manifests ─────────────────────────
    print("\n[Step 2] Building hospital page manifests...")
    hospital_out = site_data_dir / "hospital"
    hospital_csv = downloaded["xubh-q36u"]
    hospital_count = build_hospitals(hospital_csv, hospital_out, today)

    # ── Step 3: Build county manifests ───────────────────────────
    print("\n[Step 3] Building county page manifests...")
    county_out = site_data_dir / "county"
    county_csv = downloaded["geo-var-county"]
    county_count = build_counties(county_csv, county_out, today)

    # ── Step 4: Write manifest index ─────────────────────────────
    print("\n[Step 4] Writing manifest index...")
    index = {
        "generated": today.isoformat(),
        "entities": {
            "hospital": {
                "count": hospital_count,
                "path": "hospital/",
                "dataset": "Hospital General Information",
                "dataset_id": "xubh-q36u",
            },
            "county": {
                "count": county_count,
                "path": "county/",
                "dataset": "Medicare Geographic Variation by County",
                "dataset_id": "geo-var-county",
            },
        },
    }
    index_path = site_data_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"  -> {index_path}")

    # ── Summary ──────────────────────────────────────────────────
    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"ETL complete in {elapsed:.1f}s")
    print(f"  Hospitals: {hospital_count:,} manifests")
    print(f"  Counties:  {county_count:,} manifests")
    print(f"  Output:    {site_data_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
