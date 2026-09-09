import { auth } from "../firebase"
import type { RecommendationReport, Screenplay } from "./types"

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
    headers: await authHeader(),
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
    headers: { "Content-Type": "application/json", ...(await authHeader()) },
    body: JSON.stringify(screenplay),
  })

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  return (await response.json()) as RecommendationReport
}
