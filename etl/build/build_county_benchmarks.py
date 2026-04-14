"""
Build national county benchmark statistics.

Reads all county manifests and computes percentile distributions
(p10/p25/p50/p75/p90/mean/n) for every numeric metric across Geographic
Variation, CDC PLACES, and CDC SDOH. Also computes per-county percentile
ranks so the frontend can show "p42" badges next to individual values.

Output: site_data/county_benchmarks.json
"""

from __future__ import annotations

import bisect
import json
import statistics
from pathlib import Path
from typing import Any


def _try_float(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace(",", "").replace("$", "").replace("%", "")
        if val in ("", "N/A", "Not Available", ".", "*", "-"):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    return None


def _percentiles(values: list[float]) -> dict[str, float] | None:
    """Compute p10/p25/p50/p75/p90/mean/n for a list of values."""
    if len(values) < 10:
        return None
    values = sorted(values)
    n = len(values)
    return {
        "p10": values[int(n * 0.10)],
        "p25": values[int(n * 0.25)],
        "p50": values[int(n * 0.50)],
        "p75": values[int(n * 0.75)],
        "p90": values[int(n * 0.90)],
        "mean": round(statistics.mean(values), 4),
        "n": n,
    }


def _iter_numeric_leaves(manifest: dict[str, Any]) -> dict[str, float]:
    """Extract every numeric field we care about from a county manifest.

    Returns {benchmark_key: value}. Keys use dotted paths:
      - gv.{COLUMN}            (Geographic Variation metric)
      - places.{MEASURE_ID}    (CDC PLACES prevalence, %)
      - sdoh.{MEASURE_ID}      (CDC SDOH measure)
    """
    out: dict[str, float] = {}
    data = manifest.get("data", {})

    # Geographic Variation
    gv = data.get("geographic_variation", {}) or {}
    for col, entry in (gv.get("metrics") or {}).items():
        if isinstance(entry, dict):
            v = _try_float(entry.get("value"))
            if v is not None:
                out[f"gv.{col}"] = v

    # PLACES
    places = data.get("places") or {}
    for mid, entry in places.items():
        if isinstance(entry, dict):
            v = _try_float(entry.get("value"))
            if v is not None:
                out[f"places.{mid}"] = v

    # SDOH
    sdoh = data.get("sdoh") or {}
    sdoh_measures = sdoh.get("measures") if isinstance(sdoh, dict) else None
    if isinstance(sdoh_measures, dict):
        for mid, entry in sdoh_measures.items():
            if isinstance(entry, dict):
                v = _try_float(entry.get("value"))
                if v is not None:
                    out[f"sdoh.{mid}"] = v

    return out


def build_county_benchmarks(county_dir: Path, output_path: Path) -> int:
    """Build county percentiles + per-county percentile ranks.

    Returns the number of fields with computed benchmarks.
    """
    if not county_dir.exists():
        print("  [bench] No county directory")
        return 0

    # ── Pass 1: collect values ────────────────────────────────────────
    field_values: dict[str, list[float]] = {}
    per_county: dict[str, dict[str, float]] = {}
    manifest_count = 0

    for path in sorted(county_dir.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        manifest_count += 1
        fips = m.get("fips", "")
        if not fips:
            continue
        leaves = _iter_numeric_leaves(m)
        per_county[fips] = leaves
        for k, v in leaves.items():
            field_values.setdefault(k, []).append(v)

    print(f"  [bench] Counties: {manifest_count:,}; unique fields: {len(field_values):,}")

    # ── Pass 2: percentiles + per-county ranks ────────────────────────
    benchmarks: dict[str, dict[str, float]] = {}
    sorted_by_field: dict[str, list[float]] = {}
    for key, vals in field_values.items():
        p = _percentiles(vals)
        if p is None:
            continue
        benchmarks[key] = p
        sorted_by_field[key] = sorted(vals)

    county_ranks: dict[str, dict[str, int]] = {}
    for fips, leaves in per_county.items():
        rank_entry: dict[str, int] = {}
        for key, val in leaves.items():
            sorted_vals = sorted_by_field.get(key)
            if not sorted_vals:
                continue
            idx = bisect.bisect_left(sorted_vals, val)
            if idx >= len(sorted_vals):
                idx = len(sorted_vals) - 1
            pct = int((idx / max(len(sorted_vals) - 1, 1)) * 100)
            rank_entry[key] = pct
        if rank_entry:
            county_ranks[fips] = rank_entry

    # ── Write ─────────────────────────────────────────────────────────
    output = {
        "metadata": {
            "county_count": manifest_count,
            "field_count": len(benchmarks),
        },
        "benchmarks": benchmarks,
        "county_ranks": county_ranks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))
    print(f"  [bench] Wrote {output_path} ({len(benchmarks)} fields, {len(county_ranks)} counties)")
    return len(benchmarks)
