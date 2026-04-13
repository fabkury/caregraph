"""
Build ACO peer cohorts using distance-based KNN within track partitions.

Reads all ACO manifests, extracts 15 structural features across 5 domains,
partitions ACOs into BASIC vs ENHANCED, computes weighted Euclidean distance
within each partition, and selects K=30 nearest neighbors per ACO.

Output: site_data/aco_peer_cohorts.json

See docs/aco-contextual-layers.md for full specification.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path


def _pf(val: str | None) -> float | None:
    """Parse a numeric string, returning None for missing/suppressed."""
    if not val or val in ("*", "-", ".", "", " ", "N/A"):
        return None
    try:
        return float(val.replace(",", "").replace("$", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


# ── Feature extraction ────────────────────────────────────────────────

FEATURE_DEFS: list[tuple[str, str, float]] = [
    # (feature_name, domain, domain_weight)
    # Domain A: Population Acuity (1.5×)
    ("composite_hcc", "acuity", 1.5),
    ("pct_85plus", "acuity", 1.5),
    # Domain B: Population Composition (1.25×)
    ("perc_dual", "composition", 1.25),
    ("rr_weight_esrd", "composition", 1.25),
    ("rr_weight_dis", "composition", 1.25),
    ("perc_lti", "composition", 1.25),
    ("pct_under65", "composition", 1.25),
    # Domain C: Scale (1.0×)
    ("log2_n_ab", "scale", 1.0),
    ("log2_total_clinicians", "scale", 1.0),
    # Domain D: Infrastructure (1.0×)
    ("sqrt_n_hosp", "infrastructure", 1.0),
    ("sqrt_n_cah", "infrastructure", 1.0),
    ("sqrt_n_fqhc", "infrastructure", 1.0),
    ("np_pcp_ratio", "infrastructure", 1.0),
    ("pcp_spec_ratio", "infrastructure", 1.0),
    # Domain E: Assignment (0.5×)
    ("assign_prospective", "assignment", 0.5),
]

K_NEIGHBORS = 30
MEDIAN_PERC_LTI = 0.76  # Imputation value for missing Perc_LTI


def _extract_features(raw: dict[str, str]) -> dict[str, float] | None:
    """Extract all 15 features from raw MSSP data. Returns None if critical fields missing."""
    n_ab = _pf(raw.get("N_AB"))
    if not n_ab or n_ab <= 0:
        return None

    # Composite HCC: weighted sum of segment HCC scores using RR weights
    hcc_agnd = _pf(raw.get("CMS_HCC_RiskScore_AGND_PY"))
    hcc_dis = _pf(raw.get("CMS_HCC_RiskScore_DIS_PY"))
    hcc_agdu = _pf(raw.get("CMS_HCC_RiskScore_AGDU_PY"))
    w_agnd = _pf(raw.get("RR_weight_AGND_PY"))
    w_dis = _pf(raw.get("RR_weight_DIS_PY"))
    w_agdu = _pf(raw.get("RR_weight_AGDU_PY"))
    w_esrd = _pf(raw.get("RR_weight_ESRD_PY"))
    hcc_esrd = _pf(raw.get("CMS_HCC_RiskScore_ESRD_PY"))

    if None in (hcc_agnd, hcc_dis, hcc_agdu, w_agnd, w_dis, w_agdu):
        return None

    # Include ESRD if available, otherwise redistribute weight
    if hcc_esrd is not None and w_esrd is not None:
        total_w = (w_agnd or 0) + (w_dis or 0) + (w_agdu or 0) + (w_esrd or 0)
        composite_hcc = (
            hcc_agnd * w_agnd + hcc_dis * w_dis +
            hcc_agdu * w_agdu + hcc_esrd * w_esrd
        ) / max(total_w, 0.001)
    else:
        total_w = (w_agnd or 0) + (w_dis or 0) + (w_agdu or 0)
        composite_hcc = (
            hcc_agnd * w_agnd + hcc_dis * w_dis + hcc_agdu * w_agdu
        ) / max(total_w, 0.001)

    # Age composition
    age_85 = _pf(raw.get("N_Ben_Age_85plus")) or 0
    age_u65 = _pf(raw.get("N_Ben_Age_0_64")) or 0

    # Clinician counts
    n_pcp = _pf(raw.get("N_PCP")) or 0
    n_spec = _pf(raw.get("N_Spec")) or 0
    n_np = _pf(raw.get("N_NP")) or 0
    n_pa = _pf(raw.get("N_PA")) or 0
    n_cns = _pf(raw.get("N_CNS")) or 0
    total_clin = n_pcp + n_spec + n_np + n_pa + n_cns

    # Facility counts
    n_hosp = _pf(raw.get("N_Hosp")) or 0
    n_cah = _pf(raw.get("N_CAH")) or 0
    n_fqhc = _pf(raw.get("N_FQHC")) or 0

    # LTI: impute median if missing
    perc_lti = _pf(raw.get("Perc_LTI"))
    if perc_lti is None:
        perc_lti = MEDIAN_PERC_LTI

    perc_dual = _pf(raw.get("Perc_Dual"))
    if perc_dual is None:
        return None

    return {
        "composite_hcc": composite_hcc,
        "pct_85plus": age_85 / n_ab * 100,
        "perc_dual": perc_dual,
        "rr_weight_esrd": (w_esrd or 0),
        "rr_weight_dis": (w_dis or 0),
        "perc_lti": perc_lti,
        "pct_under65": age_u65 / n_ab * 100,
        "log2_n_ab": math.log2(max(n_ab, 1)),
        "log2_total_clinicians": math.log2(max(total_clin, 1)),
        "sqrt_n_hosp": math.sqrt(n_hosp),
        "sqrt_n_cah": math.sqrt(n_cah),
        "sqrt_n_fqhc": math.sqrt(n_fqhc),
        "np_pcp_ratio": n_np / max(n_pcp, 1),
        "pcp_spec_ratio": n_pcp / max(n_spec, 1),
        "assign_prospective": 1.0 if raw.get("Assign_Type") == "Prospective" else 0.0,
    }


def _is_basic(track: str) -> bool:
    return track in ("A", "B", "C", "D")


def _cohort_description(
    track_group: str,
    peer_features: list[dict[str, float]],
    mssp_medians: dict[str, float],
) -> str:
    """Generate a human-readable cohort description."""
    parts = []

    # Size
    n_abs = [2 ** f["log2_n_ab"] for f in peer_features]
    med_n_ab = sorted(n_abs)[len(n_abs) // 2]
    if med_n_ab < 10_000:
        parts.append("small")
    elif med_n_ab < 25_000:
        parts.append("mid-size")
    elif med_n_ab < 50_000:
        parts.append("large")
    else:
        parts.append("very large")

    parts.append(f"{track_group}-track")

    # Acuity
    hccs = sorted([f["composite_hcc"] for f in peer_features])
    med_hcc = hccs[len(hccs) // 2]
    mssp_med_hcc = mssp_medians.get("composite_hcc", 1.0)
    if med_hcc > mssp_med_hcc * 1.05:
        parts.append("above-average acuity")
    elif med_hcc < mssp_med_hcc * 0.95:
        parts.append("below-average acuity")
    else:
        parts.append("average acuity")

    # Infrastructure
    hosps = sorted([f["sqrt_n_hosp"] ** 2 for f in peer_features])
    cahs = sorted([f["sqrt_n_cah"] ** 2 for f in peer_features])
    fqhcs = sorted([f["sqrt_n_fqhc"] ** 2 for f in peer_features])
    med_hosp = hosps[len(hosps) // 2]
    med_cah = cahs[len(cahs) // 2]
    med_fqhc = fqhcs[len(fqhcs) // 2]

    if med_cah >= 1 or med_fqhc >= 5:
        parts.append("rural infrastructure")
    elif med_hosp >= 1:
        parts.append("hospital-affiliated")
    else:
        parts.append("physician-led")

    return f"{K_NEIGHBORS} similar {', '.join(parts)} ACOs"


# ── Key metrics for peer medians ──────────────────────────────────────

PEER_MEDIAN_FIELDS = [
    "Sav_rate", "Per_Capita_Exp_TOTAL_PY", "QualScore", "N_AB",
    "ADM", "P_EDV_Vis", "P_EM_PCP_Vis", "P_EM_SP_Vis",
    "CapAnn_INP_All", "CapAnn_SNF", "CapAnn_OPD", "CapAnn_PB",
    "CapAnn_HSP", "CapAnn_HHA", "CapAnn_DME", "CapAnn_AmbPay",
    "CAHPS_1", "CAHPS_2", "CAHPS_3", "CAHPS_4", "CAHPS_5",
    "CAHPS_6", "CAHPS_7", "CAHPS_8", "CAHPS_9", "CAHPS_11",
    "Measure_479", "Measure_484",
    "QualityID_318", "QualityID_110", "QualityID_226",
    "QualityID_113", "QualityID_112", "QualityID_438", "QualityID_370",
    "QualityID_001_WI", "QualityID_134_WI", "QualityID_236_WI",
    "Perc_Dual", "Perc_LTI",
    "CMS_HCC_RiskScore_AGND_PY", "CMS_HCC_RiskScore_DIS_PY",
    "CMS_HCC_RiskScore_AGDU_PY",
    "UpdatedBnchmk", "HistBnchmk",
    "SNF_LOS", "SNF_PayperStay",
    "P_CT_VIS", "P_MRI_VIS", "P_Nurse_Vis",
    "P_SNF_ADM", "P_FQHC_RHC_Vis",
    "Per_Capita_Exp_ALL_ESRD_PY", "Per_Capita_Exp_ALL_DIS_PY",
    "Per_Capita_Exp_ALL_AGDU_PY", "Per_Capita_Exp_ALL_AGND_PY",
]


def build_aco_peers(aco_dir: Path, output_path: Path) -> int:
    """Build peer cohorts for all ACOs.

    Returns the number of ACOs with assigned peer cohorts.
    """
    # Load all manifests
    manifests: list[dict] = []
    for f in sorted(aco_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            manifests.append(json.load(fh))

    if not manifests:
        print("  WARNING: No ACO manifests found")
        return 0

    # Extract features
    aco_data: list[dict] = []  # {aco_id, track_group, features, raw}
    skipped = 0
    for m in manifests:
        raw = m.get("data", {}).get("mssp_performance", {}).get("raw", {})
        track = raw.get("Current_Track", "")
        features = _extract_features(raw)
        if features is None:
            skipped += 1
            continue
        aco_data.append({
            "aco_id": m.get("aco_id", ""),
            "track_group": "BASIC" if _is_basic(track) else "ENHANCED",
            "features": features,
            "raw": raw,
        })

    print(f"  {len(aco_data)} ACOs with complete features ({skipped} skipped)")

    # Partition
    basic = [a for a in aco_data if a["track_group"] == "BASIC"]
    enhanced = [a for a in aco_data if a["track_group"] == "ENHANCED"]
    print(f"  BASIC: {len(basic)}, ENHANCED: {len(enhanced)}")

    # Feature names (in order)
    feat_names = [fd[0] for fd in FEATURE_DEFS]
    feat_weights = [fd[2] for fd in FEATURE_DEFS]

    def compute_cohorts(partition: list[dict], partition_name: str) -> dict:
        """Compute KNN peer cohorts within a partition."""
        n = len(partition)
        if n < K_NEIGHBORS + 1:
            print(f"  WARNING: {partition_name} partition too small ({n})")
            return {}

        # Build feature matrix
        matrix = []
        for a in partition:
            row = [a["features"][fn] for fn in feat_names]
            matrix.append(row)

        # Z-score normalize within partition
        n_feat = len(feat_names)
        means = [statistics.mean([matrix[i][j] for i in range(n)]) for j in range(n_feat)]
        stds = [statistics.stdev([matrix[i][j] for i in range(n)]) if n > 1 else 1.0 for j in range(n_feat)]
        # Avoid division by zero
        stds = [s if s > 1e-10 else 1.0 for s in stds]

        z_matrix = [
            [(matrix[i][j] - means[j]) / stds[j] for j in range(n_feat)]
            for i in range(n)
        ]

        # MSSP-within-partition medians for description generation
        mssp_medians = {}
        for j, fn in enumerate(feat_names):
            vals = sorted([matrix[i][j] for i in range(n)])
            mssp_medians[fn] = vals[len(vals) // 2]

        # Compute all pairwise distances and find KNN
        cohorts = {}
        for i in range(n):
            dists = []
            for j in range(n):
                if i == j:
                    continue
                d = math.sqrt(sum(
                    feat_weights[k] * (z_matrix[i][k] - z_matrix[j][k]) ** 2
                    for k in range(n_feat)
                ))
                dists.append((d, j))
            dists.sort()
            peer_indices = [idx for _, idx in dists[:K_NEIGHBORS]]

            # Compute peer medians for key metrics
            peer_medians: dict[str, float] = {}
            for field in PEER_MEDIAN_FIELDS:
                vals = []
                for pi in peer_indices:
                    v = _pf(partition[pi]["raw"].get(field))
                    if v is not None:
                        vals.append(v)
                if vals:
                    vals.sort()
                    peer_medians[field] = vals[len(vals) // 2]

            # Peer IDs
            peer_ids = [partition[pi]["aco_id"] for pi in peer_indices]

            # Cohort description
            peer_features = [partition[pi]["features"] for pi in peer_indices]
            description = _cohort_description(
                partition_name, peer_features, mssp_medians
            )

            aco_id = partition[i]["aco_id"]
            cohorts[aco_id] = {
                "track_group": partition_name,
                "peer_ids": peer_ids,
                "peer_medians": peer_medians,
                "cohort_description": description,
            }

        return cohorts

    basic_cohorts = compute_cohorts(basic, "BASIC")
    enhanced_cohorts = compute_cohorts(enhanced, "ENHANCED")

    all_cohorts = {**basic_cohorts, **enhanced_cohorts}

    output = {
        "metadata": {
            "method": "knn-within-track-partition",
            "k": K_NEIGHBORS,
            "features": feat_names,
            "weights": {fd[1]: fd[2] for fd in FEATURE_DEFS},
            "basic_partition_size": len(basic),
            "enhanced_partition_size": len(enhanced),
            "total_with_cohorts": len(all_cohorts),
        },
        "cohorts": all_cohorts,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f)  # No indent — file is large

    print(f"  -> {output_path} ({len(all_cohorts)} cohorts)")
    return len(all_cohorts)
