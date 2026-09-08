import type { ClusterRecommendation } from "../../api/types"
import { formatChemistryScore } from "../../utils/format"
import styles from "./ClusterTabs.module.css"

interface ClusterTabsProps {
  recommendations: ClusterRecommendation[]
  activeIndex: number
  onSelect: (index: number) => void
}

export function ClusterTabs({ recommendations, activeIndex, onSelect }: ClusterTabsProps) {
  return (
    <div className={styles.tabs}>
      <div className={styles.label}>Cluster</div>
      <div className={styles.buttons}>
        {recommendations.map((recommendation, index) => (
          <button
            key={index}
            type="button"
            className={index === activeIndex ? styles.active : styles.inactive}
            onClick={() => onSelect(index)}
          >
            {String(index + 1).padStart(2, "0")} · {formatChemistryScore(recommendation.cluster.chemistry_score)}
          </button>
        ))}
      </div>
    </div>
  )
}
