"""
Provenance envelope construction for CareGraph ETL.

Every page manifest carries provenance metadata: dataset ID, vintage,
download timestamp, row count, and source URL.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any


def build_provenance(
    dataset_id: str,
    dataset_name: str,
    vintage: str,
    download_date: date,
    row_count: int,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Build a provenance envelope for a dataset contribution to a page manifest."""
    return {
        "dataset_id": dataset_id,
        "dataset_name": dataset_name,
        "vintage": vintage,
        "download_date": download_date.isoformat(),
        "download_timestamp": datetime.now().isoformat(),
        "row_count": row_count,
        "source_url": source_url or f"https://data.cms.gov/resource/{dataset_id}",
    }
