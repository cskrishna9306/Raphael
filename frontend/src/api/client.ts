import { auth } from "../firebase"
import type {
  ClusterRecommendation,
  Project,
  ProjectSummary,
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
 * Builds the Authorization header for the signed-in user, if any. Signing in
 * is optional -- an anonymous caller gets an empty header and the backend
 * treats the request as anonymous rather than rejecting it (see
 * optional_claims). getIdToken hands back the cached ID token and refreshes
 * it automatically once it is close to expiring, so callers never have to
 * think about token lifetimes.
 */
async function authHeader(): Promise<Record<string, string>> {
  // auth is null when Firebase isn't configured for this deployment -- sign-in is
  // optional, so that's just another way to end up with no signed-in user.
  const user = auth?.currentUser
  if (!user) {
    return {}
  }
  return { Authorization: `Bearer ${await user.getIdToken()}` }
}

/**
 * Runs one authenticated request, raising ApiError on a non-2xx response.
 * Every endpoint below /health and /ready goes through here so the auth
 * header and error shape stay in one place.
 */
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...(await authHeader()), ...init.headers },
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  // DELETE /projects/{id} answers 204 with no body to parse.
  if (response.status === 204) return undefined as T

  return (await response.json()) as T
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

  return request<Screenplay>("/analyze", { method: "POST", body: formData })
}

/**
 * Runs the casting/chemistry/risk pipeline: POST /recommend with the
 * Screenplay produced by analyzeScreenplay (optionally edited by the user).
 * Passing `projectId` also saves the report to that project's history.
 */
export async function recommendCast(screenplay: Screenplay, projectId?: string): Promise<RecommendationReport> {
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""

  return request<RecommendationReport>(`/recommend${query}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(screenplay),
  })
}

/**
 * Saves a Screenplay as a new project, so the run shows up in history even
 * if the user never gets as far as running the casting analysis.
 */
export async function createProject(screenplay: Screenplay): Promise<Project> {
  return request<Project>("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(screenplay),
  })
}

/**
 * Lists the signed-in user's saved projects, most recently touched first.
 */
export async function listProjects(): Promise<ProjectSummary[]> {
  return request<ProjectSummary[]>("/projects")
}

/**
 * Reads one saved project, including its latest report if it has one.
 */
export async function getProject(projectId: string): Promise<Project> {
  return request<Project>(`/projects/${encodeURIComponent(projectId)}`)
}

/**
 * Permanently deletes one saved project and every report under it.
 */
export async function deleteProject(projectId: string): Promise<void> {
  return request<void>(`/projects/${encodeURIComponent(projectId)}`, { method: "DELETE" })
}

/**
 * Recomputes chemistry/risk for one cluster with a single character's
 * candidate substituted in. Deterministic recompute over data /recommend
 * already produced -- no new research, so this is fast.
 */
export async function swapCandidate(request: SwapRequest): Promise<ClusterRecommendation> {
  const response = await fetch(`${API_BASE_URL}/swap`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
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
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
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
  projectId?: string,
): Promise<RecommendationReport> {
  // Carries project_id for the same reason recommendCast does -- otherwise
  // switching to the streaming path silently stops saving runs to history.
  const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""

  const response = await fetch(`${API_BASE_URL}/recommend/stream${query}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
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
