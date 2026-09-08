import { createContext, useContext, useMemo, useState, type ReactNode } from "react"
import type { RecommendationReport, Screenplay } from "../api/types"

interface AppState {
  screenplay: Screenplay | null
  report: RecommendationReport | null
  setScreenplay: (screenplay: Screenplay | null) => void
  setReport: (report: RecommendationReport | null) => void
  reset: () => void
}

const AppStateContext = createContext<AppState | null>(null)

/**
 * Holds the two pieces of state produced by the pipeline (the Screenplay
 * from /analyze, the RecommendationReport from /recommend) so the Roster and
 * Casting sheet pages can read them without re-fetching or prop-drilling
 * through the router.
 */
export function AppStateProvider({ children }: { children: ReactNode }) {
  const [screenplay, setScreenplay] = useState<Screenplay | null>(null)
  const [report, setReport] = useState<RecommendationReport | null>(null)

  const value = useMemo<AppState>(
    () => ({
      screenplay,
      report,
      setScreenplay,
      setReport,
      reset: () => {
        setScreenplay(null)
        setReport(null)
      },
    }),
    [screenplay, report],
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
