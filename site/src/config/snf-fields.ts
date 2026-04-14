/**
 * SNF (Skilled Nursing Facility) field mapping configuration.
 *
 * Provides the labels, thresholds, scope/severity matrix, footnote decoder,
 * and help copy used by the SNF detail page. Raw field names mirror the
 * human-readable headers CMS ships in the Nursing Home Provider Info file.
 */

// ── Section labels for All Data grouping ────────────────────────────

export const SNF_GROUP_LABELS: Record<string, string> = {
  provider_info: 'Provider Information',
  penalties: 'Penalties',
  deficiencies: 'Deficiencies',
  ownership: 'Ownership',
  cost_report: 'Cost Report',
};

// ── Staffing role definitions ──────────────────────────────────────

export interface StaffingRole {
  /** Short display name (e.g., "RN"). */
  label: string;
  /** Longer name for tooltip / description. */
  detail: string;
  /** Field name in provider_info for reported hours. */
  reportedKey: string;
  /** Case-mix adjusted field (what would be expected for resident acuity). */
  caseMixKey?: string;
  /** Adjusted field (CMS's final rating-input value). */
  adjustedKey?: string;
  /** Federal safety floor (hours per resident per day), if any. */
  floor?: number;
  /** Source/citation for the floor. */
  floorSource?: string;
}

export const STAFFING_ROLES: StaffingRole[] = [
  {
    label: 'Total nurse',
    detail: 'All nursing staff combined: RN + LPN + Aide',
    reportedKey: 'Reported Total Nurse Staffing Hours per Resident per Day',
    caseMixKey: 'Case-Mix Total Nurse Staffing Hours per Resident per Day',
    adjustedKey: 'Adjusted Total Nurse Staffing Hours per Resident per Day',
    floor: 3.48,
    floorSource: 'CMS 2024 minimum staffing rule (phasing in)',
  },
  {
    label: 'Registered Nurse (RN)',
    detail: 'Licensed RN hours. Strongest driver of clinical outcomes.',
    reportedKey: 'Reported RN Staffing Hours per Resident per Day',
    caseMixKey: 'Case-Mix RN Staffing Hours per Resident per Day',
    adjustedKey: 'Adjusted RN Staffing Hours per Resident per Day',
    floor: 0.55,
    floorSource: 'CMS 2024 minimum staffing rule (phasing in)',
  },
  {
    label: 'Licensed Practical Nurse (LPN)',
    detail: 'LPN/LVN hours. Often handles medication administration.',
    reportedKey: 'Reported LPN Staffing Hours per Resident per Day',
    caseMixKey: 'Case-Mix LPN Staffing Hours per Resident per Day',
    adjustedKey: 'Adjusted LPN Staffing Hours per Resident per Day',
  },
  {
    label: 'Nurse aide',
    detail: 'CNA hours. Bulk of direct resident care — bathing, feeding, mobility.',
    reportedKey: 'Reported Nurse Aide Staffing Hours per Resident per Day',
    caseMixKey: 'Case-Mix Nurse Aide Staffing Hours per Resident per Day',
    adjustedKey: 'Adjusted Nurse Aide Staffing Hours per Resident per Day',
  },
  {
    label: 'Licensed (RN + LPN)',
    detail: 'Combined licensed nurse coverage.',
    reportedKey: 'Reported Licensed Staffing Hours per Resident per Day',
  },
  {
    label: 'Physical therapist',
    detail: 'Rehabilitation therapist hours — important for post-acute / rehab admissions.',
    reportedKey: 'Reported Physical Therapist Staffing Hours per Resident Per Day',
  },
];

export const WEEKEND_STAFFING_FIELDS = {
  totalWeekend: 'Total number of nurse staff hours per resident per day on the weekend',
  rnWeekend: 'Registered Nurse hours per resident per day on the weekend',
  adjustedTotal: 'Adjusted Weekend Total Nurse Staffing Hours per Resident per Day',
  caseMixTotal: 'Case-Mix Weekend Total Nurse Staffing Hours per Resident per Day',
};

export const TURNOVER_FIELDS = {
  totalNursing: 'Total nursing staff turnover',
  rn: 'Registered Nurse turnover',
  admin: 'Number of administrators who have left the nursing home',
};

export const CASE_MIX_FIELDS = {
  index: 'Nursing Case-Mix Index',
  ratio: 'Nursing Case-Mix Index Ratio',
};

// ── Scope / Severity matrix (CMS A–L scale) ────────────────────────

export interface SeverityBand {
  codes: string[];
  label: string;
  color: string;
  bg: string;
  order: number;
}

export const SEVERITY_BANDS: SeverityBand[] = [
  {
    codes: ['A', 'B', 'C'],
    label: 'No actual harm — minor',
    color: '#374151',
    bg: '#f3f4f6',
    order: 1,
  },
  {
    codes: ['D', 'E', 'F'],
    label: 'Actual harm — potential for minor',
    color: '#854d0e',
    bg: '#fef9c3',
    order: 2,
  },
  {
    codes: ['G', 'H', 'I'],
    label: 'Actual harm',
    color: '#9a3412',
    bg: '#ffedd5',
    order: 3,
  },
  {
    codes: ['J', 'K', 'L'],
    label: 'Immediate jeopardy',
    color: '#991b1b',
    bg: '#fee2e2',
    order: 4,
  },
];

export function severityBand(code: string | undefined | null): SeverityBand | null {
  if (!code) return null;
  const first = code.trim().charAt(0).toUpperCase();
  for (const b of SEVERITY_BANDS) {
    if (b.codes.includes(first)) return b;
  }
  return null;
}

// ── Footnote decoder ───────────────────────────────────────────────
//
// CMS ships footnote codes on several rating fields. We decode the most
// common ones. Unknown codes fall back to "Footnote N".

export const FOOTNOTE_TEXT: Record<string, string> = {
  '1': 'New facility — too new to be rated.',
  '2': 'Data not available.',
  '3': 'Results are based on a shorter period.',
  '4': 'Results are based on a shorter period.',
  '5': 'New measure — no historical data yet.',
  '6': 'Data suppressed for small denominators.',
  '7': 'Data suppressed — too few residents.',
  '8': 'Results are not reliable.',
  '9': 'Fewer than 20 residents.',
  '11': 'Rating based on three-year cycle.',
  '17': 'New or recently certified — limited history.',
  '19': 'Staffing data not submitted or failed integrity review.',
  '20': 'Data not available — PBJ submission issue.',
  '21': 'Imputed due to missing data.',
  '25': 'Resident count too small for reliable rating.',
  '26': 'New facility — insufficient data.',
  '27': 'Staffing penalized (missing PBJ submission).',
};

export function decodeFootnote(code: string | undefined | null): string | null {
  if (!code) return null;
  const trimmed = String(code).trim();
  if (!trimmed) return null;
  return FOOTNOTE_TEXT[trimmed] ?? `Footnote ${trimmed}.`;
}

// ── Special Focus Facility copy ────────────────────────────────────

export const SFF_COPY = {
  sff: {
    title: 'Special Focus Facility',
    body: 'CMS has designated this nursing home as a Special Focus Facility — a persistent pattern of serious quality problems. SFFs are surveyed twice as often as other facilities and face escalating enforcement.',
  },
  candidate: {
    title: 'SFF Candidate',
    body: 'CMS has identified this nursing home as a candidate for the Special Focus Facility program — a history of serious quality issues that may escalate to full SFF status.',
  },
  abuse: {
    title: 'Abuse citation in last 2 cycles',
    body: 'CMS flagged this facility for abuse or neglect citations within the last two standard-survey cycles (Care Compare "abuse icon").',
  },
};

// ── Ownership type descriptions ────────────────────────────────────

export const OWNERSHIP_TYPE_COPY: Record<string, string> = {
  'For profit - Corporation': 'For-profit corporation',
  'For profit - Limited Liability company': 'For-profit LLC',
  'For profit - Individual': 'For-profit (individual owner)',
  'For profit - Partnership': 'For-profit partnership',
  'Non profit - Corporation': 'Non-profit corporation',
  'Non profit - Church related': 'Non-profit (church-affiliated)',
  'Non profit - Other': 'Non-profit (other)',
  'Government - City': 'Government (city)',
  'Government - City/county': 'Government (city/county)',
  'Government - County': 'Government (county)',
  'Government - State': 'Government (state)',
  'Government - Federal': 'Government (federal)',
  'Government - Hospital district': 'Government (hospital district)',
};

// ── Cost report metric metadata ────────────────────────────────────

export interface CostMetricDef {
  key: string;
  label: string;
  format: 'percent' | 'dollar' | 'ratio';
  /** Positive value = good direction by default. */
  higherIsBetter?: boolean;
}

export const COST_METRICS_OPERATING: CostMetricDef[] = [
  { key: 'operating_margin', label: 'Operating Margin', format: 'percent', higherIsBetter: true },
  { key: 'total_margin', label: 'Total Margin', format: 'percent', higherIsBetter: true },
  { key: 'occupancy_rate', label: 'Occupancy Rate', format: 'percent', higherIsBetter: true },
  { key: 'cost_per_resident_day', label: 'Cost per Resident Day', format: 'dollar' },
];

export const COST_METRICS_INCOME: CostMetricDef[] = [
  { key: 'net_patient_revenue', label: 'Net Patient Revenue', format: 'dollar' },
  { key: 'total_costs', label: 'Total Costs', format: 'dollar' },
  { key: 'net_income', label: 'Net Income', format: 'dollar', higherIsBetter: true },
];

export const COST_METRICS_BALANCE: CostMetricDef[] = [
  { key: 'total_assets', label: 'Total Assets', format: 'dollar' },
  { key: 'total_liabilities', label: 'Total Liabilities', format: 'dollar' },
  { key: 'fund_balance', label: 'Fund Balance', format: 'dollar', higherIsBetter: true },
  { key: 'current_ratio', label: 'Current Ratio', format: 'ratio', higherIsBetter: true },
];

export function formatCostValue(val: number | null | undefined, format: 'percent' | 'dollar' | 'ratio'): string {
  if (val === null || val === undefined || !isFinite(val)) return '\u2014';
  if (format === 'percent') return val.toFixed(1) + '%';
  if (format === 'dollar') {
    const abs = Math.abs(val);
    if (abs >= 1_000_000) return (val < 0 ? '-$' : '$') + (abs / 1_000_000).toFixed(1) + 'M';
    if (abs >= 1_000) return (val < 0 ? '-$' : '$') + (abs / 1_000).toFixed(0) + 'K';
    return (val < 0 ? '-$' : '$') + Math.round(abs).toLocaleString();
  }
  return val.toFixed(2);
}

// ── Flag definitions (for the hero badges row) ─────────────────────

export interface FlagDef {
  /** Raw provider_info key. */
  key: string;
  /** Only fire on "Y" (otherwise compares equal to truthyValue). */
  truthyValue?: string;
  /** Class on the pill: 'warn' | 'alert' | 'info'. */
  tone: 'warn' | 'alert' | 'info';
  label: string;
  tooltip: string;
}

export const FACILITY_FLAGS: FlagDef[] = [
  {
    key: 'Special Focus Status',
    truthyValue: 'SFF',
    tone: 'alert',
    label: 'Special Focus Facility',
    tooltip: SFF_COPY.sff.body,
  },
  {
    key: 'Special Focus Status',
    truthyValue: 'SFF Candidate',
    tone: 'warn',
    label: 'SFF Candidate',
    tooltip: SFF_COPY.candidate.body,
  },
  {
    key: 'Abuse Icon',
    truthyValue: 'Y',
    tone: 'alert',
    label: 'Abuse citation flag',
    tooltip: SFF_COPY.abuse.body,
  },
  {
    key: 'Most Recent Health Inspection More Than 2 Years Ago',
    truthyValue: 'Y',
    tone: 'warn',
    label: 'Inspection > 2 years ago',
    tooltip: 'CMS recommends at least one standard survey every 12-15 months. This facility has not been inspected for more than two years.',
  },
  {
    key: 'Provider Changed Ownership in Last 12 Months',
    truthyValue: 'Y',
    tone: 'warn',
    label: 'Changed ownership < 12 mo',
    tooltip: 'Ownership change within the last year. Ratings may not fully reflect the new operator.',
  },
  {
    key: 'Continuing Care Retirement Community',
    truthyValue: 'Y',
    tone: 'info',
    label: 'CCRC',
    tooltip: 'Continuing Care Retirement Community — offers independent living, assisted living, and skilled nursing on one campus.',
  },
  {
    key: 'Provider Resides in Hospital',
    truthyValue: 'Y',
    tone: 'info',
    label: 'Hospital-based',
    tooltip: 'Hospital-based SNF — located inside or colocated with a Medicare-certified hospital. Typically handles higher-acuity post-acute patients.',
  },
];
