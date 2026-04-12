"""
Join-key normalization for CareGraph ETL.

Handles:
- CCN (CMS Certification Number): 6-character, zero-padded string
- County FIPS: 5-digit, zero-padded string
- SSA-to-FIPS crosswalk application
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


def normalize_ccn(raw_ccn: str | int | None) -> str | None:
    """Normalize a CCN to 6-character, zero-padded string.

    CMS Certification Numbers are 6 characters. Some sources drop leading zeros.
    """
    if raw_ccn is None or str(raw_ccn).strip() == "":
        return None
    ccn = str(raw_ccn).strip()
    # Remove any non-alphanumeric characters
    ccn = re.sub(r"[^A-Za-z0-9]", "", ccn)
    # Zero-pad to 6 characters
    ccn = ccn.zfill(6)
    return ccn


def normalize_fips(raw_fips: str | int | None) -> str | None:
    """Normalize a county FIPS code to 5-digit, zero-padded string."""
    if raw_fips is None or str(raw_fips).strip() == "":
        return None
    fips = str(raw_fips).strip()
    # Remove any non-digit characters
    fips = re.sub(r"\D", "", fips)
    if not fips:
        return None
    # Zero-pad to 5 digits
    fips = fips.zfill(5)
    return fips


def normalize_state_fips(raw_fips: str | int | None) -> str | None:
    """Normalize a state FIPS code to 2-digit, zero-padded string."""
    if raw_fips is None or str(raw_fips).strip() == "":
        return None
    fips = str(raw_fips).strip()
    fips = re.sub(r"\D", "", fips)
    if not fips:
        return None
    return fips.zfill(2)


# Built-in SSA-to-FIPS crosswalk for common codes.
# In a full build this would be loaded from the NBER crosswalk file.
# For M1, the Geographic Variation dataset uses FIPS directly, so this
# is included for future use.
SSA_TO_FIPS: dict[str, str] = {}


def load_ssa_to_fips_crosswalk(crosswalk_path: Path) -> dict[str, str]:
    """Load SSA-to-FIPS crosswalk from a CSV file.

    Expected columns: ssa_code, fips_code (or similar).
    Returns {ssa_code: fips_code}.
    """
    mapping: dict[str, str] = {}
    if not crosswalk_path.exists():
        return mapping
    with open(crosswalk_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ssa = row.get("ssa_code", row.get("ssacounty", "")).strip()
            fips = row.get("fips_code", row.get("fipscounty", "")).strip()
            if ssa and fips:
                mapping[ssa] = normalize_fips(fips) or fips
    return mapping


def apply_ssa_to_fips(ssa_code: str, crosswalk: dict[str, str]) -> str | None:
    """Convert an SSA county code to FIPS using the crosswalk."""
    return crosswalk.get(ssa_code.strip())
