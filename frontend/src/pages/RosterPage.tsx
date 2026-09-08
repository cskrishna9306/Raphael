import { useState } from "react"
import { Link } from "react-router-dom"
import { useAppState } from "../state/AppStateContext"
import { Panel } from "../components/common/Panel"
import { EmptyState } from "../components/common/EmptyState"
import { Button } from "../components/common/Button"
import { ClusterTabs } from "../components/roster/ClusterTabs"
import { ClusterSummaryPanel } from "../components/roster/ClusterSummaryPanel"
import { FormationSection } from "../components/roster/FormationSection"
import { groupSelectionsByStoryWeight } from "../utils/rosterGrouping"
import { downloadReportAsJson } from "../utils/exportReport"
import styles from "./RosterPage.module.css"

export function RosterPage() {
  const { report } = useAppState()
  const [activeIndex, setActiveIndex] = useState(0)

  if (!report || report.recommendations.length === 0) {
    return (
      <EmptyState title="No roster yet">
        <p>Run a screenplay through the ingest flow to get ranked cast clusters here.</p>
        <Link to="/">
          <Button variant="primary">Go to Ingest →</Button>
        </Link>
      </EmptyState>
    )
  }

  const recommendation = report.recommendations[Math.min(activeIndex, report.recommendations.length - 1)]
  const buckets = groupSelectionsByStoryWeight(recommendation.cluster.selections)

  return (
    <Panel className={styles.panel}>
      <ClusterTabs recommendations={report.recommendations} activeIndex={activeIndex} onSelect={setActiveIndex} />
      <div className={styles.actionsRow}>
        <Button onClick={() => downloadReportAsJson(report)}>Export sheet</Button>
      </div>
      <div className={styles.body}>
        <div className={styles.tree}>
          {buckets.map(([bucket, selections]) => (
            <FormationSection key={bucket} bucket={bucket} selections={selections} topRisks={recommendation.top_risks} />
          ))}
        </div>
        <ClusterSummaryPanel recommendation={recommendation} rank={activeIndex} />
      </div>
    </Panel>
  )
}
