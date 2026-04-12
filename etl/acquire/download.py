"""
Acquire raw datasets from data.cms.gov.

CMS uses two API systems:
  - Provider Data API: /provider-data/api/1/datastore/query/{id}/0
  - CMS Data API: /data-api/v1/dataset/{uuid}/data

For reliability, we prefer direct CSV bulk download URLs when available,
falling back to paginated API calls.

Files are stored in data/raw/ with content-addressable filenames:
{dataset_id}_{YYYY-MM-DD}.csv. Re-running on the same day is a no-op.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx

# Datasets for M1 — each entry specifies the download strategy
DATASETS: dict[str, dict] = {
    "xubh-q36u": {
        "name": "Hospital General Information",
        "entity": "hospital",
        "api_type": "provider-data",
        # Direct CSV download URL (most reliable)
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1770163599/Hospital_General_Information.csv",
        # Paginated API fallback
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0",
    },
    "geo-var-county": {
        "name": "Medicare Geographic Variation by County",
        "entity": "county",
        "api_type": "data-api",
        # Direct CSV download URL
        "csv_url": "https://data.cms.gov/sites/default/files/2025-03/a40ac71d-9f80-4d99-92d2-fd149433d7d8/2014-2023%20Medicare%20Fee-for-Service%20Geographic%20Variation%20Public%20Use%20File.csv",
        # Paginated API fallback (UUID)
        "api_url": "https://data.cms.gov/data-api/v1/dataset/6219697b-8f6c-4164-bed4-cd9317c58ebc/data",
    },
}

# Page sizes for paginated API fallbacks
PROVIDER_DATA_PAGE_SIZE = 5000
DATA_API_PAGE_SIZE = 5000


def raw_path(dataset_id: str, download_date: date, raw_dir: Path) -> Path:
    """Content-addressable filename for a raw download."""
    return raw_dir / f"{dataset_id}_{download_date.isoformat()}.csv"


def _download_direct_csv(url: str, out_path: Path) -> int:
    """Download a CSV file directly. Returns row count."""
    print(f"    [direct] {url}")
    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=1024 * 256):
                    f.write(chunk)

    # Count rows (subtract header)
    with open(out_path, encoding="utf-8", errors="replace") as f:
        row_count = sum(1 for _ in f) - 1
    return row_count


def _download_provider_data_api(api_url: str, out_path: Path) -> int:
    """Download via the Provider Data paginated API. Returns row count."""
    import csv
    import io
    import json

    print(f"    [api] {api_url}")
    all_rows: list[dict] = []
    offset = 0

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        while True:
            params = {"limit": PROVIDER_DATA_PAGE_SIZE, "offset": offset}
            resp = client.get(api_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                break
            all_rows.extend(results)
            offset += PROVIDER_DATA_PAGE_SIZE
            if len(results) < PROVIDER_DATA_PAGE_SIZE:
                break

    if not all_rows:
        return 0

    # Write as CSV
    fieldnames = list(all_rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    return len(all_rows)


def _download_data_api(api_url: str, out_path: Path) -> int:
    """Download via the CMS Data API (JSON). Returns row count."""
    import csv
    import json

    print(f"    [api] {api_url}")
    all_rows: list[dict] = []
    offset = 0

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        while True:
            params = {"size": DATA_API_PAGE_SIZE, "offset": offset}
            resp = client.get(api_url, params=params)
            resp.raise_for_status()
            results = resp.json()
            if not isinstance(results, list) or not results:
                break
            all_rows.extend(results)
            offset += DATA_API_PAGE_SIZE
            if len(results) < DATA_API_PAGE_SIZE:
                break

    if not all_rows:
        return 0

    fieldnames = list(all_rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    return len(all_rows)


def download_dataset(
    dataset_id: str,
    raw_dir: Path,
    download_date: date | None = None,
) -> Path:
    """Download a dataset from data.cms.gov.

    Tries the direct CSV URL first, falls back to paginated API.
    Returns the path to the downloaded CSV file.
    Skips download if file already exists for today's date.
    """
    if download_date is None:
        download_date = date.today()

    ds = DATASETS[dataset_id]
    out_path = raw_path(dataset_id, download_date, raw_dir)

    if out_path.exists():
        print(f"  [skip] {out_path.name} already exists")
        return out_path

    print(f"  [download] {ds['name']}")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Try direct CSV download first
    csv_url = ds.get("csv_url")
    if csv_url:
        try:
            row_count = _download_direct_csv(csv_url, out_path)
            print(f"    -> {out_path.name} ({row_count:,} rows)")
            return out_path
        except Exception as e:
            print(f"    [warn] Direct CSV download failed: {e}")
            print("    [info] Falling back to paginated API...")

    # Fall back to paginated API
    api_url = ds.get("api_url")
    if api_url:
        api_type = ds.get("api_type", "provider-data")
        if api_type == "provider-data":
            row_count = _download_provider_data_api(api_url, out_path)
        else:
            row_count = _download_data_api(api_url, out_path)
        print(f"    -> {out_path.name} ({row_count:,} rows)")
        return out_path

    raise RuntimeError(f"No download method available for {dataset_id}")


def acquire_all(raw_dir: Path) -> dict[str, Path]:
    """Download all M1 datasets. Returns {dataset_id: file_path}."""
    results = {}
    for dataset_id in DATASETS:
        results[dataset_id] = download_dataset(dataset_id, raw_dir)
    return results
