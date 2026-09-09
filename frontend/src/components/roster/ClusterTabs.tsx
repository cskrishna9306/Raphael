import type { ReactNode } from "react"
import type { ClusterRecommendation } from "../../api/types"
import { formatChemistryScore } from "../../utils/format"
import styles from "./ClusterTabs.module.css"

interface ClusterTabsProps {
  recommendations: ClusterRecommendation[]
  activeIndex: number
  onSelect: (index: number) => void
  /** Actions share this strip rather than getting a band of their own. */
  actions?: ReactNode
}

/** How many of a cluster's actors carry a high-risk assessment. */
function highRiskCount(recommendation: ClusterRecommendation): number {
  return recommendation.top_risks.filter((risk) => risk.risk_level === "high").length
}

export function ClusterTabs({ recommendations, activeIndex, onSelect, actions }: ClusterTabsProps) {
  return (
    <div className={styles.tabs} role="tablist" aria-label="Cast alternatives">
      <div className={styles.buttons}>
        {recommendations.map((recommendation, index) => {
          const isActive = index === activeIndex
          const flagged = highRiskCount(recommendation)
          return (
            <button
              key={index}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={isActive ? styles.active : styles.inactive}
              onClick={() => onSelect(index)}
            >
              {/* Labelled by what distinguishes each option -- rank, score and
                  flagged actors -- instead of an opaque index. */}
              <span className={styles.rank}>{index === 0 ? "Best" : `#${index + 1}`}</span>
              <span className={`${styles.score} tabular`}>
                {formatChemistryScore(recommendation.cluster.chemistry_score)}
              </span>
              {flagged > 0 ? (
                <span className={styles.flag} title={`${flagged} high-risk`}>
                  {flagged}▲
                </span>
              ) : null}
            </button>
          )
        })}
      </div>
      {actions ? <div className={styles.actions}>{actions}</div> : null}
    </div>
  )
}
