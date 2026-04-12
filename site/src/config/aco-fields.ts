/**
 * ACO MSSP Performance field mapping configuration.
 *
 * Maps raw CMS field names to human-readable labels, groups them into
 * domain sections, and defines formatting/display rules. Used by the
 * ACO [id].astro page to render the structured Table view.
 */

// ── Types ────────────────────────────────────────────────────────────

export type FieldFormat = 'dollar' | 'dollar_agg' | 'percent' | 'decimal3' | 'decimal2' | 'integer' | 'rate' | 'text' | 'boolean' | 'date';

export interface FieldDef {
  key: string;
  label: string;
  format: FieldFormat;
  /** For inverted quality measures where lower = better */
  lowerIsBetter?: boolean;
  /** Short tooltip / help text */
  help?: string;
}

export interface PivotSegment {
  code: string;
  label: string;
}

export interface PivotPeriod {
  code: string;
  label: string;
}

export interface PivotTableDef {
  title: string;
  fieldPrefix: string;
  segments: PivotSegment[];
  periods: PivotPeriod[];
  format: FieldFormat;
  help?: string;
}

export interface Section {
  id: string;
  title: string;
  fields?: FieldDef[];
  pivot?: PivotTableDef;
  /** Custom rendering handled by the template */
  custom?: 'waterfall' | 'demographics' | 'quality_flags' | 'quality_measures';
}

// ── Population segments ──────────────────────────────────────────────

const SEGMENTS: PivotSegment[] = [
  { code: 'ESRD', label: 'End-Stage Renal Disease (ESRD)' },
  { code: 'DIS',  label: 'Disabled' },
  { code: 'AGDU', label: 'Aged, Dual-Eligible' },
  { code: 'AGND', label: 'Aged, Non-Dual' },
];

const BENCHMARK_PERIODS: PivotPeriod[] = [
  { code: 'BY1', label: 'BY1' },
  { code: 'BY2', label: 'BY2' },
  { code: 'BY3', label: 'BY3' },
  { code: 'PY',  label: 'PY' },
];

// ── Section definitions ──────────────────────────────────────────────

export const ACO_SECTIONS: Section[] = [

  // ── 1. Program Structure ───────────────────────────────────────────
  {
    id: 'program-structure',
    title: 'Program Structure',
    fields: [
      { key: 'Current_Track',        label: 'Current Track',        format: 'text' },
      { key: 'Agree_Type',           label: 'Agreement Type',       format: 'text' },
      { key: 'Agreement_Period_Num', label: 'Agreement Period',     format: 'text' },
      { key: 'Current_Start_Date',   label: 'Start Date',           format: 'date' },
      { key: 'Risk_Model',           label: 'Risk Model',           format: 'text',
        help: 'One-Sided: ACO shares savings only. Two-Sided: ACO shares both savings and losses.' },
      { key: 'Assign_Type',          label: 'Assignment Type',      format: 'text',
        help: 'Prospective: beneficiaries assigned at start of year. Retrospective: assigned at year-end based on utilization.' },
      { key: 'SNF_Waiver',           label: 'SNF 3-Day Waiver',     format: 'boolean',
        help: 'Whether the ACO participates in the 3-day SNF waiver, allowing direct SNF admission without a prior hospital stay.' },
    ],
  },

  // ── 2. Financial Performance (Savings Waterfall) ───────────────────
  {
    id: 'financial-performance',
    title: 'Financial Performance',
    custom: 'waterfall',
    // The waterfall steps are defined inline in the template; these fields
    // are listed here for completeness and fallback rendering.
    fields: [
      { key: 'N_AB',                  label: 'Assigned Beneficiaries',           format: 'integer' },
      { key: 'HistBnchmk',            label: 'Historical Benchmark (per capita)', format: 'dollar' },
      { key: 'RegAdj',                label: 'Regional Adjustment',              format: 'dollar' },
      { key: 'PriorSavAdj',           label: 'Prior Savings Adjustment',         format: 'dollar' },
      { key: 'FinalAdjCat',           label: 'Adjustment Category',              format: 'text' },
      { key: 'UpdatedBnchmk',         label: 'Updated Benchmark (per capita)',   format: 'dollar' },
      { key: 'Guardrail',             label: 'Guardrail Applied',                format: 'boolean',
        help: 'Whether CMS applied a guardrail cap to limit benchmark growth.' },
      { key: 'ABtotBnchmk',           label: 'Total Benchmark (all beneficiaries)', format: 'dollar_agg' },
      { key: 'ABtotExp',              label: 'Total Expenditure (all beneficiaries)', format: 'dollar_agg' },
      { key: 'Per_Capita_Exp_TOTAL_PY', label: 'Per Capita Expenditure (PY)',    format: 'dollar' },
      { key: 'GenSaveLoss',           label: 'Generated Savings / Losses',       format: 'dollar_agg' },
      { key: 'Sav_rate',              label: 'Savings Rate',                     format: 'percent' },
      { key: 'MinSavPerc',            label: 'Minimum Savings Rate (threshold)', format: 'percent' },
      { key: 'BnchmkMinExp',          label: 'Benchmark Minus Expenditure',      format: 'dollar_agg' },
      { key: 'DisAdj',                label: 'Disaster Adjustment',              format: 'dollar_agg' },
      { key: 'Impact_Mid_Year_Termination', label: 'Mid-Year Termination Impact', format: 'dollar_agg' },
      { key: 'FinalShareRate',         label: 'Final Shared Savings Rate',       format: 'percent' },
      { key: 'ReducedSS',             label: 'Reduced Shared Savings',           format: 'boolean' },
      { key: 'FinalLossRate',          label: 'Final Shared Loss Rate',          format: 'percent' },
      { key: 'EarnSaveLoss',          label: 'Earned Savings / Losses',          format: 'dollar_agg' },
      { key: 'Rev_Exp_Cat',           label: 'Revenue-to-Expense Category',      format: 'text' },
      { key: 'AIP',                   label: 'Advance Investment Payment',        format: 'boolean' },
      { key: 'AIPBalance',            label: 'AIP Balance',                       format: 'dollar_agg' },
      { key: 'AIPRecoup',             label: 'AIP Recouped',                      format: 'dollar_agg' },
      { key: 'AIPOwe',                label: 'AIP Owed',                          format: 'dollar_agg' },
    ],
  },

  // ── 3. Per Capita Expenditure ──────────────────────────────────────
  {
    id: 'per-capita-expenditure',
    title: 'Per Capita Expenditure by Population Segment',
    pivot: {
      title: 'Per Capita Expenditure ($)',
      fieldPrefix: 'Per_Capita_Exp_ALL_',
      segments: SEGMENTS,
      periods: BENCHMARK_PERIODS,
      format: 'dollar',
      help: 'Annual per-beneficiary expenditure across benchmark years (BY1–BY3) and the performance year (PY). Includes Parts A and B FFS spending.',
    },
  },

  // ── 4. Risk Scores ─────────────────────────────────────────────────
  {
    id: 'risk-scores',
    title: 'Risk Scores',
    pivot: {
      title: 'CMS-HCC Risk Scores',
      fieldPrefix: 'CMS_HCC_RiskScore_',
      segments: SEGMENTS,
      periods: BENCHMARK_PERIODS,
      format: 'decimal3',
      help: 'Hierarchical Condition Category risk scores. A score of 1.0 = national average. Below 1.0 means the population is healthier than average.',
    },
    // Additional pivot tables and fields handled via custom rendering:
    // - Demographic Risk Scores (PY, BY3)
    // - Risk Redistribution Weights (PY only)
  },

  // ── 5. Beneficiary Demographics ────────────────────────────────────
  {
    id: 'demographics',
    title: 'Beneficiary Demographics',
    custom: 'demographics',
    fields: [
      // Enrollment by population category
      { key: 'N_AB_Year_PY',              label: 'Total Person-Years (PY)',        format: 'integer' },
      { key: 'N_AB_Year_ESRD_BY3',        label: 'ESRD (BY3)',                     format: 'integer' },
      { key: 'N_AB_Year_DIS_BY3',         label: 'Disabled (BY3)',                 format: 'integer' },
      { key: 'N_AB_Year_AGED_Dual_BY3',   label: 'Aged Dual (BY3)',               format: 'integer' },
      { key: 'N_AB_Year_AGED_NonDual_BY3', label: 'Aged Non-Dual (BY3)',          format: 'integer' },
      { key: 'N_AB_Year_ESRD_PY',         label: 'ESRD (PY)',                     format: 'integer' },
      { key: 'N_AB_Year_DIS_PY',          label: 'Disabled (PY)',                 format: 'integer' },
      { key: 'N_AB_Year_AGED_Dual_PY',    label: 'Aged Dual (PY)',               format: 'integer' },
      { key: 'N_AB_Year_AGED_NonDual_PY', label: 'Aged Non-Dual (PY)',           format: 'integer' },
      { key: 'N_AB_Year_Dual_PY',         label: 'Dual-Eligible (PY)',            format: 'integer' },
      { key: 'N_AB_Year_NonDual_PY',      label: 'Non-Dual (PY)',                format: 'integer' },
      // VA/CBA enrollment
      { key: 'N_Ben_VA_Only',             label: 'VA Only',                       format: 'integer' },
      { key: 'N_Ben_CBA_Only',            label: 'CBA Only',                      format: 'integer' },
      { key: 'N_Ben_CBA_and_VA',          label: 'CBA and VA',                    format: 'integer' },
      // Age distribution
      { key: 'N_Ben_Age_0_64',            label: 'Age 0–64',                      format: 'integer' },
      { key: 'N_Ben_Age_65_74',           label: 'Age 65–74',                     format: 'integer' },
      { key: 'N_Ben_Age_75_84',           label: 'Age 75–84',                     format: 'integer' },
      { key: 'N_Ben_Age_85plus',          label: 'Age 85+',                       format: 'integer' },
      // Gender
      { key: 'N_Ben_Female',              label: 'Female',                        format: 'integer' },
      { key: 'N_Ben_Male',                label: 'Male',                          format: 'integer' },
      // Race/ethnicity
      { key: 'N_Ben_Race_White',          label: 'White',                         format: 'integer' },
      { key: 'N_Ben_Race_Black',          label: 'Black',                         format: 'integer' },
      { key: 'N_Ben_Race_Asian',          label: 'Asian',                         format: 'integer' },
      { key: 'N_Ben_Race_Hisp',           label: 'Hispanic',                      format: 'integer' },
      { key: 'N_Ben_Race_Native',         label: 'Native American/Alaska Native', format: 'integer' },
      { key: 'N_Ben_Race_Other',          label: 'Other',                         format: 'integer' },
      { key: 'N_Ben_Race_Unknown',        label: 'Unknown',                       format: 'integer' },
      // Special populations
      { key: 'Perc_Dual',                 label: 'Dual-Eligible (%)',             format: 'percent' },
      { key: 'Perc_LTI',                  label: 'Long-Term Institutionalized (%)', format: 'percent' },
    ],
  },

  // ── 6. Utilization — Spending by Service ───────────────────────────
  {
    id: 'spending-by-service',
    title: 'Per Capita Spending by Service Category',
    fields: [
      { key: 'CapAnn_INP_All',    label: 'Inpatient — All',                format: 'dollar' },
      { key: 'CapAnn_INP_S_trm',  label: 'Inpatient — Short-Term Acute',  format: 'dollar' },
      { key: 'CapAnn_INP_L_trm',  label: 'Inpatient — Long-Term',         format: 'dollar' },
      { key: 'CapAnn_INP_Rehab',  label: 'Inpatient — Rehab',             format: 'dollar' },
      { key: 'CapAnn_INP_Psych',  label: 'Inpatient — Psychiatric',       format: 'dollar' },
      { key: 'CapAnn_HSP',        label: 'Hospice',                        format: 'dollar' },
      { key: 'CapAnn_SNF',        label: 'Skilled Nursing Facility',       format: 'dollar' },
      { key: 'CapAnn_OPD',        label: 'Outpatient',                     format: 'dollar' },
      { key: 'CapAnn_PB',         label: 'Physician / Supplier (Part B)',  format: 'dollar' },
      { key: 'CapAnn_AmbPay',     label: 'Ambulance',                      format: 'dollar' },
      { key: 'CapAnn_HHA',        label: 'Home Health',                    format: 'dollar' },
      { key: 'CapAnn_DME',        label: 'Durable Medical Equipment',      format: 'dollar' },
    ],
  },

  // ── 7. Utilization — Admissions & Visits ───────────────────────────
  {
    id: 'admissions-visits',
    title: 'Utilization — Admissions & Visits',
    fields: [
      // Admissions per 1,000
      { key: 'ADM',             label: 'Hospital Admissions (per 1,000)',            format: 'rate' },
      { key: 'ADM_S_Trm',      label: 'Short-Term Acute Admissions (per 1,000)',    format: 'rate' },
      { key: 'ADM_L_Trm',      label: 'Long-Term Admissions (per 1,000)',           format: 'rate' },
      { key: 'ADM_Rehab',      label: 'Rehab Admissions (per 1,000)',               format: 'rate' },
      { key: 'ADM_Psych',      label: 'Psychiatric Admissions (per 1,000)',          format: 'rate' },
      // Visits per 1,000
      { key: 'P_EDV_Vis',      label: 'ED Visits (per 1,000)',                      format: 'rate' },
      { key: 'P_EDV_Vis_HOSP', label: 'ED Visits Resulting in Hospitalization (per 1,000)', format: 'rate' },
      { key: 'P_CT_VIS',       label: 'CT Scans (per 1,000)',                       format: 'rate' },
      { key: 'P_MRI_VIS',      label: 'MRI Scans (per 1,000)',                      format: 'rate' },
      { key: 'P_EM_Total',     label: 'E&M Visits — Total (per 1,000)',             format: 'rate' },
      { key: 'P_EM_PCP_Vis',   label: 'E&M Visits — Primary Care (per 1,000)',      format: 'rate' },
      { key: 'P_EM_SP_Vis',    label: 'E&M Visits — Specialist (per 1,000)',        format: 'rate' },
      { key: 'P_Nurse_Vis',    label: 'Nurse Practitioner Visits (per 1,000)',       format: 'rate' },
      { key: 'P_FQHC_RHC_Vis', label: 'FQHC / RHC Visits (per 1,000)',             format: 'rate' },
      { key: 'P_SNF_ADM',      label: 'SNF Admissions (per 1,000)',                 format: 'rate' },
      { key: 'SNF_LOS',        label: 'SNF Average Length of Stay (days)',           format: 'integer' },
      { key: 'SNF_PayperStay', label: 'SNF Average Payment per Stay',               format: 'dollar' },
    ],
  },

  // ── 8. Provider Composition ────────────────────────────────────────
  {
    id: 'provider-composition',
    title: 'Provider Composition',
    fields: [
      { key: 'N_Hosp',       label: 'Hospitals',                      format: 'integer' },
      { key: 'N_CAH',        label: 'Critical Access Hospitals',      format: 'integer' },
      { key: 'N_FQHC',       label: 'FQHCs',                          format: 'integer' },
      { key: 'N_RHC',        label: 'Rural Health Clinics',           format: 'integer' },
      { key: 'N_ETA',        label: 'Extension of Treatment Areas',   format: 'integer' },
      { key: 'N_Fac_Other',  label: 'Other Facilities',               format: 'integer' },
      { key: 'N_PCP',        label: 'Primary Care Physicians',        format: 'integer' },
      { key: 'N_Spec',       label: 'Specialists',                    format: 'integer' },
      { key: 'N_NP',         label: 'Nurse Practitioners',            format: 'integer' },
      { key: 'N_PA',         label: 'Physician Assistants',           format: 'integer' },
      { key: 'N_CNS',        label: 'Clinical Nurse Specialists',     format: 'integer' },
    ],
  },

  // ── 9. CAHPS Patient Experience ────────────────────────────────────
  {
    id: 'cahps',
    title: 'CAHPS Patient Experience',
    fields: [
      { key: 'CAHPS_1',  label: 'Getting Timely Care, Appointments & Information', format: 'decimal2' },
      { key: 'CAHPS_2',  label: 'How Well Providers Communicate',                   format: 'decimal2' },
      { key: 'CAHPS_3',  label: 'Patient\'s Rating of Provider',                    format: 'decimal2' },
      { key: 'CAHPS_4',  label: 'Access to Specialists',                            format: 'decimal2' },
      { key: 'CAHPS_5',  label: 'Health Promotion & Education',                     format: 'decimal2' },
      { key: 'CAHPS_6',  label: 'Shared Decision-Making',                           format: 'decimal2' },
      { key: 'CAHPS_7',  label: 'Health Status / Functional Status',                format: 'decimal2' },
      { key: 'CAHPS_8',  label: 'Courteous & Helpful Office Staff',                 format: 'decimal2' },
      { key: 'CAHPS_9',  label: 'Care Coordination',                                format: 'decimal2' },
      { key: 'CAHPS_11', label: 'Stewardship of Patient Resources',                 format: 'decimal2' },
    ],
  },

  // ── 10. Clinical Quality Measures ──────────────────────────────────
  {
    id: 'quality-measures',
    title: 'Clinical Quality Measures',
    custom: 'quality_measures',
    fields: [
      { key: 'QualScore',      label: 'Overall Quality Score (Composite)',       format: 'decimal2' },
      { key: 'Measure_479',    label: 'All-Cause Unplanned Admissions (risk-adjusted rate)', format: 'decimal2',
        lowerIsBetter: true,
        help: 'Risk-standardized rate of unplanned admissions per 100 person-years. Lower indicates better care coordination.' },
      { key: 'Measure_484',    label: 'Risk-Standardized All-Condition Readmission Rate', format: 'decimal2',
        lowerIsBetter: true,
        help: 'Risk-standardized rate of unplanned readmissions within 30 days. Lower indicates better discharge planning.' },
      { key: 'QualityID_318',  label: 'Falls: Screening for Future Fall Risk',              format: 'decimal2' },
      { key: 'QualityID_110',  label: 'Influenza Immunization',                             format: 'decimal2' },
      { key: 'QualityID_226',  label: 'Tobacco Use: Screening & Cessation Intervention',    format: 'decimal2' },
      { key: 'QualityID_113',  label: 'Colorectal Cancer Screening',                        format: 'decimal2' },
      { key: 'QualityID_112',  label: 'Breast Cancer Screening',                            format: 'decimal2' },
      { key: 'QualityID_438',  label: 'Statin Therapy for Cardiovascular Disease Prevention', format: 'decimal2' },
      { key: 'QualityID_370',  label: 'Depression Remission at 12 Months',                  format: 'decimal2' },
      // Multi-pathway measures — primary value, then reporting variants
      { key: 'QualityID_134_WI',           label: 'Depression Screening (Web Interface)',           format: 'decimal2' },
      { key: 'QualityID_134_eCQM',         label: 'Depression Screening (eCQM)',                    format: 'decimal2' },
      { key: 'QualityID_134_MIPSCQM',      label: 'Depression Screening (MIPS CQM)',               format: 'decimal2' },
      { key: 'QualityID_134_MedicareCQM',  label: 'Depression Screening (Medicare CQM)',            format: 'decimal2' },
      { key: 'QualityID_001_WI',           label: 'Diabetes: HbA1c Poor Control >9% (Web Interface)', format: 'decimal2',
        lowerIsBetter: true,
        help: 'Percentage of diabetic patients with HbA1c >9% (poor control). Lower is better — indicates fewer patients with uncontrolled diabetes.' },
      { key: 'QualityID_001_eCQM',         label: 'Diabetes: HbA1c Poor Control >9% (eCQM)',       format: 'decimal2', lowerIsBetter: true },
      { key: 'QualityID_001_MIPSCQM',      label: 'Diabetes: HbA1c Poor Control >9% (MIPS CQM)',  format: 'decimal2', lowerIsBetter: true },
      { key: 'QualityID_001_MedicareCQM',  label: 'Diabetes: HbA1c Poor Control >9% (Medicare CQM)', format: 'decimal2', lowerIsBetter: true },
      { key: 'QualityID_236_WI',           label: 'Controlling High Blood Pressure (Web Interface)', format: 'decimal2' },
      { key: 'QualityID_236_eCQM',         label: 'Controlling High Blood Pressure (eCQM)',         format: 'decimal2' },
      { key: 'QualityID_236_MIPSCQM',      label: 'Controlling High Blood Pressure (MIPS CQM)',    format: 'decimal2' },
      { key: 'QualityID_236_MedicareCQM',  label: 'Controlling High Blood Pressure (Medicare CQM)', format: 'decimal2' },
    ],
  },
];

// ── Quality Reporting Flags ──────────────────────────────────────────

export interface QualityFlag {
  key: string;
  label: string;
}

export const QUALITY_FLAGS: QualityFlag[] = [
  { key: 'Met_QPS',                                label: 'Met Quality Performance Standard (QPS)' },
  { key: 'Met_AltQPS',                             label: 'Met Alternative QPS' },
  { key: 'Met_40pctl',                             label: 'Met 40th Percentile Threshold' },
  { key: 'Met_SSP_quality_reporting_requirements', label: 'Met SSP Quality Reporting Requirements' },
  { key: 'Report_WI',                              label: 'Reported via Web Interface' },
  { key: 'Report_eCQM_CQM_MedicareCQM',           label: 'Reported via eCQM / CQM / Medicare CQM' },
  { key: 'Met_FirstYear',                          label: 'First-Year ACO Quality Pass' },
  { key: 'Met_Incentive',                          label: 'Met Incentive Threshold' },
  { key: 'Recvd40p',                               label: 'Received 40th Percentile Bonus' },
  { key: 'DisAffQual',                             label: 'Disaster / Affected Quality Waiver Applied' },
];

// ── Demographic Risk Scores pivot (PY vs BY3 only) ──────────────────

export const DEMOG_RISK_PIVOT: PivotTableDef = {
  title: 'Demographic Risk Scores',
  fieldPrefix: 'Demog_RiskScore_',
  segments: SEGMENTS,
  periods: [
    { code: 'BY3', label: 'BY3' },
    { code: 'PY',  label: 'PY' },
  ],
  format: 'decimal3',
  help: 'Demographic-only risk scores (age/sex/Medicaid status). Compared with HCC risk scores, the difference reflects clinical coding intensity.',
};

// ── Risk Redistribution Weights (PY only) ────────────────────────────

export const RISK_WEIGHTS: FieldDef[] = [
  { key: 'RR_weight_ESRD_PY', label: 'ESRD Weight',           format: 'percent' },
  { key: 'RR_weight_DIS_PY',  label: 'Disabled Weight',       format: 'percent' },
  { key: 'RR_weight_AGDU_PY', label: 'Aged Dual Weight',      format: 'percent' },
  { key: 'RR_weight_AGND_PY', label: 'Aged Non-Dual Weight',  format: 'percent' },
];

// ── Multi-pathway quality measure groupings ──────────────────────────

export interface MultiPathwayMeasure {
  measureId: string;
  label: string;
  lowerIsBetter?: boolean;
  pathways: { suffix: string; label: string }[];
}

export const MULTI_PATHWAY_MEASURES: MultiPathwayMeasure[] = [
  {
    measureId: '134',
    label: 'Depression Screening & Follow-Up Plan',
    pathways: [
      { suffix: 'WI',           label: 'Web Interface' },
      { suffix: 'eCQM',         label: 'eCQM' },
      { suffix: 'MIPSCQM',     label: 'MIPS CQM' },
      { suffix: 'MedicareCQM', label: 'Medicare CQM' },
    ],
  },
  {
    measureId: '001',
    label: 'Diabetes: HbA1c Poor Control (>9%)',
    lowerIsBetter: true,
    pathways: [
      { suffix: 'WI',           label: 'Web Interface' },
      { suffix: 'eCQM',         label: 'eCQM' },
      { suffix: 'MIPSCQM',     label: 'MIPS CQM' },
      { suffix: 'MedicareCQM', label: 'Medicare CQM' },
    ],
  },
  {
    measureId: '236',
    label: 'Controlling High Blood Pressure',
    pathways: [
      { suffix: 'WI',           label: 'Web Interface' },
      { suffix: 'eCQM',         label: 'eCQM' },
      { suffix: 'MIPSCQM',     label: 'MIPS CQM' },
      { suffix: 'MedicareCQM', label: 'Medicare CQM' },
    ],
  },
];

// ── Helpers ──────────────────────────────────────────────────────────

/** Set of all field keys covered by the structured sections */
export function getCoveredKeys(): Set<string> {
  const keys = new Set<string>();

  // Identity fields (rendered in page header, not in sections)
  keys.add('ACO_ID');
  keys.add('ACO_Name');

  for (const section of ACO_SECTIONS) {
    if (section.fields) {
      for (const f of section.fields) keys.add(f.key);
    }
    if (section.pivot) {
      const { fieldPrefix, segments, periods } = section.pivot;
      for (const seg of segments) {
        for (const per of periods) {
          keys.add(`${fieldPrefix}${seg.code}_${per.code}`);
        }
      }
    }
  }

  // Demographic risk scores
  for (const seg of DEMOG_RISK_PIVOT.segments) {
    for (const per of DEMOG_RISK_PIVOT.periods) {
      keys.add(`${DEMOG_RISK_PIVOT.fieldPrefix}${seg.code}_${per.code}`);
    }
  }

  // Risk weights
  for (const w of RISK_WEIGHTS) keys.add(w.key);

  // Quality flags
  for (const f of QUALITY_FLAGS) keys.add(f.key);

  // Total PY expenditure (shown in waterfall)
  keys.add('Per_Capita_Exp_TOTAL_PY');

  return keys;
}
