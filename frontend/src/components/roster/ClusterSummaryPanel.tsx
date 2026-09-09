import type { ClusterRecommendation } from "../../api/types"
import { formatChemistryScore } from "../../utils/format"
import { RiskList } from "./RiskList"
import styles from "./ClusterSummaryPanel.module.css"

export interface SwapDelta {
  characterName: string
  from: number
  to: number
}

export function ClusterSummaryPanel({
  recommendation,
  rank,
  swapDelta,
}: {
  recommendation: ClusterRecommendation
  rank: number
  swapDelta?: SwapDelta | null
}) {
  const { cluster, top_risks } = recommendation

  return (
    <div className={styles.panel}>
      <div className={styles.label}>Cluster {String(rank + 1).padStart(2, "0")} summary</div>
      <div className={styles.scoreCard}>
        <div className={styles.scoreRow}>
          <span className={styles.scoreValue}>{formatChemistryScore(cluster.chemistry_score)}</span>
          <span className={styles.scoreCaption}>ensemble chemistry · {cluster.strength}</span>
        </div>
        {swapDelta ? (
          <div className={styles.deltaRow}>
            After swapping {swapDelta.characterName}: {formatChemistryScore(swapDelta.from)} → {formatChemistryScore(swapDelta.to)}
            {" "}
            ({swapDelta.to >= swapDelta.from ? "+" : ""}
            {formatChemistryScore(swapDelta.to - swapDelta.from)})
          </div>
        ) : null}
      </div>

      <div className={styles.label}>Risk register</div>
      <RiskList risks={top_risks} />
    </div>
  )
}
