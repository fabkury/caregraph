"""
Acquire raw datasets from data.cms.gov and data.cdc.gov.

CMS uses two API systems:
  - Provider Data API: /provider-data/api/1/datastore/query/{id}/0
  - CMS Data API: /data-api/v1/dataset/{uuid}/data

CDC PLACES uses the Socrata (SODA) API with $limit/$offset pagination.

For reliability, we prefer direct CSV bulk download URLs when available,
falling back to paginated API calls.

Files are stored in data/raw/ with content-addressable filenames:
{dataset_id}_{YYYY-MM-DD}.csv. Re-running on the same day is a no-op.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx

# Datasets — each entry specifies the download strategy
DATASETS: dict[str, dict] = {
    # ── M1 datasets ─────────────────────────────────────────────────
    "xubh-q36u": {
        "name": "Hospital General Information",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/893c372430d9d71a1c52737d01239d47_1770163599/Hospital_General_Information.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/xubh-q36u/0",
    },
    "geo-var-county": {
        "name": "Medicare Geographic Variation by County",
        "entity": "county",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-03/a40ac71d-9f80-4d99-92d2-fd149433d7d8/2014-2023%20Medicare%20Fee-for-Service%20Geographic%20Variation%20Public%20Use%20File.csv",
        "api_url": "https://data.cms.gov/data-api/v1/dataset/6219697b-8f6c-4164-bed4-cd9317c58ebc/data",
    },
    # ── M2 datasets ─────────────────────────────────────────────────
    "nh-provider-info": {
        "name": "Nursing Home Provider Info",
        "entity": "snf",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/3059e5643c76d35f1185eb1ee2f38d63_1773439550/NH_ProviderInfo_Mar2026.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0",
    },
    "nh-quality-mds": {
        "name": "SNF Quality Measures (MDS)",
        "entity": "snf",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/7e1ccbe085c113f331361dc24f7c82f7_1773439544/NH_QualityMsr_MDS_Mar2026.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/djen-97ju/0",
    },
    "mssp-performance": {
        "name": "MSSP ACO Performance PY2024",
        "entity": "aco",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-09/a355a538-5e08-46bf-a744-549f02782154/PY%202024%20ACO%20Results%20PUF_Rerun_20250925.csv",
        "api_url": "https://data.cms.gov/data-api/v1/dataset/73b2ce14-351d-40ac-90ba-ec9e1f5ba80c/data",
    },
    "hrrp": {
        "name": "Hospital Readmissions Reduction Program",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/a171bc36c488d3e0dc33ec63abb469a6_1770163617/FY_2026_Hospital_Readmissions_Reduction_Program_Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/9n3s-kdb3/0",
    },
    "hvbp-tps": {
        "name": "Hospital Value-Based Purchasing TPS",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/5551d4839c1dd75e3f7fe1310a1e2369_1770163628/hvbp_tps.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/ypbt-wvdk/0",
    },
    "cdc-places": {
        "name": "CDC PLACES County-Level Data",
        "entity": "county",
        "api_type": "soda",
        "csv_url": None,  # No direct CSV; use SODA API
        "api_url": "https://data.cdc.gov/resource/swc5-untb.csv",
    },
    # ── Phase 1 hospital enrichment datasets ──────────────────────
    "hosp-timely-care": {
        "name": "Timely and Effective Care — Hospital",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/0437b5494ac61507ad90f2af6b8085a7_1770163650/Timely_and_Effective_Care-Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/yv7e-xc69/0",
    },
    "hosp-complications": {
        "name": "Complications and Deaths — Hospital",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/6af7c44d77436e5a1caac3ce39a83fe9_1770163566/Complications_and_Deaths-Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/ynj2-r877/0",
    },
    "hosp-hcahps": {
        "name": "Patient Survey (HCAHPS) — Hospital",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/78a50346fbe828ea0ce2837847af6a7c_1770163580/HCAHPS-Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/dgck-syfz/0",
    },
    "hosp-hai": {
        "name": "Healthcare Associated Infections — Hospital",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/43825e12dc0c923df9ba5cbdf473c9d5_1770163586/Healthcare_Associated_Infections-Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/77hc-ibv8/0",
    },
    "hosp-unplanned-visits": {
        "name": "Unplanned Hospital Visits — Hospital",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/30edc1d0417a34b58affcc2495a02b0a_1770163657/Unplanned_Hospital_Visits-Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/632h-zaca/0",
    },
    "hosp-mspb": {
        "name": "Medicare Spending Per Beneficiary — Hospital",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/500f70bcb6c65433c00a96af0e0c0430_1770163607/HOSPITAL_QUARTERLY_MSPB_6_DECIMALS.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/5hk7-b79m/0",
    },
    # ── Phase 2 SNF enrichment datasets ─────────────────────────
    "nh-penalties": {
        "name": "Nursing Home Penalties",
        "entity": "snf",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/f7b99706de76b7f098d49a42836a58c5_1773439548/NH_Penalties_Mar2026.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/g6vv-u9sr/0",
    },
    "nh-deficiencies": {
        "name": "Nursing Home Health Deficiencies",
        "entity": "snf",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/f609bbd6bc2c89e847fe42c3b3e40c65_1773439542/NH_HealthCitations_Mar2026.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/r5ix-sfxw/0",
    },
    "nh-ownership": {
        "name": "Nursing Home Ownership",
        "entity": "snf",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/b26803052eaf48fda977c7088cb28a84_1773439546/NH_Ownership_Mar2026.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/y2hd-n93e/0",
    },
    # ── Phase 3 ACO cross-link datasets ─────────────────────────
    "aco-participants": {
        "name": "ACO Participants",
        "entity": "aco",
        "api_type": "data-api",
        "csv_url": None,
        "api_url": "https://data.cms.gov/data-api/v1/dataset/9767cb68-8ea9-4f0b-8179-9431abc89f11/data",
    },
    "aco-snf-affiliates": {
        "name": "ACO SNF Affiliates",
        "entity": "aco",
        "api_type": "data-api",
        "csv_url": None,
        "api_url": "https://data.cms.gov/data-api/v1/dataset/5b227bd9-82d4-4145-86fd-809e02ca7f18/data",
    },
    # ── M5 datasets ─────────────────────────────────────────────────
    "partd-drug-spending": {
        "name": "Medicare Part D Spending by Drug",
        "entity": "drug",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-05/56d95a8b-138c-4b60-84a5-613fbab7197f/DSD_PTD_RY25_P04_V10_DY23_BGM.csv",
        "api_url": "https://data.cms.gov/data-api/v1/dataset/7e0b4365-fd63-4a29-8f5e-e0ac9f66a81b/data",
    },
    "partb-drug-spending": {
        "name": "Medicare Part B Spending by Drug",
        "entity": "drug",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-05/f52d5fcd-8d93-481d-9173-6219813e4efb/DSD_PTB_RY25_P06_V10_DYT23_HCPCS-%20250430.csv",
        "api_url": "https://data.cms.gov/data-api/v1/dataset/76a714ad-3a2c-43ac-b76d-9dadf8f7d890/data",
    },
    "partb-discarded-units": {
        "name": "Medicare Part B Discarded Drug Units",
        "entity": "drug",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-05/201381fe-e6a9-413c-8e52-636f28796d5e/DW_R25_P04_V10_DY23_HCPCS-%20250505.csv",
        "api_url": "https://data.cms.gov/data-api/v1/dataset/09fd71b8-eb3e-45af-a01e-f8ab5a190e84/data",
    },
    "inpatient-by-drg": {
        "name": "Medicare Inpatient Hospitals by Provider and Service (DRG)",
        "entity": "drg",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-05/ca1c9013-8c7c-4560-a4a1-28cf7e43ccc8/MUP_INP_RY25_P03_V10_DY23_PrvSvc.CSV",
        "api_url": "https://data.cms.gov/data-api/v1/dataset/690ddc6c-2767-4618-b277-420ffb2bf27c/data",
    },
    # ── Tier A enrichment datasets ─────────────────────────────────
    "hosp-cost-report": {
        "name": "Hospital Provider Cost Report",
        "entity": "hospital",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2026-01/3c39f483-c7e0-4025-8396-4df76942e10f/CostReport_2023_Final.csv",
        "api_url": None,
    },
    "snf-cost-report": {
        "name": "Skilled Nursing Facility Cost Report",
        "entity": "snf",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2025-11/34ea98e4-20f4-42f7-b5b2-616d35b0fe93/CostReportsnf_Final_23.csv",
        "api_url": None,
    },
    "hac-reduction": {
        "name": "Hospital-Acquired Condition (HAC) Reduction Program",
        "entity": "hospital",
        "api_type": "provider-data",
        "csv_url": "https://data.cms.gov/provider-data/sites/default/files/resources/74be67fd6833391f578abb5605d03ce6_1770163605/FY_2026_HAC_Reduction_Program_Hospital.csv",
        "api_url": "https://data.cms.gov/provider-data/api/1/datastore/query/yq43-i98g/0",
    },
    "aco-bene-county": {
        "name": "ACO Assigned Beneficiaries by County",
        "entity": "aco",
        "api_type": "data-api",
        "csv_url": "https://data.cms.gov/sites/default/files/2024-11/8a74dd30-06a1-4751-beee-dc0dd3c9d609/Number_Of_ACO_Assigned_Beneficiaries_by_County_PUF_2023_01_01.csv",
        "api_url": None,
    },
    "cdc-sdoh": {
        "name": "CDC SDOH Measures for County",
        "entity": "county",
        "api_type": "soda",
        "csv_url": None,
        "api_url": "https://data.cdc.gov/resource/i6u4-y3g4.csv",
    },
    "cms-chronic-conditions": {
        "name": "Medicare Specific Chronic Conditions by County",
        "entity": "county",
        "api_type": "data-api",
        "csv_url": None,
        "api_url": "https://data.cms.gov/data-api/v1/dataset/efaa78b6-71af-4e1e-b52a-93ed3a1e1cb4/data",
    },
    "nadac": {
        "name": "NADAC National Average Drug Acquisition Cost",
        "entity": "drug",
        "api_type": "provider-data",
        "csv_url": "https://download.medicaid.gov/data/nadac-national-average-drug-acquisition-cost-04-08-2026.csv",
        "api_url": "https://data.medicaid.gov/api/1/datastore/query/fbb83258-11c7-47f5-8b18-5f8e79f7e704/0",
    },
}

# Page sizes for paginated API fallbacks
PROVIDER_DATA_PAGE_SIZE = 1000
DATA_API_PAGE_SIZE = 5000
SODA_PAGE_SIZE = 50000


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


def _download_soda_api(api_url: str, out_path: Path) -> int:
    """Download via the Socrata (SODA) API with $limit/$offset pagination.

    The CDC PLACES API returns CSV directly when the URL ends in .csv.
    Paginates until a page returns fewer rows than the limit.
    Returns total row count.
    """
    print(f"    [soda] {api_url}")
    total_rows = 0
    offset = 0
    first_page = True

    with httpx.Client(timeout=300.0, follow_redirects=True) as client:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            while True:
                params = {"$limit": SODA_PAGE_SIZE, "$offset": offset}
                resp = client.get(api_url, params=params)
                resp.raise_for_status()
                text = resp.text

                lines = text.splitlines()
                if not lines:
                    break

                if first_page:
                    # Write header + data rows
                    f.write(text)
                    if not text.endswith("\n"):
                        f.write("\n")
                    # Data rows = total lines minus the header
                    page_rows = len(lines) - 1
                    first_page = False
                else:
                    # Skip the header row on subsequent pages
                    data_lines = lines[1:]
                    if not data_lines:
                        break
                    f.write("\n".join(data_lines))
                    f.write("\n")
                    page_rows = len(data_lines)

                total_rows += page_rows
                offset += SODA_PAGE_SIZE

                if page_rows < SODA_PAGE_SIZE:
                    break

    return total_rows


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
        elif api_type == "soda":
            row_count = _download_soda_api(api_url, out_path)
        elif api_type == "data-api":
            row_count = _download_data_api(api_url, out_path)
        else:
            raise RuntimeError(f"Unknown api_type '{api_type}' for {dataset_id}")
        print(f"    -> {out_path.name} ({row_count:,} rows)")
        return out_path

    raise RuntimeError(f"No download method available for {dataset_id}")


def acquire_all(raw_dir: Path) -> dict[str, Path]:
    """Download all datasets. Returns {dataset_id: file_path}.

    Datasets that fail to download are skipped with a warning.
    """
    results = {}
    for dataset_id in DATASETS:
        try:
            results[dataset_id] = download_dataset(dataset_id, raw_dir)
        except Exception as e:
            print(f"  [ERROR] Failed to download {dataset_id}: {e}")
            print(f"  [ERROR] Skipping {dataset_id} — enrichment will be skipped")
    return results
