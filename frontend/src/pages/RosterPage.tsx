import { useState } from "react"
import { Link } from "react-router-dom"
import { useAppState } from "../state/AppStateContext"
import { Panel } from "../components/common/Panel"
import { EmptyState } from "../components/common/EmptyState"
import { Button } from "../components/common/Button"
import { ClusterTabs } from "../components/roster/ClusterTabs"
import { ClusterSummaryPanel } from "../components/roster/ClusterSummaryPanel"
import { EnsembleGraph } from "../components/roster/EnsembleGraph"
import { FormationSection } from "../components/roster/FormationSection"
import { groupSelectionsByStoryWeight } from "../utils/rosterGrouping"
import { downloadReportAsJson } from "../utils/exportReport"
import styles from "./RosterPage.module.css"

export function RosterPage() {
  const { report } = useAppState()
  const [activeIndex, setActiveIndex] = useState(0)
  // One actor name, shared by the cast cards, the risk register and the graph,
  // so pointing at any of the three highlights the same person in all of them.
  const [linkedName, setLinkedName] = useState<string | null>(null)

  if (!report || report.recommendations.length === 0) {
    return (
      <EmptyState title="No roster yet">
        <p>Run a screenplay through the ingest flow to get ranked cast clusters here.</p>
        <Link to="/ingest">
          <Button variant="primary">Go to Ingest →</Button>
        </Link>
      </EmptyState>
    )
  }

  const recommendation = report.recommendations[Math.min(activeIndex, report.recommendations.length - 1)]
  const buckets = groupSelectionsByStoryWeight(recommendation.cluster.selections)
  const allScores = report.recommendations.map((entry) => entry.cluster.chemistry_score)

  return (
    <Panel className={styles.panel}>
      <ClusterTabs
        recommendations={report.recommendations}
        activeIndex={activeIndex}
        onSelect={setActiveIndex}
        actions={<Button onClick={() => downloadReportAsJson(report)}>Export sheet</Button>}
      />

      <div className={styles.body}>
        <div className={styles.tree}>
          {buckets.map(([bucket, selections]) => (
            <FormationSection
              key={bucket}
              bucket={bucket}
              selections={selections}
              topRisks={recommendation.top_risks}
              linkedName={linkedName}
              onLinkChange={setLinkedName}
            />
          ))}

          <EnsembleGraph
            selections={recommendation.cluster.selections}
            linkedName={linkedName}
            onLinkChange={setLinkedName}
          />
        </div>

        <ClusterSummaryPanel
          recommendation={recommendation}
          rank={activeIndex}
          allScores={allScores}
          linkedName={linkedName}
          onLinkChange={setLinkedName}
        />
      </div>
    </Panel>
  )
}
