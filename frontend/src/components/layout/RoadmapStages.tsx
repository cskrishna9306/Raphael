import { NavLink, useLocation } from "react-router-dom"
import { useAppState } from "../../state/AppStateContext"
import styles from "./RoadmapStages.module.css"

const STAGES = [
  { to: "/ingest", number: "01", label: "Ingest", body: "Break down the screenplay" },
  { to: "/roster", number: "02", label: "Roster", body: "Ranked cast clusters" },
]

export function RoadmapStages() {
  const { pathname } = useLocation()
  const { report } = useAppState()

  const activeIndex = STAGES.findIndex((stage) => stage.to === pathname)
  if (activeIndex === -1) return null

  return (
    <ol className={styles.roadmap}>
      {STAGES.map((stage, index) => {
        const isCurrent = index === activeIndex
        const isReached = index <= activeIndex
        const isLocked = stage.to === "/roster" && !report

        const content = (
          <>
            <div className={styles.track}>
              <span className={isReached ? styles.nodeReached : styles.node} />
            </div>
            <div className={styles.number}>{stage.number}</div>
            <div className={styles.label}>{stage.label}</div>
            <div className={styles.body}>{stage.body}</div>
          </>
        )

        const classNames = [
          styles.stage,
          isReached ? styles.stageReached : "",
          index < activeIndex ? styles.stageAdvanced : "",
          isLocked ? styles.stageLocked : "",
        ]

        return (
          <li key={stage.to} className={classNames.filter(Boolean).join(" ")} aria-current={isCurrent ? "step" : undefined}>
            {isLocked ? (
              <div className={styles.stageInner} aria-disabled="true">
                {content}
              </div>
            ) : (
              <NavLink to={stage.to} className={styles.stageInner}>
                {content}
              </NavLink>
            )}
          </li>
        )
      })}
    </ol>
  )
}
