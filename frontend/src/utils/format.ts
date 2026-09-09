/**
 * chemistry_score's scale isn't fixed by the API (ChemistryEngine bands it
 * relative to the run's own min/max, see chemistry/engine.py), so this
 * formats whatever comes back readably instead of assuming a 0-100 range:
 * whole numbers print as-is, anything smaller keeps two decimal places.
 */
export function formatChemistryScore(score: number): string {
  return Number.isInteger(score) ? String(score) : score.toFixed(2)
}

// Screenplays name characters and titles in caps, so that is what /analyze
// returns. These helpers are display-only: the raw value stays the join key
// between /analyze, /recommend and the risk/chemistry reports, so it must
// never be rewritten in the model itself.

/** Tokens to leave in caps -- title-casing these would read as a mistake. */
const KEEP_UPPERCASE = new Set(["AI", "TV", "VO", "OS", "FBI", "CIA", "NYPD", "EMT", "DJ", "UN", "CEO"])

/** Words that stay lowercase inside a title unless they open or close it. */
const TITLE_MINOR_WORDS = new Set([
  "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
  "nor", "of", "on", "or", "over", "the", "to", "up", "vs", "with",
])

const ROMAN_NUMERAL = /^[IVXLCDM]+$/

/** True when a value carries no lowercase letters at all, i.e. screenplay caps. */
function isAllCaps(value: string): boolean {
  return /[A-Z]/.test(value) && !/[a-z]/.test(value)
}

function capitalize(segment: string): string {
  if (!segment) return segment
  return segment[0].toUpperCase() + segment.slice(1).toLowerCase()
}

function capitalizeToken(token: string): string {
  const bare = token.replace(/[^A-Za-z]/g, "")
  if (KEEP_UPPERCASE.has(bare) || (bare.length > 1 && ROMAN_NUMERAL.test(bare))) return token

  // Both sides of a hyphen take a capital ("OKONKWO-REYES" -> "Okonkwo-Reyes").
  return token
    .split("-")
    .map((part) =>
      part
        .split("'")
        .map((piece, index, pieces) =>
          // "O'BRIEN" -> "O'Brien", but "MAYA'S" -> "Maya's": only a single
          // leading letter takes a capital after the apostrophe.
          index === 0 || pieces[index - 1].length === 1 ? capitalize(piece) : piece.toLowerCase(),
        )
        .join("'"),
    )
    .join("-")
}

interface WordContext {
  position: number
  total: number
  /** The word before this one, or null at the start. */
  previous: string | null
}

/** Splits on whitespace while keeping the separators, so spacing survives. */
function mapWords(value: string, transform: (token: string, context: WordContext) => string): string {
  const parts = value.split(/(\s+)/)
  // Positions are tracked by index, not by value: a repeated word ("THE MAN
  // AND THE SEA") must not resolve to the first occurrence's position.
  const wordIndices = parts.reduce<number[]>((acc, part, index) => {
    if (part.trim()) acc.push(index)
    return acc
  }, [])
  return parts
    .map((part, index) => {
      if (!part.trim()) return part
      const position = wordIndices.indexOf(index)
      return transform(part, {
        position,
        total: wordIndices.length,
        previous: position > 0 ? parts[wordIndices[position - 1]] : null,
      })
    })
    .join("")
}

/**
 * Renders a screenplay character name readably: "CAPTAIN MAYA OKONKWO-REYES"
 * becomes "Captain Maya Okonkwo-Reyes". A name that already carries mixed case
 * is returned untouched, so nothing the breakdown got right is undone.
 */
export function toDisplayName(value: string): string {
  if (!isAllCaps(value)) return value
  return mapWords(value, (token) => capitalizeToken(token))
}

/**
 * Same, with title conventions: "THE LAST TRANSMISSION" becomes "The Last
 * Transmission", and minor words inside a title stay lowercase.
 */
export function toDisplayTitle(value: string): string {
  if (!isAllCaps(value)) return value
  return mapWords(value, (token, { position, total, previous }) => {
    const bare = token.replace(/[^A-Za-z]/g, "").toLowerCase()
    const isEdge = position === 0 || position === total - 1
    // A word opening a subtitle is capitalised too: "2001: A Space Odyssey".
    const opensClause = previous !== null && /[:;—–]$/.test(previous)
    if (!isEdge && !opensClause && TITLE_MINOR_WORDS.has(bare)) return token.toLowerCase()
    return capitalizeToken(token)
  })
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
