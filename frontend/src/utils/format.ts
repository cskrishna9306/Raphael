/**
 * chemistry_score's scale isn't fixed by the API (ChemistryEngine bands it
 * relative to the run's own min/max, see chemistry/engine.py), so this
 * formats whatever comes back readably instead of assuming a 0-100 range:
 * whole numbers print as-is, anything smaller keeps two decimal places.
 */
export function formatChemistryScore(score: number): string {
  return Number.isInteger(score) ? String(score) : score.toFixed(2)
}
