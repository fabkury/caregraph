/**
 * County field mapping configuration.
 *
 * Drives the unified [fips].astro page: labels, grouping, formatting,
 * and whether "lower is better" (for colouring percentile badges).
 *
 * Keys match the columns in the Medicare Geographic Variation PUF for
 * fields under `gv.*`; PLACES measure IDs under `places.*`; and SDOH
 * keys (from enrich_tier_a.py) under `sdoh.*`.
 */

export type FieldFormat =
  | 'dollar'
  | 'dollar_large'
  | 'percent'        // value already expressed 0-1 (multiply by 100)
  | 'percent_raw'    // value already expressed 0-100
  | 'decimal1'
  | 'decimal2'
  | 'integer'
  | 'rate_per_1k'
  | 'rate_per_100k';

export interface FieldDef {
  key: string;
  label: string;
  format: FieldFormat;
  lowerIsBetter?: boolean;
  help?: string;
}

// ── Beneficiary profile ────────────────────────────────────────────

export const BENEFICIARY_FIELDS: FieldDef[] = [
  { key: 'BENES_TOTAL_CNT', label: 'Total Medicare Beneficiaries', format: 'integer' },
  { key: 'BENES_FFS_CNT',   label: 'Fee-for-Service Beneficiaries', format: 'integer' },
  { key: 'BENES_MA_CNT',    label: 'Medicare Advantage Beneficiaries', format: 'integer' },
  { key: 'MA_PRTCPTN_RATE', label: 'MA Participation Rate', format: 'percent' },
  { key: 'BENE_AVG_AGE',    label: 'Average Age', format: 'decimal1' },
  { key: 'BENE_AVG_RISK_SCRE', label: 'Average HCC Risk Score', format: 'decimal2',
    help: 'CMS Hierarchical Condition Category score. Higher means a sicker average beneficiary.' },
  { key: 'BENE_DUAL_PCT',   label: 'Dual Eligible (Medicare + Medicaid)', format: 'percent',
    help: 'Share of beneficiaries also enrolled in Medicaid — a marker of low income and complex need.' },
];

export const DEMOGRAPHICS_FIELDS: FieldDef[] = [
  { key: 'BENE_FEML_PCT',        label: 'Female', format: 'percent' },
  { key: 'BENE_MALE_PCT',        label: 'Male',   format: 'percent' },
  { key: 'BENE_RACE_WHT_PCT',    label: 'White',  format: 'percent' },
  { key: 'BENE_RACE_BLACK_PCT',  label: 'Black',  format: 'percent' },
  { key: 'BENE_RACE_HSPNC_PCT',  label: 'Hispanic', format: 'percent' },
  { key: 'BENE_RACE_OTHR_PCT',   label: 'Other race', format: 'percent' },
];

// ── Spending — per-capita standardized by setting ──────────────────
//
// For the composition chart we want the *share* of total standardized
// spending that goes to each setting. We derive it from `*_MDCR_STDZD_PYMT_PCT`
// when present; otherwise fall back to `*_MDCR_STDZD_PYMT_PC` divided by
// TOT_MDCR_STDZD_PYMT_PC.

export interface ServiceSetting {
  prefix: string;
  label: string;
  color: string;
  /** "events" for service-specific utilization column picks below */
  utilizationCol: string;
  utilizationLabel: string;
  beneUserCol: string;
}

export const SERVICE_SETTINGS: ServiceSetting[] = [
  { prefix: 'IP',       label: 'Inpatient',               color: '#2563eb',
    utilizationCol: 'IP_CVRD_STAYS_PER_1000_BENES', utilizationLabel: 'stays / 1k',
    beneUserCol: 'BENES_IP_PCT' },
  { prefix: 'OP',       label: 'Outpatient Hospital',     color: '#7c3aed',
    utilizationCol: 'OP_VISITS_PER_1000_BENES', utilizationLabel: 'visits / 1k',
    beneUserCol: 'BENES_OP_PCT' },
  { prefix: 'EM',       label: 'Evaluation & Mgmt (E/M)', color: '#0891b2',
    utilizationCol: 'EM_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_EM_PCT' },
  { prefix: 'PRCDRS',   label: 'Procedures',              color: '#c026d3',
    utilizationCol: 'PRCDR_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_PRCDRS_PCT' },
  { prefix: 'IMGNG',    label: 'Imaging',                 color: '#db2777',
    utilizationCol: 'IMGNG_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_IMGNG_PCT' },
  { prefix: 'TESTS',    label: 'Tests',                   color: '#ea580c',
    utilizationCol: 'TESTS_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_TESTS_PCT' },
  { prefix: 'SNF',      label: 'Skilled Nursing (SNF)',   color: '#d97706',
    utilizationCol: 'SNF_CVRD_STAYS_PER_1000_BENES', utilizationLabel: 'stays / 1k',
    beneUserCol: 'BENES_SNF_PCT' },
  { prefix: 'HH',       label: 'Home Health',             color: '#059669',
    utilizationCol: 'HH_EPISODES_PER_1000_BENES', utilizationLabel: 'episodes / 1k',
    beneUserCol: 'BENES_HH_PCT' },
  { prefix: 'HOSPC',    label: 'Hospice',                 color: '#16a34a',
    utilizationCol: 'HOSPC_CVRD_STAYS_PER_1000_BENES', utilizationLabel: 'stays / 1k',
    beneUserCol: 'BENES_HOSPC_PCT' },
  { prefix: 'IRF',      label: 'Inpatient Rehab',         color: '#f97316',
    utilizationCol: 'IRF_CVRD_STAYS_PER_1000_BENES', utilizationLabel: 'stays / 1k',
    beneUserCol: 'BENES_IRF_PCT' },
  { prefix: 'LTCH',     label: 'Long-Term Care Hospital', color: '#be185d',
    utilizationCol: 'LTCH_CVRD_STAYS_PER_1000_BENES', utilizationLabel: 'stays / 1k',
    beneUserCol: 'BENES_LTCH_PCT' },
  { prefix: 'ASC',      label: 'Ambulatory Surgery Ctr',  color: '#8b5cf6',
    utilizationCol: 'ASC_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_ASC_PCT' },
  { prefix: 'DME',      label: 'Durable Medical Equip',   color: '#475569',
    utilizationCol: 'DME_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_DME_PCT' },
  { prefix: 'OP_DLYS',  label: 'Part B Drugs (OP)',       color: '#0ea5e9',
    utilizationCol: 'OP_DLYS_VISITS_PER_1000_BENES', utilizationLabel: 'visits / 1k',
    beneUserCol: 'BENES_OP_DLYS_PCT' },
  { prefix: 'FQHC_RHC', label: 'FQHC / Rural Health',     color: '#65a30d',
    utilizationCol: 'FQHC_RHC_VISITS_PER_1000_BENES', utilizationLabel: 'visits / 1k',
    beneUserCol: 'BENES_FQHC_RHC_PCT' },
  { prefix: 'AMBLNC',   label: 'Ambulance',               color: '#dc2626',
    utilizationCol: 'AMBLNC_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_AMBLNC_PCT' },
  { prefix: 'TRTMNTS',  label: 'Treatments',              color: '#9333ea',
    utilizationCol: 'TRTMNTS_EVNTS_PER_1000_BENES', utilizationLabel: 'events / 1k',
    beneUserCol: 'BENES_TRTMNTS_PCT' },
];

// ── Utilization-only / combined outcomes ───────────────────────────

export const UTILIZATION_HEADLINE_FIELDS: FieldDef[] = [
  { key: 'ACUTE_HOSP_READMSN_PCT', label: '30-Day Readmission Rate', format: 'percent',
    lowerIsBetter: true,
    help: 'Share of hospital discharges followed by an unplanned readmission within 30 days.' },
  { key: 'ER_VISITS_PER_1000_BENES', label: 'ER Visits per 1,000 Benes',
    format: 'rate_per_1k', lowerIsBetter: true },
  { key: 'BENES_ER_VISITS_PCT', label: 'Beneficiaries With ≥1 ER Visit',
    format: 'percent', lowerIsBetter: true },
];

// ── AHRQ Prevention Quality Indicators (preventable admissions) ────

export interface PqiCondition {
  label: string;
  help: string;
  ageBands: { label: string; key: string }[];
}

export const PQI_CONDITIONS: PqiCondition[] = [
  {
    label: 'Diabetes short-term complications',
    help: 'PQI-03 — admissions for diabetes short-term complications per 100,000 population.',
    ageBands: [
      { label: '<65', key: 'PQI03_DBTS_AGE_LT_65' },
      { label: '65–74', key: 'PQI03_DBTS_AGE_65_74' },
      { label: '75+',  key: 'PQI03_DBTS_AGE_GE_75' },
    ],
  },
  {
    label: 'COPD / asthma (older adults)',
    help: 'PQI-05 — admissions for COPD or asthma in older adults per 100,000.',
    ageBands: [
      { label: '40–64', key: 'PQI05_COPD_ASTHMA_AGE_40_64' },
      { label: '65–74', key: 'PQI05_COPD_ASTHMA_AGE_65_74' },
      { label: '75+',   key: 'PQI05_COPD_ASTHMA_AGE_GE_75' },
    ],
  },
  {
    label: 'Hypertension',
    help: 'PQI-07 — admissions for uncontrolled hypertension per 100,000.',
    ageBands: [
      { label: '<65', key: 'PQI07_HYPRTNSN_AGE_LT_65' },
      { label: '65–74', key: 'PQI07_HYPRTNSN_AGE_65_74' },
      { label: '75+',  key: 'PQI07_HYPRTNSN_AGE_GE_75' },
    ],
  },
  {
    label: 'Heart failure',
    help: 'PQI-08 — admissions for congestive heart failure per 100,000.',
    ageBands: [
      { label: '<65', key: 'PQI08_CHF_AGE_LT_65' },
      { label: '65–74', key: 'PQI08_CHF_AGE_65_74' },
      { label: '75+',  key: 'PQI08_CHF_AGE_GE_75' },
    ],
  },
  {
    label: 'Bacterial pneumonia',
    help: 'PQI-11 — admissions for community-acquired bacterial pneumonia per 100,000.',
    ageBands: [
      { label: '<65', key: 'PQI11_BCTRL_PNA_AGE_LT_65' },
      { label: '65–74', key: 'PQI11_BCTRL_PNA_AGE_65_74' },
      { label: '75+',  key: 'PQI11_BCTRL_PNA_AGE_GE_75' },
    ],
  },
  {
    label: 'Urinary tract infection',
    help: 'PQI-12 — admissions for UTI per 100,000.',
    ageBands: [
      { label: '<65', key: 'PQI12_UTI_AGE_LT_65' },
      { label: '65–74', key: 'PQI12_UTI_AGE_65_74' },
      { label: '75+',  key: 'PQI12_UTI_AGE_GE_75' },
    ],
  },
  {
    label: 'Asthma (younger adults)',
    help: 'PQI-15 — admissions for asthma in adults aged 18–39 per 100,000.',
    ageBands: [{ label: '<40', key: 'PQI15_ASTHMA_AGE_LT_40' }],
  },
  {
    label: 'Lower-extremity amputation (diabetes)',
    help: 'PQI-16 — admissions for lower-extremity amputation in diabetics per 100,000.',
    ageBands: [
      { label: '<65', key: 'PQI16_LWRXTRMTY_AMPUTN_AGE_LT_65' },
      { label: '65–74', key: 'PQI16_LWRXTRMTY_AMPUTN_AGE_65_74' },
      { label: '75+',  key: 'PQI16_LWRXTRMTY_AMPUTN_AGE_GE_75' },
    ],
  },
];

// ── PLACES category ordering and labels ────────────────────────────
//
// The raw CDC PLACES `category` field drives these groups. We keep the
// order we display them in.

export const PLACES_CATEGORIES_ORDER: string[] = [
  'Health Outcomes',
  'Health Status',
  'Prevention',
  'Health Risk Behaviors',
  'Disability',
  'Health-Related Social Needs',
];

/** Measures where a higher value is BAD (most chronic conditions, risk
 *  behaviors, disabilities, and unmet social needs). Everything not
 *  listed here is treated as "higher is better" (preventive screenings,
 *  mammography, cholesterol screen, dental visit, etc.). */
export const PLACES_LOWER_IS_BETTER_CATEGORIES = new Set([
  'Health Outcomes',
  'Health Status',
  'Health Risk Behaviors',
  'Disability',
  'Health-Related Social Needs',
]);

// ── SDOH fields (from enrich_tier_a.py keys) ────────────────────────

export interface SdohGroup {
  domain: string;
  fields: FieldDef[];
}

export const SDOH_GROUPS: SdohGroup[] = [
  {
    domain: 'Economic Stability',
    fields: [
      { key: 'POVERTY',       label: 'Below 150% Federal Poverty Level', format: 'percent_raw',
        lowerIsBetter: true,
        help: 'Share of county residents living below 150% of the federal poverty threshold.' },
      { key: 'UNEMPLOYMENT',  label: 'Unemployment Rate', format: 'percent_raw',
        lowerIsBetter: true },
    ],
  },
  {
    domain: 'Education & Connectivity',
    fields: [
      { key: 'NO_DIPLOMA',    label: 'No High School Diploma (adults 25+)',
        format: 'percent_raw', lowerIsBetter: true },
      { key: 'NO_BROADBAND',  label: 'No Broadband Internet',
        format: 'percent_raw', lowerIsBetter: true,
        help: 'Share of households without a broadband internet subscription — a telehealth access barrier.' },
    ],
  },
  {
    domain: 'Housing',
    fields: [
      { key: 'HOUSING_BURDEN', label: 'Housing Cost Burden',
        format: 'percent_raw', lowerIsBetter: true,
        help: 'Share of households paying more than 30% of income on housing.' },
      { key: 'CROWDING',       label: 'Crowded Housing Units',
        format: 'percent_raw', lowerIsBetter: true },
      { key: 'SINGLE_PARENT',  label: 'Single-Parent Households',
        format: 'percent_raw' },
    ],
  },
  {
    domain: 'Demographics',
    fields: [
      { key: 'MINORITY',     label: 'Racial / Ethnic Minority Population',
        format: 'percent_raw' },
      { key: 'AGE_65_PLUS',  label: 'Age 65+',
        format: 'percent_raw' },
    ],
  },
];

// ── Formatting helpers ─────────────────────────────────────────────

export function formatValue(
  value: number | null | undefined,
  format: FieldFormat,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  switch (format) {
    case 'dollar':
      return '$' + Math.round(value).toLocaleString();
    case 'dollar_large':
      if (value >= 1e9) return '$' + (value / 1e9).toFixed(2) + 'B';
      if (value >= 1e6) return '$' + (value / 1e6).toFixed(2) + 'M';
      if (value >= 1e3) return '$' + (value / 1e3).toFixed(1) + 'K';
      return '$' + Math.round(value).toLocaleString();
    case 'percent':
      return (value * 100).toFixed(1) + '%';
    case 'percent_raw':
      return value.toFixed(1) + '%';
    case 'decimal1':
      return value.toFixed(1);
    case 'decimal2':
      return value.toFixed(2);
    case 'integer':
      return Math.round(value).toLocaleString();
    case 'rate_per_1k':
      return value.toFixed(1);
    case 'rate_per_100k':
      return Math.round(value).toLocaleString();
  }
}

// ── Percentile helpers ─────────────────────────────────────────────

export function pctlClass(
  percentile: number | undefined,
  lowerIsBetter?: boolean,
): string {
  if (percentile === undefined || percentile === null) return '';
  if (lowerIsBetter) {
    if (percentile <= 25) return 'pctl-inv-low';
    if (percentile >= 75) return 'pctl-inv-high';
    return 'pctl-inv-mid';
  }
  if (percentile <= 25) return 'pctl-low';
  if (percentile >= 75) return 'pctl-high';
  return 'pctl-mid';
}
