import { useState } from "react"
import { Link } from "react-router-dom"
import { useAppState } from "../state/AppStateContext"
import { Panel } from "../components/common/Panel"
import { EmptyState } from "../components/common/EmptyState"
import { Button } from "../components/common/Button"
import { RiskBadge } from "../components/common/RiskBadge"
import { ClusterTabs } from "../components/roster/ClusterTabs"
import { riskAssessmentFor } from "../utils/rosterGrouping"
import { formatChemistryScore } from "../utils/format"
import { downloadReportAsJson } from "../utils/exportReport"
import styles from "./CastingSheetPage.module.css"

export function CastingSheetPage() {
  const { report } = useAppState()
  const [activeIndex, setActiveIndex] = useState(0)

  if (!report || report.recommendations.length === 0) {
    return (
      <EmptyState title="No casting sheet yet">
        <p>Run a screenplay through the ingest flow to generate a sheet here.</p>
        <Link to="/">
          <Button variant="primary">Go to Ingest →</Button>
        </Link>
      </EmptyState>
    )
  }

  const recommendation = report.recommendations[Math.min(activeIndex, report.recommendations.length - 1)]

  return (
    <Panel className={styles.panel}>
      <ClusterTabs recommendations={report.recommendations} activeIndex={activeIndex} onSelect={setActiveIndex} />
      <div className={styles.actionsRow}>
        <span className={styles.scoreLabel}>
          chemistry {formatChemistryScore(recommendation.cluster.chemistry_score)} · {recommendation.cluster.strength}
        </span>
        <Button onClick={() => downloadReportAsJson(report)}>Export sheet</Button>
      </div>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Character</th>
              <th>Role</th>
              <th>Candidate</th>
              <th>Fit rationale</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {recommendation.cluster.selections.map((selection) => {
              const risk = riskAssessmentFor(selection.candidate.name, recommendation.top_risks)
              return (
                <tr key={selection.character.name}>
                  <td>{selection.character.name}</td>
                  <td className={styles.roleCell}>{selection.character.role_presence}</td>
                  <td>{selection.candidate.name}</td>
                  <td className={styles.rationaleCell}>{selection.candidate.fit_rationale ?? "—"}</td>
                  <td>{risk ? <RiskBadge level={risk.risk_level} /> : "—"}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}
