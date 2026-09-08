import type { RiskLevel } from "../../api/types"
import styles from "./RiskBadge.module.css"

const LABEL: Record<RiskLevel, string> = {
  low: "LOW",
  medium: "MED",
  high: "HIGH",
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={[styles.badge, styles[level]].join(" ")}>
      <span className={styles.dot} />
      {LABEL[level]}
    </span>
  )
}
