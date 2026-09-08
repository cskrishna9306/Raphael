import { useState } from "react"
import type { RiskAssessment } from "../../api/types"
import { RiskBadge } from "../common/RiskBadge"
import styles from "./RiskList.module.css"

export function RiskList({ risks }: { risks: RiskAssessment[] }) {
  const [expandedName, setExpandedName] = useState<string | null>(null)

  if (risks.length === 0) {
    return <div className={styles.empty}>No flagged risks for this cluster.</div>
  }

  return (
    <div className={styles.list}>
      {risks.map((risk) => {
        const isExpanded = expandedName === risk.name
        return (
          <button
            key={risk.name}
            type="button"
            className={styles.item}
            onClick={() => setExpandedName(isExpanded ? null : risk.name)}
          >
            <div className={styles.header}>
              <span className={styles.name}>{risk.name}</span>
              <RiskBadge level={risk.risk_level} />
            </div>
            {isExpanded ? (
              <div className={styles.detail}>
                <p className={styles.rationale}>{risk.rationale}</p>
                {risk.flags.map((flag, index) => (
                  <div key={index} className={styles.flag}>
                    <span className={styles.flagCategory}>{flag.category}</span>
                    <span>{flag.description}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </button>
        )
      })}
    </div>
  )
}
