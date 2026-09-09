import { auth } from "../firebase"
import type { Project, ProjectSummary, RecommendationReport, Screenplay } from "./types"

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
 * Builds the Authorization header the protected endpoints require. getIdToken
 * hands back the cached ID token and refreshes it automatically once it is
 * close to expiring, so callers never have to think about token lifetimes.
 */
async function authHeader(): Promise<Record<string, string>> {
  const user = auth.currentUser
  if (!user) {
    throw new ApiError(401, "Your session has ended. Sign in again to continue.")
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
