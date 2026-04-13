/**
 * Hospital field mapping configuration.
 *
 * Maps raw CMS field names to human-readable labels, groups them into
 * clinically meaningful sections, and defines formatting/display rules.
 * Used by the hospital [ccn].astro page to render the unified view.
 */

// ── Types ────────────────────────────────────────────────────────────

export type FieldFormat =
  | 'dollar'
  | 'percent'
  | 'decimal2'
  | 'decimal4'
  | 'integer'
  | 'ratio'
  | 'text'
  | 'boolean'
  | 'star';

export interface FieldDef {
  key: string;
  label: string;
  format: FieldFormat;
  /** For metrics where lower = better (e.g., readmission ratios) */
  lowerIsBetter?: boolean;
  /** Short tooltip / help text */
  help?: string;
}

// ── Hospital type descriptions ──────────────────────────────────────

export const HOSPITAL_TYPE_INFO: Record<string, { short: string; detail: string }> = {
  'Acute Care Hospitals': {
    short: 'Acute Care',
    detail: 'General medical and surgical hospital participating in Medicare IPPS. Subject to CMS quality reporting and payment adjustment programs (VBP, HRRP, HAC).',
  },
  'Critical Access Hospitals': {
    short: 'Critical Access (CAH)',
    detail: 'Small rural hospital (≤25 inpatient beds) at least 35 miles from the nearest hospital. Reimbursed at 101% of cost rather than standard DRG rates. Exempt from most CMS payment adjustment programs.',
  },
  'Psychiatric': {
    short: 'Psychiatric',
    detail: 'Inpatient psychiatric facility. Paid under the Inpatient Psychiatric Facility PPS, not IPPS. Not subject to hospital VBP, HRRP, or HAC programs.',
  },
  'Acute Care - Veterans Administration': {
    short: 'VA Hospital',
    detail: 'Department of Veterans Affairs medical center. Federally operated — does not participate in Medicare payment programs but voluntarily reports some quality data.',
  },
  'Childrens': {
    short: "Children's Hospital",
    detail: "Pediatric specialty hospital. Exempt from standard IPPS and most adult-focused CMS quality programs. May participate in voluntary quality reporting.",
  },
  'Rural Emergency Hospital': {
    short: 'Rural Emergency (REH)',
    detail: 'New designation (2023). Provides emergency and outpatient services only — no inpatient beds. Former Critical Access or small rural hospitals that converted to maintain emergency access.',
  },
  'Acute Care - Department of Defense': {
    short: 'DoD Hospital',
    detail: 'Department of Defense military medical facility. Federally operated — does not participate in Medicare payment programs.',
  },
  'Long-term': {
    short: 'Long-Term Care (LTCH)',
    detail: 'Long-term care hospital with average length of stay ≥25 days. Treats patients with complex medical needs requiring extended hospitalization. Paid under LTCH PPS.',
  },
};

// ── Ownership category mapping ──────────────────────────────────────

export const OWNERSHIP_CATEGORIES: Record<string, string> = {
  'Voluntary non-profit - Private': 'Non-Profit',
  'Voluntary non-profit - Church': 'Non-Profit (Church)',
  'Voluntary non-profit - Other': 'Non-Profit (Other)',
  'Proprietary': 'For-Profit',
  'Government - Hospital District or Authority': 'Government (District)',
  'Government - Local': 'Government (Local)',
  'Government - State': 'Government (State)',
  'Government - Federal': 'Government (Federal)',
  'Tribal': 'Tribal',
  'Physician': 'Physician-Owned',
};

// ── HRRP condition labels & descriptions ────────────────────────────

export interface HrrpCondition {
  measureId: string;
  label: string;
  shortLabel: string;
  help: string;
}

export const HRRP_CONDITIONS: HrrpCondition[] = [
  {
    measureId: 'READM-30-AMI-HRRP',
    label: 'Acute Myocardial Infarction (Heart Attack)',
    shortLabel: 'AMI',
    help: '30-day readmission rate after hospitalization for heart attack.',
  },
  {
    measureId: 'READM-30-HF-HRRP',
    label: 'Heart Failure',
    shortLabel: 'HF',
    help: '30-day readmission rate after hospitalization for heart failure.',
  },
  {
    measureId: 'READM-30-PN-HRRP',
    label: 'Pneumonia',
    shortLabel: 'PN',
    help: '30-day readmission rate after hospitalization for pneumonia.',
  },
  {
    measureId: 'READM-30-COPD-HRRP',
    label: 'COPD',
    shortLabel: 'COPD',
    help: '30-day readmission rate after hospitalization for chronic obstructive pulmonary disease.',
  },
  {
    measureId: 'READM-30-HIP-KNEE-HRRP',
    label: 'Hip/Knee Replacement',
    shortLabel: 'Hip/Knee',
    help: '30-day readmission rate after elective hip or knee replacement surgery.',
  },
  {
    measureId: 'READM-30-CABG-HRRP',
    label: 'CABG Surgery',
    shortLabel: 'CABG',
    help: '30-day readmission rate after coronary artery bypass graft surgery.',
  },
];

// ── VBP domain definitions ──────────────────────────────────────────

export interface VbpDomain {
  key: string;
  label: string;
  weight: number;
  help: string;
}

export const VBP_DOMAINS: VbpDomain[] = [
  {
    key: 'total_performance_score',
    label: 'Total Performance Score',
    weight: 100,
    help: 'Weighted composite of all four domain scores. Determines the magnitude and direction of a hospital\'s Medicare payment adjustment.',
  },
  {
    key: 'clinical_outcomes_score',
    label: 'Clinical Outcomes',
    weight: 25,
    help: 'Measures mortality rates for conditions like heart attack, heart failure, pneumonia, and COPD. Based on 30-day risk-standardized mortality.',
  },
  {
    key: 'safety_score',
    label: 'Safety',
    weight: 25,
    help: 'Patient safety measures including healthcare-associated infections (CLABSI, CAUTI, SSI, MRSA, C. diff) and perioperative complications.',
  },
  {
    key: 'person_community_score',
    label: 'Person & Community Engagement',
    weight: 25,
    help: 'Based on HCAHPS patient experience survey results — communication with nurses and doctors, hospital cleanliness, pain management, discharge information.',
  },
  {
    key: 'efficiency_score',
    label: 'Efficiency & Cost Reduction',
    weight: 25,
    help: 'Based on Medicare Spending Per Beneficiary (MSPB). Measures episode-of-care costs from 3 days before admission through 30 days after discharge.',
  },
];

// ── CMS Star Rating domains ────────────────────────────────────────

export interface StarDomain {
  id: string;
  label: string;
  groupCountKey: string;
  facilityCountKey: string;
  betterKey: string | null;
  noDiffKey: string | null;
  worseKey: string | null;
  footnoteKey: string;
  help: string;
}

export const STAR_DOMAINS: StarDomain[] = [
  {
    id: 'mortality',
    label: 'Mortality',
    groupCountKey: 'MORT Group Measure Count',
    facilityCountKey: 'Count of Facility MORT Measures',
    betterKey: 'Count of MORT Measures Better',
    noDiffKey: 'Count of MORT Measures No Different',
    worseKey: 'Count of MORT Measures Worse',
    footnoteKey: 'MORT Group Footnote',
    help: '30-day death rates for heart attack, heart failure, pneumonia, COPD, stroke, CABG, and kidney disease.',
  },
  {
    id: 'safety',
    label: 'Safety of Care',
    groupCountKey: 'Safety Group Measure Count',
    facilityCountKey: 'Count of Facility Safety Measures',
    betterKey: 'Count of Safety Measures Better',
    noDiffKey: 'Count of Safety Measures No Different',
    worseKey: 'Count of Safety Measures Worse',
    footnoteKey: 'Safety Group Footnote',
    help: 'Healthcare-associated infections and patient safety indicators (PSI-90 composite).',
  },
  {
    id: 'readmission',
    label: 'Readmission',
    groupCountKey: 'READM Group Measure Count',
    facilityCountKey: 'Count of Facility READM Measures',
    betterKey: 'Count of READM Measures Better',
    noDiffKey: 'Count of READM Measures No Different',
    worseKey: 'Count of READM Measures Worse',
    footnoteKey: 'READM Group Footnote',
    help: '30-day unplanned readmission rates for heart attack, heart failure, pneumonia, COPD, hip/knee replacement, and CABG.',
  },
  {
    id: 'patient_experience',
    label: 'Patient Experience',
    groupCountKey: 'Pt Exp Group Measure Count',
    facilityCountKey: 'Count of Facility Pt Exp Measures',
    betterKey: null,
    noDiffKey: null,
    worseKey: null,
    footnoteKey: 'Pt Exp Group Footnote',
    help: 'HCAHPS survey scores — patient-reported experience with communication, responsiveness, cleanliness, and discharge planning.',
  },
  {
    id: 'timely_effective',
    label: 'Timely & Effective Care',
    groupCountKey: 'TE Group Measure Count',
    facilityCountKey: 'Count of Facility TE Measures',
    betterKey: null,
    noDiffKey: null,
    worseKey: null,
    footnoteKey: 'TE Group Footnote',
    help: 'Process-of-care measures including flu immunization, blood clot prevention, and appropriate use of imaging.',
  },
];

// ── Payment program definitions ─────────────────────────────────────

export interface PaymentProgram {
  id: string;
  name: string;
  shortName: string;
  help: string;
}

export const PAYMENT_PROGRAMS: PaymentProgram[] = [
  {
    id: 'hrrp',
    name: 'Hospital Readmissions Reduction Program',
    shortName: 'HRRP',
    help: 'Reduces Medicare payments to hospitals with excess readmissions for AMI, HF, pneumonia, COPD, hip/knee replacement, and CABG. Maximum penalty: 3% of base DRG payments.',
  },
  {
    id: 'vbp',
    name: 'Hospital Value-Based Purchasing',
    shortName: 'VBP',
    help: 'Adjusts Medicare payments (up or down) based on clinical outcomes, safety, patient experience, and efficiency. Funded by a 2% withhold from base DRG payments.',
  },
  {
    id: 'hac',
    name: 'Hospital-Acquired Condition Reduction Program',
    shortName: 'HAC',
    help: 'Reduces Medicare payments by 1% for hospitals in the worst-performing quartile on HAC measures (healthcare-associated infections and patient safety indicators).',
  },
];

// ── Benchmark key mapping ───────────────────────────────────────────

/** Maps display context to benchmark keys in hospital_benchmarks.json */
export const BENCHMARK_KEYS = {
  vbp_tps: 'vbp.total_performance_score',
  vbp_clinical: 'vbp.clinical_outcomes_score',
  vbp_safety: 'vbp.safety_score',
  vbp_person: 'vbp.person_community_score',
  vbp_efficiency: 'vbp.efficiency_score',
  hrrp_worst: 'hrrp.worst_err',
  hrrp_avg: 'hrrp.avg_err',
  star: 'star_rating',
} as const;
