import type { ClusterRecommendation } from "../../api/types"
import { formatChemistryScore } from "../../utils/format"
import { RiskList } from "./RiskList"
import styles from "./ClusterSummaryPanel.module.css"

export interface SwapDelta {
  characterName: string
  from: number
  to: number
}

interface ClusterSummaryPanelProps {
  recommendation: ClusterRecommendation
  rank: number
  /** Every cluster's score, so this one can be placed against the others. */
  allScores: number[]
  /** Set after a /swap, to show what the substitution did to the score. */
  swapDelta?: SwapDelta | null
  linkedName: string | null
  onLinkChange: (name: string | null) => void
}

export function ClusterSummaryPanel({
  recommendation,
  rank,
  allScores,
  swapDelta,
  linkedName,
  onLinkChange,
}: ClusterSummaryPanelProps) {
  const { cluster, top_risks } = recommendation

  // ChemistryEngine bands scores relative to the run, so there is no fixed
  // 0-1 range to plot against. The honest scale is this run's own spread.
  const min = Math.min(...allScores)
  const max = Math.max(...allScores)
  const span = max - min
  const position = span > 0 ? (cluster.chemistry_score - min) / span : 1

  const sorted = [...allScores].sort((a, b) => b - a)
  const next = sorted.find((score) => score < cluster.chemistry_score)
  const delta = next === undefined ? null : cluster.chemistry_score - next

  return (
    <aside className={styles.panel}>
      <div className={styles.block}>
        <h3 className={styles.label}>Ensemble chemistry</h3>
        <div className={styles.scoreRow}>
          <span className={`${styles.scoreValue} tabular`}>{formatChemistryScore(cluster.chemistry_score)}</span>
          <span className={styles[cluster.strength]}>{cluster.strength}</span>
        </div>

        <div className={styles.track}>
          <div className={styles.fill} style={{ width: `${Math.max(4, position * 100)}%` }} />
        </div>
        <div className={styles.ticks}>
          <span className="tabular">{formatChemistryScore(min)}</span>
          <span>
            rank {rank + 1} of {allScores.length}
            {delta !== null ? ` · +${formatChemistryScore(delta)} vs next` : ""}
          </span>
          <span className="tabular">{formatChemistryScore(max)}</span>
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

      <div className={styles.block}>
        <h3 className={styles.label}>Risk register</h3>
        <RiskList risks={top_risks} linkedName={linkedName} onLinkChange={onLinkChange} />
      </div>
    </aside>
  )
}
