/**
 * chemistry_score's scale isn't fixed by the API (ChemistryEngine bands it
 * relative to the run's own min/max, see chemistry/engine.py), so this
 * formats whatever comes back readably instead of assuming a 0-100 range:
 * whole numbers print as-is, anything smaller keeps two decimal places.
 */
export function formatChemistryScore(score: number): string {
  return Number.isInteger(score) ? String(score) : score.toFixed(2)
}

const RELATIVE_UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 365 * 24 * 60 * 60 * 1000],
  ["month", 30 * 24 * 60 * 60 * 1000],
  ["week", 7 * 24 * 60 * 60 * 1000],
  ["day", 24 * 60 * 60 * 1000],
  ["hour", 60 * 60 * 1000],
  ["minute", 60 * 1000],
]

const relativeTime = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" })

/**
 * Formats an API timestamp as a short relative label ("3 days ago") for the
 * history list. Returns null for a missing or unparseable value -- the
 * timestamps are optional on the API side, so callers omit the line rather
 * than print a placeholder.
 */
export function formatRelativeTime(timestamp?: string | null): string | null {
  if (!timestamp) return null

  const parsed = Date.parse(timestamp)
  if (Number.isNaN(parsed)) return null

  const elapsed = parsed - Date.now()
  for (const [unit, size] of RELATIVE_UNITS) {
    if (Math.abs(elapsed) >= size) return relativeTime.format(Math.round(elapsed / size), unit)
  }

  return "just now"
}
