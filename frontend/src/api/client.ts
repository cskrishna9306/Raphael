import type {
  ClusterRecommendation,
  RecommendationReport,
  RecommendStreamEvent,
  Screenplay,
  SwapPreviewRequest,
  SwapPreviewResponse,
  SwapRequest,
} from "./types"

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === "string") return body.detail
    return JSON.stringify(body?.detail ?? body)
  } catch {
    return response.statusText || `Request failed with status ${response.status}`
  }
}

/**
 * Checks the backend's liveness (/health) and readiness (/ready) probes.
 * Used only to drive the status banner -- never blocks or gates the
 * /analyze and /recommend calls themselves.
 */
export async function checkBackendStatus(): Promise<boolean> {
  try {
    const [health, ready] = await Promise.all([fetch(`${API_BASE_URL}/health`), fetch(`${API_BASE_URL}/ready`)])
    return health.ok && ready.ok
  } catch {
    return false
  }
}

/**
 * Runs the screenplay breakdown step: POST /analyze with the raw
 * screenplay document (.txt or .pdf) as multipart form data.
 */
export async function analyzeScreenplay(file: File): Promise<Screenplay> {
  const formData = new FormData()
  formData.append("file", file)

  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  return (await response.json()) as Screenplay
}

/**
 * Runs the casting/chemistry/risk pipeline: POST /recommend with the
 * Screenplay produced by analyzeScreenplay (optionally edited by the user).
 */
export async function recommendCast(screenplay: Screenplay): Promise<RecommendationReport> {
  const response = await fetch(`${API_BASE_URL}/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(screenplay),
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  return (await response.json()) as RecommendationReport
}

/**
 * Recomputes chemistry/risk for one cluster with a single character's
 * candidate substituted in. Deterministic recompute over data /recommend
 * already produced -- no new research, so this is fast.
 */
export async function swapCandidate(request: SwapRequest): Promise<ClusterRecommendation> {
  const response = await fetch(`${API_BASE_URL}/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  return (await response.json()) as ClusterRecommendation
}

/**
 * Scores every other candidate in one character's shortlist as a
 * hypothetical swap, without committing to any of them -- lets the swap
 * picker show each alternative's real chemistry delta and a per-co-star
 * "why" before the user picks. Pure recompute, same as swapCandidate.
 */
export async function previewSwaps(request: SwapPreviewRequest): Promise<SwapPreviewResponse> {
  const response = await fetch(`${API_BASE_URL}/swap/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  return (await response.json()) as SwapPreviewResponse
}

/**
 * Streaming counterpart to recommendCast: POST /recommend/stream, parsing
 * the server-sent-events response by hand (the browser's EventSource API
 * can't send a POST body, so this reads the response body's stream
 * directly). Calls `onProgress` for each character as casting_director
 * finishes searching for them, and resolves to the same RecommendationReport
 * recommendCast would have -- a drop-in replacement plus real progress.
 */
export async function recommendCastStream(
  screenplay: Screenplay,
  onProgress: (event: { character: string; completed: number; total: number }) => void,
): Promise<RecommendationReport> {
  const response = await fetch(`${API_BASE_URL}/recommend/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(screenplay),
  })

  if (!response.ok || !response.body) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let result: RecommendationReport | null = null

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let boundary = buffer.indexOf("\n\n")
    while (boundary !== -1) {
      const rawEvent = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      boundary = buffer.indexOf("\n\n")

      const line = rawEvent.split("\n").find((l) => l.startsWith("data: "))
      if (!line) continue
      const event = JSON.parse(line.slice(6)) as RecommendStreamEvent

      if (event.type === "casting_progress") {
        onProgress({ character: event.character, completed: event.completed, total: event.total })
      } else if (event.type === "recommend_complete") {
        result = event.report
      } else if (event.type === "error") {
        throw new ApiError(response.status, event.message)
      }
    }
  }

  if (!result) throw new ApiError(response.status, "Stream ended before a result was produced.")
  return result
}
