import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"
import { ApiError, deleteProject, listProjects } from "../api/client"
import type { ProjectSummary } from "../api/types"
import { useAuth } from "./AuthContext"

interface HistoryState {
  projects: ProjectSummary[]
  /** True only for the first load of an account; a refresh leaves the existing list on screen. */
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  remove: (projectId: string) => Promise<void>
}

/** What has actually been fetched, tagged with the account it was fetched for. */
interface LoadedHistory {
  uid: string
  projects: ProjectSummary[]
  error: string | null
}

const HistoryContext = createContext<HistoryState | null>(null)

// Hoisted so the signed-out/loading case hands back a stable identity rather
// than a fresh literal that re-renders every consumer each render.
const NO_PROJECTS: ProjectSummary[] = []

function describeError(caught: unknown): string {
  return caught instanceof ApiError ? caught.message : "Could not load your history."
}

/**
 * Owns the signed-in user's saved-project list. Shared through context rather
 * than fetched per component because the ingest flow has to refresh it after
 * creating a project or saving a report, and the sidebar has to re-render.
 */
export function HistoryProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [loaded, setLoaded] = useState<LoadedHistory | null>(null)

  // Tagging the fetch with its uid lets `loading` and the empty list be
  // derived during render instead of tracked as their own state. Switching
  // accounts then can't leave the previous user's projects on screen even for
  // one frame -- the tag stops matching the moment the account changes.
  const isCurrent = user !== null && loaded !== null && loaded.uid === user.uid
  const projects = isCurrent ? loaded.projects : NO_PROJECTS
  const error = isCurrent ? loaded.error : null
  const loading = user !== null && !isCurrent

  useEffect(() => {
    if (!user) return

    const { uid } = user
    let cancelled = false

    void listProjects()
      .then((fetched) => {
        if (!cancelled) setLoaded({ uid, projects: fetched, error: null })
      })
      .catch((caught) => {
        if (!cancelled) setLoaded({ uid, projects: [], error: describeError(caught) })
      })

    return () => {
      cancelled = true
    }
  }, [user])

  const refresh = useCallback(async () => {
    if (!user) return

    const { uid } = user
    try {
      setLoaded({ uid, projects: await listProjects(), error: null })
    } catch (caught) {
      // Keep whatever is already listed -- a failed refresh shouldn't blank
      // out a list the user can still meaningfully click.
      setLoaded((current) =>
        current !== null && current.uid === uid ? { ...current, error: describeError(caught) } : current,
      )
    }
  }, [user])

  const remove = useCallback(async (projectId: string) => {
    await deleteProject(projectId)
    // Drop it locally rather than refetching -- the delete already told us it
    // is gone, and this keeps the row from flickering back in.
    setLoaded((current) =>
      current === null
        ? current
        : { ...current, projects: current.projects.filter((project) => project.id !== projectId) },
    )
  }, [])

  const value = useMemo<HistoryState>(
    () => ({ projects, loading, error, refresh, remove }),
    [projects, loading, error, refresh, remove],
  )

  return <HistoryContext.Provider value={value}>{children}</HistoryContext.Provider>
}

export function useHistory(): HistoryState {
  const context = useContext(HistoryContext)
  if (!context) {
    throw new Error("useHistory must be used within a HistoryProvider")
  }
  return context
}
