"""
Enrich ACO manifests with participant and SNF affiliate cross-links.

Reads existing ACO manifests from site_data/aco/ and joins:
  a) ACO Participants — TINs/NPIs/CCNs of providers in each ACO
  b) ACO SNF Affiliates — SNF CCNs affiliated with each ACO

This replaces the weak state-level ACO→county links with organizational
cross-links: ACO→Hospital and ACO→SNF (via CCN), and the reverse links
on hospital/SNF manifests (Hospital→ACO, SNF→ACO).

Updated manifests are written back in place.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from etl.normalize.keys import normalize_aco_id, normalize_ccn
from etl.provenance.envelope import build_provenance


def _clean(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip()


def _find_column(row: dict[str, str], candidates: list[str]) -> str | None:
    """Find the first matching column name from candidates."""
    row_keys = list(row.keys())
    row_keys_upper = {k.upper(): k for k in row_keys}

    for candidate in candidates:
        if candidate in row:
            return candidate
        if candidate.upper() in row_keys_upper:
            return row_keys_upper[candidate.upper()]

    for candidate in candidates:
        candidate_upper = candidate.upper()
        for key in row_keys:
            if candidate_upper in key.upper():
                return key

    return None


def _load_aco_participants(
    csv_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Load ACO Participants data grouped by ACO ID.

    Returns {aco_id: [{provider_name, ccn, npi, tin, provider_type, ...}]}.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_aco = _find_column(sample, [
        "ACO_ID", "ACO ID", "ACO_Num", "aco_id",
    ])
    # ACO Name column — not extracted per-row but used for identification
    _find_column(sample, ["ACO_Name", "ACO Name", "aco_name"])
    col_tin = _find_column(sample, [
        "ACO_Participant_TIN", "TIN", "Participant_TIN",
        "aco_participant_tin",
    ])
    col_ccn = _find_column(sample, [
        "Participant_CCN", "CCN", "Provider_CCN",
        "participant_ccn",
    ])
    col_provider_name = _find_column(sample, [
        "Participant_Legal_Business_Name",
        "Legal Business Name",
        "Provider Name",
        "participant_legal_business_name",
    ])
    col_provider_type = _find_column(sample, [
        "Participant_Provider_Type",
        "Provider Type",
        "participant_provider_type",
    ])
    col_npi = _find_column(sample, [
        "Participant_NPI", "NPI", "participant_npi",
    ])
    col_start = _find_column(sample, [
        "Participation_Start_Date",
        "Start Date",
        "participation_start_date",
    ])

    if col_aco is None:
        print("    [warn] Could not find ACO ID column in participants data")
        return result

    for row in rows:
        aco_id = normalize_aco_id(row.get(col_aco, ""))
        if aco_id is None:
            continue

        participant: dict[str, Any] = {}
        if col_provider_name:
            participant["provider_name"] = _clean(row.get(col_provider_name, ""))
        if col_ccn:
            ccn = normalize_ccn(row.get(col_ccn, ""))
            if ccn:
                participant["ccn"] = ccn
        if col_tin:
            participant["tin"] = _clean(row.get(col_tin, ""))
        if col_npi:
            participant["npi"] = _clean(row.get(col_npi, ""))
        if col_provider_type:
            participant["provider_type"] = _clean(row.get(col_provider_type, ""))
        if col_start:
            participant["start_date"] = _clean(row.get(col_start, ""))

        if participant.get("provider_name") or participant.get("ccn"):
            result.setdefault(aco_id, []).append(participant)

    return result


def _load_aco_snf_affiliates(
    csv_path: Path,
) -> dict[str, list[dict[str, Any]]]:
    """Load ACO SNF Affiliates data grouped by ACO ID.

    Returns {aco_id: [{snf_ccn, snf_name, state, ...}]}.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    with open(csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return result

    sample = rows[0]
    col_aco = _find_column(sample, [
        "ACO_ID", "ACO ID", "ACO_Num", "aco_id",
    ])
    col_ccn = _find_column(sample, [
        "SNF_CCN", "SNF CCN", "CCN", "snf_ccn",
        "Affiliate_CCN",
    ])
    col_name = _find_column(sample, [
        "SNF_Name", "SNF Name", "snf_name",
        "Affiliate_Name",
    ])
    col_state = _find_column(sample, [
        "SNF_State", "State", "snf_state",
    ])

    if col_aco is None:
        print("    [warn] Could not find ACO ID column in SNF affiliates data")
        return result

    for row in rows:
        aco_id = normalize_aco_id(row.get(col_aco, ""))
        if aco_id is None:
            continue

        affiliate: dict[str, Any] = {}
        if col_ccn:
            ccn = normalize_ccn(row.get(col_ccn, ""))
            if ccn:
                affiliate["snf_ccn"] = ccn
        if col_name:
            affiliate["snf_name"] = _clean(row.get(col_name, ""))
        if col_state:
            affiliate["state"] = _clean(row.get(col_state, ""))

        if affiliate.get("snf_ccn") or affiliate.get("snf_name"):
            result.setdefault(aco_id, []).append(affiliate)

    return result


def enrich_acos(
    aco_dir: Path,
    hospital_dir: Path,
    snf_dir: Path,
    download_date: date,
    *,
    participants_csv: Path | None = None,
    snf_affiliates_csv: Path | None = None,
) -> int:
    """Enrich ACO manifests with participant cross-links.

    Also writes reverse links onto hospital and SNF manifests so they
    can show "This provider participates in ACO X".

    Returns the number of ACO manifests enriched.
    """
    if not aco_dir.exists():
        print("  [enrich-aco] No ACO directory found")
        return 0

    # Load participant data
    participants: dict[str, list[dict[str, Any]]] = {}
    if participants_csv and participants_csv.exists():
        print("  [enrich-aco] Loading ACO Participants data...")
        participants = _load_aco_participants(participants_csv)
        print(f"  [enrich-aco] Participants: {len(participants):,} ACOs")

    snf_affiliates: dict[str, list[dict[str, Any]]] = {}
    if snf_affiliates_csv and snf_affiliates_csv.exists():
        print("  [enrich-aco] Loading ACO SNF Affiliates data...")
        snf_affiliates = _load_aco_snf_affiliates(snf_affiliates_csv)
        print(f"  [enrich-aco] SNF Affiliates: {len(snf_affiliates):,} ACOs")

    if not participants and not snf_affiliates:
        print("  [enrich-aco] No enrichment data available")
        return 0

    # Build reverse index: CCN -> list of (aco_id, aco_name, role)
    # for writing back onto hospital and SNF manifests
    ccn_to_acos: dict[str, list[dict[str, str]]] = {}

    # ── Enrich ACO manifests ───────────────────────────────────────
    enriched = 0
    aco_manifests: dict[str, dict[str, Any]] = {}

    for manifest_path in sorted(aco_dir.glob("*.json")):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        aco_id = manifest.get("aco_id", "")
        aco_name = manifest.get("aco_name", "")
        aco_manifests[aco_id] = manifest
        modified = False

        # Add participants
        if aco_id in participants:
            manifest.setdefault("data", {})["participants"] = participants[aco_id]
            modified = True

            # Build reverse index from participant CCNs
            for p in participants[aco_id]:
                ccn = p.get("ccn")
                if ccn:
                    ccn_to_acos.setdefault(ccn, []).append({
                        "aco_id": aco_id,
                        "aco_name": aco_name,
                        "role": "participant",
                    })

        # Add SNF affiliates
        if aco_id in snf_affiliates:
            manifest.setdefault("data", {})["snf_affiliates"] = snf_affiliates[aco_id]
            modified = True

            # Build reverse index from SNF affiliate CCNs
            for a in snf_affiliates[aco_id]:
                ccn = a.get("snf_ccn")
                if ccn:
                    ccn_to_acos.setdefault(ccn, []).append({
                        "aco_id": aco_id,
                        "aco_name": aco_name,
                        "role": "snf_affiliate",
                    })

        if modified:
            provenance_list = manifest.get("provenance", [])
            existing_ids = {p.get("dataset_id") for p in provenance_list}

            if aco_id in participants and "aco-participants" not in existing_ids:
                provenance_list.append(
                    build_provenance(
                        dataset_id="aco-participants",
                        dataset_name="ACO Participants",
                        vintage=str(download_date.year),
                        download_date=download_date,
                        row_count=sum(len(v) for v in participants.values()),
                    )
                )

            if aco_id in snf_affiliates and "aco-snf-affiliates" not in existing_ids:
                provenance_list.append(
                    build_provenance(
                        dataset_id="aco-snf-affiliates",
                        dataset_name="ACO SNF Affiliates",
                        vintage=str(download_date.year),
                        download_date=download_date,
                        row_count=sum(len(v) for v in snf_affiliates.values()),
                    )
                )

            manifest["provenance"] = provenance_list

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            enriched += 1

    # ── Write reverse links onto hospital manifests ────────────────
    hospital_linked = 0
    if hospital_dir.exists():
        for manifest_path in sorted(hospital_dir.glob("*.json")):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            ccn = manifest.get("ccn", "")
            if ccn not in ccn_to_acos:
                continue

            # Add ACO links to related list
            related = manifest.get("related", [])
            existing_aco_ids = {
                r["id"] for r in related if r.get("type") == "aco"
            }

            added = False
            for aco_link in ccn_to_acos[ccn]:
                if aco_link["aco_id"] not in existing_aco_ids:
                    related.append({
                        "type": "aco",
                        "id": aco_link["aco_id"],
                        "name": aco_link["aco_name"],
                        "context": f"ACO {aco_link['role'].replace('_', ' ')}",
                    })
                    added = True

            if added:
                manifest["related"] = related
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                hospital_linked += 1

    print(f"  [enrich-aco] Linked {hospital_linked:,} hospitals to ACOs")

    # ── Write reverse links onto SNF manifests ─────────────────────
    snf_linked = 0
    if snf_dir.exists():
        for manifest_path in sorted(snf_dir.glob("*.json")):
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            ccn = manifest.get("ccn", "")
            if ccn not in ccn_to_acos:
                continue

            related = manifest.get("related", [])
            existing_aco_ids = {
                r["id"] for r in related if r.get("type") == "aco"
            }

            added = False
            for aco_link in ccn_to_acos[ccn]:
                if aco_link["aco_id"] not in existing_aco_ids:
                    related.append({
                        "type": "aco",
                        "id": aco_link["aco_id"],
                        "name": aco_link["aco_name"],
                        "context": f"ACO {aco_link['role'].replace('_', ' ')}",
                    })
                    added = True

            if added:
                manifest["related"] = related
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
                snf_linked += 1

    print(f"  [enrich-aco] Linked {snf_linked:,} SNFs to ACOs")
    print(f"  [enrich-aco] Enriched {enriched:,} ACO manifests")
    return enriched
