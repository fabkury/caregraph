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

/** Format a raw string or number using a heuristic keyed on the field name.
 *
 * `label` is an optional suffix hint: when a metric's display label ends
 * in "($)" or "(%)", we trust that over the key-name heuristic. This
 * prevents fields like `cost_to_charge_ratio` (a unitless ratio, label
 * "Cost-to-Charge Ratio") from being misformatted as currency just
 * because the key contains the substring "cost".
 */
export function heuristicFormat(value: unknown, key: string, label?: string): string {
  if (value === null || value === undefined) return '\u2014';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  const s = String(value).trim();
  if (NOT_REPORTED_VALUES.has(s)) return s === '' ? '\u2014' : s;

  const num = Number(s.replace(/[$,%]/g, ''));
  if (!isFinite(num)) return s;

  const k = key;
  const labelStr = label || '';

  // Label-driven formatting takes priority — it reflects ETL intent.
  if (/\(\$\)\s*$/.test(labelStr)) return '$' + Math.round(num).toLocaleString();
  if (/\(%\)\s*$/.test(labelStr)) return num.toFixed(1) + '%';
  if (/\bratio\b/i.test(labelStr) || /_ratio$/i.test(k) || /\bratio\b/i.test(k)) {
    return Number.isInteger(num) ? String(num) : num.toFixed(2);
  }

  if (/_PYMT_AMT|_PYMT_PC|_PYMT_PER_USER|dollar|spending|\bpayment\b|\bcosts?\b|\bfine\b|\bamount\b|\brevenue\b|\bincome\b|\bassets\b|\bliabilities\b|\bbalance\b/i.test(k))
    return '$' + Math.round(num).toLocaleString();
  if (/_PCT$|_RATE$|percent|rate$|_share$|\bshare$/i.test(k))
    return (Math.abs(num) <= 1 ? num * 100 : num).toFixed(1) + '%';
  if (/_CNT$|count|number/i.test(k) && Number.isFinite(num))
    return Number.isInteger(num) || num > 50
      ? Math.round(num).toLocaleString()
      : num.toFixed(2);
  if (Number.isInteger(num) && Math.abs(num) >= 1000) return num.toLocaleString();
  if (Number.isFinite(num) && !Number.isInteger(num)) return num.toFixed(2);
  return s;
}

/**
 * Generic flattener for a `manifest.data.<dsKey>` subtree. Handles four
 * shapes so pages don't corrupt the CSV export when new enrichments land:
 *
 *   1. scalar                       → emit one row
 *   2. `{value, label, ...}`        → one row, using .label as label
 *   3. deeper nested object         → recurse, prefixing the path
 *   4. array of objects             → one row per (item, field), keyed by
 *      the item's primary identifier (tag / Measure ID / etc.) so users
 *      can tell which record a value belongs to after sorting.
 */
function isLabeledMetric(v: any): v is { value: any; label?: string } {
  return v && typeof v === 'object' && !Array.isArray(v) && 'value' in v;
}

function rowIdentifier(obj: Record<string, any>, fallbackIdx: number): string {
  const preferred = ['Measure ID', 'measure_id', 'Measure Name', 'tag', 'id', 'code'];
  for (const k of preferred) {
    const v = obj[k];
    if (v !== undefined && v !== null && String(v).trim() !== '') return String(v).trim();
  }
  return `#${fallbackIdx + 1}`;
}

export function flattenDataset(
  groupLabel: string,
  node: unknown,
  rows: AllDataRow[],
): void {
  walk('', '', node);

  function walk(pathKey: string, pathLabel: string, n: any): void {
    if (n === null || n === undefined || n === '') return;

    if (Array.isArray(n)) {
      for (let i = 0; i < n.length; i++) {
        const item = n[i];
        if (!item || typeof item !== 'object' || Array.isArray(item)) {
          walk(`${pathKey}[${i}]`, `${pathLabel} [${i + 1}]`.trim(), item);
          continue;
        }
        const id = rowIdentifier(item as Record<string, any>, i);
        for (const [k, v] of Object.entries(item as Record<string, any>)) {
          if (v === null || v === undefined || v === '') continue;
          const nextKey = pathKey ? `${pathKey}[${id}].${k}` : `${id}.${k}`;
          const nextLabel = pathLabel ? `${pathLabel} [${id}] — ${k}` : `${id} — ${k}`;
          walk(nextKey, nextLabel, v);
        }
      }
      return;
    }

    if (typeof n === 'object') {
      if (isLabeledMetric(n)) {
        if (n.value === null || n.value === undefined || n.value === '') return;
        const label = n.label && String(n.label).trim() !== '' ? String(n.label) : pathLabel;
        pushRow(pathKey, label, n.value, label);
        return;
      }
      for (const [k, v] of Object.entries(n as Record<string, any>)) {
        walk(
          pathKey ? `${pathKey}.${k}` : k,
          pathLabel ? `${pathLabel} — ${k}` : k,
          v,
        );
      }
      return;
    }

    pushRow(pathKey, pathLabel, n, undefined);
  }

  function pushRow(pathKey: string, pathLabel: string, value: unknown, formatLabel: string | undefined) {
    const leafKey = pathKey.split('.').pop() || pathKey;
    rows.push({
      group: groupLabel,
      rawKey: pathKey,
      label: pathLabel,
      value: heuristicFormat(value, leafKey, formatLabel),
      bmMedian: '\u2014',
      percentile: undefined,
    });
  }
}
