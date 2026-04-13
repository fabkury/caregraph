/**
 * Shared dataset registry for the CareGraph Methodology pages.
 *
 * Single source of truth for dataset display metadata used by both
 * the Methodology hub (index.astro) and detail pages ([id].astro).
 */

export interface DatasetInfo {
  name: string;
  entity: string;
  vintage: string;
  /** base = creates entity pages; enrichment = adds data to existing pages; cross-link = links between entity types */
  role: 'base' | 'enrichment' | 'cross-link';
  /** Publishing agency */
  source: 'CMS' | 'CDC' | 'Medicaid';
}

export const datasetRegistry: Record<string, DatasetInfo> = {
  // ── Hospitals ─────────────────────────────────────────────────────
  'xubh-q36u': {
    name: 'Hospital General Information',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'base',
    source: 'CMS',
  },
  'hrrp': {
    name: 'Hospital Readmissions Reduction Program',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hvbp-tps': {
    name: 'Hospital Value-Based Purchasing TPS',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hosp-timely-care': {
    name: 'Timely and Effective Care — Hospital',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hosp-complications': {
    name: 'Complications and Deaths — Hospital',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hosp-hcahps': {
    name: 'Patient Survey (HCAHPS) — Hospital',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hosp-hai': {
    name: 'Healthcare Associated Infections — Hospital',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CDC',
  },
  'hosp-unplanned-visits': {
    name: 'Unplanned Hospital Visits — Hospital',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hosp-mspb': {
    name: 'Medicare Spending Per Beneficiary — Hospital',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'hosp-cost-report': {
    name: 'Hospital Provider Cost Report',
    entity: 'hospital',
    vintage: 'FY2023',
    role: 'enrichment',
    source: 'CMS',
  },
  'hac-reduction': {
    name: 'Hospital-Acquired Condition (HAC) Reduction Program',
    entity: 'hospital',
    vintage: 'FY2026',
    role: 'enrichment',
    source: 'CMS',
  },

  // ── Skilled Nursing Facilities ────────────────────────────────────
  'nh-provider-info': {
    name: 'Nursing Home Provider Info',
    entity: 'snf',
    vintage: 'Mar 2026',
    role: 'base',
    source: 'CMS',
  },
  'nh-quality-mds': {
    name: 'SNF Quality Measures (MDS)',
    entity: 'snf',
    vintage: 'Mar 2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'nh-penalties': {
    name: 'Nursing Home Penalties',
    entity: 'snf',
    vintage: 'Mar 2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'nh-deficiencies': {
    name: 'Nursing Home Health Deficiencies',
    entity: 'snf',
    vintage: 'Mar 2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'nh-ownership': {
    name: 'Nursing Home Ownership',
    entity: 'snf',
    vintage: 'Mar 2026',
    role: 'enrichment',
    source: 'CMS',
  },
  'snf-cost-report': {
    name: 'Skilled Nursing Facility Cost Report',
    entity: 'snf',
    vintage: 'FY2023',
    role: 'enrichment',
    source: 'CMS',
  },

  // ── Counties ──────────────────────────────────────────────────────
  'geo-var-county': {
    name: 'Medicare Geographic Variation by County',
    entity: 'county',
    vintage: '2014–2023',
    role: 'base',
    source: 'CMS',
  },
  'cdc-places': {
    name: 'CDC PLACES County-Level Data',
    entity: 'county',
    vintage: '2023 Release',
    role: 'enrichment',
    source: 'CDC',
  },
  'cdc-sdoh': {
    name: 'CDC SDOH Measures for County',
    entity: 'county',
    vintage: '2023 Release',
    role: 'enrichment',
    source: 'CDC',
  },
  'cms-chronic-conditions': {
    name: 'Medicare Specific Chronic Conditions by County',
    entity: 'county',
    vintage: '2023',
    role: 'enrichment',
    source: 'CMS',
  },

  // ── ACOs ──────────────────────────────────────────────────────────
  'mssp-performance': {
    name: 'MSSP ACO Performance PY2024',
    entity: 'aco',
    vintage: 'PY2024',
    role: 'base',
    source: 'CMS',
  },
  'aco-participants': {
    name: 'ACO Participants',
    entity: 'aco',
    vintage: 'PY2024',
    role: 'cross-link',
    source: 'CMS',
  },
  'aco-snf-affiliates': {
    name: 'ACO SNF Affiliates',
    entity: 'aco',
    vintage: 'PY2024',
    role: 'cross-link',
    source: 'CMS',
  },
  'aco-bene-county': {
    name: 'ACO Assigned Beneficiaries by County',
    entity: 'aco',
    vintage: 'PY2023',
    role: 'cross-link',
    source: 'CMS',
  },

  // ── Drugs ─────────────────────────────────────────────────────────
  'partd-drug-spending': {
    name: 'Medicare Part D Spending by Drug',
    entity: 'drug',
    vintage: 'CY2023',
    role: 'base',
    source: 'CMS',
  },
  'partb-drug-spending': {
    name: 'Medicare Part B Spending by Drug',
    entity: 'drug',
    vintage: 'CY2023',
    role: 'enrichment',
    source: 'CMS',
  },
  'partb-discarded-units': {
    name: 'Medicare Part B Discarded Drug Units',
    entity: 'drug',
    vintage: 'CY2023',
    role: 'enrichment',
    source: 'CMS',
  },
  'nadac': {
    name: 'NADAC National Average Drug Acquisition Cost',
    entity: 'drug',
    vintage: '2026 (weekly)',
    role: 'enrichment',
    source: 'Medicaid',
  },

  // ── Conditions ────────────────────────────────────────────────────
  // CDC PLACES is listed under counties; conditions are derived from
  // the same dataset by aggregating across counties per measure.
  // No additional base dataset — condition pages are built from cdc-places.

  // ── DRGs ──────────────────────────────────────────────────────────
  'inpatient-by-drg': {
    name: 'Medicare Inpatient Hospitals by Provider and Service (DRG)',
    entity: 'drg',
    vintage: 'CY2023',
    role: 'base',
    source: 'CMS',
  },
};

/** Entity type display names (title case, pluralized) */
export const entityLabels: Record<string, string> = {
  hospital: 'Hospitals',
  snf: 'Skilled Nursing Facilities',
  county: 'Counties',
  aco: 'ACOs',
  drug: 'Drugs',
  condition: 'Conditions',
  drg: 'DRGs',
};

/** Ordered list of entity types for consistent section rendering */
export const entityOrder = ['hospital', 'snf', 'county', 'aco', 'drug', 'condition', 'drg'] as const;
