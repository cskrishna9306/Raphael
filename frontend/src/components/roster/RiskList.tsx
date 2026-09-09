import { useState } from "react"
import type { RiskAssessment } from "../../api/types"
import { RiskBadge } from "../common/RiskBadge"
import styles from "./RiskList.module.css"

interface RiskListProps {
  risks: RiskAssessment[]
  /** Actor currently hovered elsewhere on the roster, if any. */
  linkedName: string | null
  onLinkChange: (name: string | null) => void
}

export function RiskList({ risks, linkedName, onLinkChange }: RiskListProps) {
  const [expandedName, setExpandedName] = useState<string | null>(null)

  if (risks.length === 0) {
    return <p className={styles.empty}>No flagged risks for this cluster.</p>
  }

  return (
    <div className={styles.list}>
      {risks.map((risk) => {
        const isExpanded = expandedName === risk.name
        const isLinked = linkedName === risk.name
        return (
          <div
            key={risk.name}
            className={[styles.item, isLinked ? styles.linked : ""].filter(Boolean).join(" ")}
            // Pointing at a register entry outlines that actor's card, and
            // pointing at a card outlines this row -- one instrument, not two
            // lists of the same facts.
            onMouseEnter={() => onLinkChange(risk.name)}
            onMouseLeave={() => onLinkChange(null)}
          >
            <button
              type="button"
              className={styles.trigger}
              aria-expanded={isExpanded}
              onClick={() => setExpandedName(isExpanded ? null : risk.name)}
            >
              <span className={styles.name}>{risk.name}</span>
              <RiskBadge level={risk.risk_level} />
              <span className={styles.chevron} aria-hidden="true">
                {isExpanded ? "−" : "+"}
              </span>
            </button>

            {isExpanded ? (
              <div className={styles.detail}>
                <p className={styles.rationale}>{risk.rationale}</p>
                {risk.flags.map((flag, index) => (
                  <div key={index} className={styles.flag}>
                    <span className={styles.flagCategory}>{flag.category}</span>
                    <span className={styles.flagBody}>{flag.description}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
