import { createContext, useContext, useMemo, useState, type ReactNode } from "react"
import type { ClusterRecommendation, RecommendationReport, Screenplay } from "../api/types"

interface AppState {
  screenplay: Screenplay | null
  report: RecommendationReport | null
  /** Id of the saved project these two belong to, or null for work not saved to history yet. */
  projectId: string | null
  /**
   * Bumped by every reset(). The ingest route uses it as a React key, so
   * starting over also clears that page's own local state (the dropped file,
   * the stage) rather than leaving it pointing at the previous screenplay.
   */
  sessionKey: number
  setScreenplay: (screenplay: Screenplay | null) => void
  setReport: (report: RecommendationReport | null) => void
  setProjectId: (projectId: string | null) => void
  /** Overwrites one cluster slot in place (e.g. after a /swap) -- other ranked clusters are untouched. */
  updateRecommendation: (index: number, next: ClusterRecommendation) => void
  reset: () => void
}

const AppStateContext = createContext<AppState | null>(null)

/**
 * Holds the pipeline's state (the Screenplay from /analyze, the
 * RecommendationReport from /recommend, and the history project they belong
 * to) so the Roster page and the history sidebar can read them without
 * re-fetching or prop-drilling through the router.
 */
export function AppStateProvider({ children }: { children: ReactNode }) {
  const [screenplay, setScreenplay] = useState<Screenplay | null>(null)
  const [report, setReport] = useState<RecommendationReport | null>(null)
  const [projectId, setProjectId] = useState<string | null>(null)
  const [sessionKey, setSessionKey] = useState(0)

  const value = useMemo<AppState>(
    () => ({
      screenplay,
      report,
      projectId,
      sessionKey,
      setScreenplay,
      setReport,
      setProjectId,
      updateRecommendation: (index, next) => {
        setReport((current) => {
          if (!current) return current
          const recommendations = current.recommendations.slice()
          recommendations[index] = next
          return { ...current, recommendations }
        })
      },
      reset: () => {
        setScreenplay(null)
        setReport(null)
        setProjectId(null)
        setSessionKey((current) => current + 1)
      },
    }),
    [screenplay, report, projectId, sessionKey],
  )

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>
}

export function useAppState(): AppState {
  const context = useContext(AppStateContext)
  if (!context) {
    throw new Error("useAppState must be used within an AppStateProvider")
  }
  return context
}
