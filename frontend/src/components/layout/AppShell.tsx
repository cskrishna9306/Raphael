import type { ReactNode } from "react"
import { useLocation } from "react-router-dom"
import { useBackendStatus } from "../../hooks/useBackendStatus"
import { HistorySidebar } from "../history/HistorySidebar"
import { NavBar } from "./NavBar"
import { RoadmapStages } from "./RoadmapStages"
import { StatusBanner } from "./StatusBanner"
import styles from "./AppShell.module.css"

// History only means something on the pipeline pages, where selecting an entry
// loads it. An allowlist rather than an exclusion, so neither the public
// landing page nor any future informational page picks the sidebar up by
// default. Same set of routes RoadmapStages shows itself for.
const HISTORY_ROUTES = ["/ingest", "/roster"]

export function AppShell({ children }: { children: ReactNode }) {
  const backendStatus = useBackendStatus()
  const { pathname } = useLocation()

  const showHistory = HISTORY_ROUTES.includes(pathname)

  return (
    <div className={styles.shell}>
      <StatusBanner status={backendStatus} />
      <NavBar />
      <main className={styles.main}>
        {showHistory ? (
          <div className={styles.workspace}>
            <HistorySidebar />
            {/* The roadmap lives in the content column, not above the whole
                workspace: centred across the page it reads as floating between
                the history rail and the panel rather than heading either. */}
            <div className={styles.content}>
              <RoadmapStages />
              {children}
            </div>
          </div>
        ) : (
          children
        )}
      </main>
    </div>
  )
}
