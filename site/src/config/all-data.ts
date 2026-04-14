/**
 * Shared helpers for the per-entity "All Data" section.
 *
 * Each entity page builds its own `AllDataRow[]` from the manifest (because
 * the data shapes differ), but they all share the same row model, CSV
 * serialization, and percentile badge styling.
 */

export interface AllDataRow {
  /** Source grouping (e.g., "General Information", "Value-Based Purchasing"). */
  group: string;
  /** Raw CMS/CDC column name as shipped in the source file. */
  rawKey: string;
  /** Human-readable label. When the raw key is already human-readable, rawKey and label are equal. */
  label: string;
  /** Preformatted display value (e.g., "$1,234", "4.6%", "Not Available"). */
  value: string;
  /** Preformatted national median for context, or "—" if no benchmark exists. */
  bmMedian: string;
  /** Percentile rank (1–100) relative to the national cohort, or undefined. */
  percentile: number | undefined;
}

/** Colour-band CSS class for a percentile badge. */
export function pctlClass(p: number | undefined, inverted = false): string {
  if (p === undefined) return '';
  if (inverted) {
    if (p <= 25) return 'pctl-high';
    if (p >= 75) return 'pctl-low';
    return 'pctl-mid';
  }
  if (p <= 25) return 'pctl-low';
  if (p >= 75) return 'pctl-high';
  return 'pctl-mid';
}

/** CSV-safe cell: escape embedded quotes and wrap in double quotes. */
function csvCell(v: string): string {
  return `"${String(v ?? '').replace(/"/g, '""')}"`;
}

/**
 * Build a data:URI CSV that mirrors the rendered All Data table.
 * Columns: Source, Raw key, Metric, Value, National Median, Percentile.
 */
export function buildAllDataCsv(rows: AllDataRow[]): string {
  const header = ['Source', 'Raw key', 'Metric', 'Value', 'National Median', 'Percentile'];
  const lines = [header.map(csvCell).join(',')];
  for (const r of rows) {
    lines.push([
      csvCell(r.group),
      csvCell(r.rawKey),
      csvCell(r.label),
      csvCell(r.value),
      csvCell(r.bmMedian),
      csvCell(r.percentile === undefined ? '' : `p${r.percentile}`),
    ].join(','));
  }
  return `data:text/csv;charset=utf-8,${encodeURIComponent(lines.join('\n'))}`;
}

/** Treat these scalar sentinel strings as "not reported". */
const NOT_REPORTED_VALUES = new Set(['', '-', '*', 'N/A', 'Not Available', 'Not Applicable']);

/** Format a raw string or number using a heuristic keyed on the field name. */
export function heuristicFormat(value: unknown, key: string): string {
  if (value === null || value === undefined) return '\u2014';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  const s = String(value).trim();
  if (NOT_REPORTED_VALUES.has(s)) return s === '' ? '\u2014' : s;

  const num = Number(s.replace(/[$,%]/g, ''));
  if (!isFinite(num)) return s;

  const k = key;
  if (/_PYMT_AMT|_PYMT_PC|_PYMT_PER_USER|dollar|spending|payment|cost|fine|amount/i.test(k))
    return '$' + Math.round(num).toLocaleString();
  if (/_PCT$|_RATE$|percent|rate$/i.test(k))
    return (Math.abs(num) <= 1 ? num * 100 : num).toFixed(1) + '%';
  if (/_CNT$|count|number/i.test(k) && Number.isFinite(num))
    return Number.isInteger(num) || num > 50
      ? Math.round(num).toLocaleString()
      : num.toFixed(2);
  if (Number.isInteger(num) && Math.abs(num) >= 1000) return num.toLocaleString();
  if (Number.isFinite(num) && !Number.isInteger(num)) return num.toFixed(2);
  return s;
}
