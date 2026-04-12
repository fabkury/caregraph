/**
 * CareGraph Workspace — localStorage utilities.
 *
 * Shared by the Workspace page and the Pin buttons on entity pages.
 */

const PINS_KEY = 'caregraph-workspace-pins';

export interface Pin {
  type: string;
  id: string;
  name: string;
}

interface WorkspaceExport {
  version: 1;
  exported: string;
  pins: Pin[];
  notes: Record<string, string>;
}

/** Get all pinned entities. */
export function getPins(): Pin[] {
  try {
    const raw = localStorage.getItem(PINS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/** Save the full pins array. */
function savePins(pins: Pin[]): void {
  localStorage.setItem(PINS_KEY, JSON.stringify(pins));
}

/** Add a pin. No-op if already pinned. */
export function addPin(type: string, id: string, name: string): void {
  const pins = getPins();
  if (pins.some(p => p.type === type && p.id === id)) return;
  pins.push({ type, id, name });
  savePins(pins);
}

/** Remove a pin. */
export function removePin(type: string, id: string): void {
  const pins = getPins().filter(p => !(p.type === type && p.id === id));
  savePins(pins);
}

/** Check if an entity is pinned. */
export function isPinned(type: string, id: string): boolean {
  return getPins().some(p => p.type === type && p.id === id);
}

/** Note key helper. */
function noteKey(type: string, id: string): string {
  return `caregraph-workspace-notes-${type}-${id}`;
}

/** Get a note for a pinned entity. */
export function getNote(type: string, id: string): string {
  return localStorage.getItem(noteKey(type, id)) || '';
}

/** Set a note for a pinned entity. */
export function setNote(type: string, id: string, text: string): void {
  if (text) {
    localStorage.setItem(noteKey(type, id), text);
  } else {
    localStorage.removeItem(noteKey(type, id));
  }
}

/** Export workspace as a JSON string. */
export function exportWorkspace(): string {
  const pins = getPins();
  const notes: Record<string, string> = {};
  for (const pin of pins) {
    const n = getNote(pin.type, pin.id);
    if (n) {
      notes[`${pin.type}-${pin.id}`] = n;
    }
  }
  const data: WorkspaceExport = {
    version: 1,
    exported: new Date().toISOString(),
    pins,
    notes,
  };
  return JSON.stringify(data, null, 2);
}

/** Import workspace from a JSON string. Merges with existing pins. */
export function importWorkspace(jsonStr: string): void {
  const data: WorkspaceExport = JSON.parse(jsonStr);
  if (!data.pins || !Array.isArray(data.pins)) {
    throw new Error('Invalid workspace file: missing pins array');
  }

  // Merge pins (avoid duplicates)
  for (const pin of data.pins) {
    addPin(pin.type, pin.id, pin.name);
  }

  // Merge notes
  if (data.notes && typeof data.notes === 'object') {
    for (const [key, text] of Object.entries(data.notes)) {
      const parts = key.split('-');
      if (parts.length >= 2) {
        const type = parts[0];
        const id = parts.slice(1).join('-');
        // Only overwrite if the imported note is non-empty
        if (text) {
          setNote(type, id, text);
        }
      }
    }
  }
}
