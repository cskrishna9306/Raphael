import type { ReactNode } from "react"
import { useBackendStatus } from "../../hooks/useBackendStatus"
import { NavBar } from "./NavBar"
import { RoadmapStages } from "./RoadmapStages"
import { StatusBanner } from "./StatusBanner"
import styles from "./AppShell.module.css"

export function AppShell({ children }: { children: ReactNode }) {
  const backendStatus = useBackendStatus()

  return (
    <div className={styles.shell}>
      <StatusBanner status={backendStatus} />
      <NavBar />
      <main className={styles.main}>
        <RoadmapStages />
        {children}
      </main>
    </div>
  )
}
