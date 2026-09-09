import { useState } from "react"
import { Link } from "react-router-dom"
import { useAppState } from "../state/AppStateContext"
import { ApiError, previewSwaps, swapCandidate } from "../api/client"
import type { CastingCandidate, SwapPreview } from "../api/types"
import { Panel } from "../components/common/Panel"
import { EmptyState } from "../components/common/EmptyState"
import { Button } from "../components/common/Button"
import { ErrorBanner } from "../components/common/ErrorBanner"
import { ClusterTabs } from "../components/roster/ClusterTabs"
import { ClusterSummaryPanel, type SwapDelta } from "../components/roster/ClusterSummaryPanel"
import { EnsembleGraph } from "../components/roster/EnsembleGraph"
import { FormationSection } from "../components/roster/FormationSection"
import { groupSelectionsByStoryWeight } from "../utils/rosterGrouping"
import { downloadReportAsJson } from "../utils/exportReport"
import styles from "./RosterPage.module.css"

export function RosterPage() {
  const { report, updateRecommendation } = useAppState()
  const [activeIndex, setActiveIndex] = useState(0)
  // One actor name, shared by the cast cards, the risk register and the graph,
  // so pointing at any of the three highlights the same person in all of them.
  const [linkedName, setLinkedName] = useState<string | null>(null)
  const [swappingCharacter, setSwappingCharacter] = useState<string | null>(null)
  const [swapError, setSwapError] = useState<string | null>(null)
  const [swapDelta, setSwapDelta] = useState<SwapDelta | null>(null)

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

  const handleSelectTab = (index: number) => {
    setActiveIndex(index)
    setSwapError(null)
    setSwapDelta(null)
  }

  const handleSwap = async (characterName: string, candidate: CastingCandidate) => {
    setSwapError(null)
    setSwappingCharacter(characterName)
    const previousScore = recommendation.cluster.chemistry_score
    try {
      const selections = recommendation.cluster.selections.map((selection) =>
        selection.character.name === characterName ? { ...selection, candidate } : selection,
      )
      const result = await swapCandidate({
        roster: report.roster,
        selections,
        reference_scores: report.recommendations.map((r) => r.cluster.chemistry_score),
      })
      updateRecommendation(activeIndex, result)
      setSwapDelta({ characterName, from: previousScore, to: result.cluster.chemistry_score })
    } catch (err) {
      setSwapError(err instanceof ApiError ? err.message : "Could not recompute this swap -- is the server running?")
    } finally {
      setSwappingCharacter(null)
    }
  }

  const handlePreview = async (characterName: string): Promise<SwapPreview[]> => {
    // Every actor already cast in this report's OTHER clusters, across every role -- flagged
    // (not filtered out) on the returned previews via used_in_other_cluster. Keeps a swap from
    // silently reintroducing a duplicate cast member across clusters.
    const usedElsewhere = report.recommendations
      .filter((_, index) => index !== activeIndex)
      .flatMap((r) => r.cluster.selections.map((s) => s.candidate.name))

    const response = await previewSwaps({
      roster: report.roster,
      selections: recommendation.cluster.selections,
      character_name: characterName,
      used_elsewhere: usedElsewhere,
    })
    return response.previews
  }

  return (
    <Panel className={styles.panel}>
      <ClusterTabs
        recommendations={report.recommendations}
        activeIndex={activeIndex}
        onSelect={handleSelectTab}
        actions={<Button onClick={() => downloadReportAsJson(report)}>Export sheet</Button>}
      />
      {swapError ? <ErrorBanner message={swapError} /> : null}


      <div className={styles.body}>
        <div className={styles.tree}>
          {buckets.map(([bucket, selections]) => (
            <FormationSection
              key={bucket}
              bucket={bucket}
              selections={selections}
              topRisks={recommendation.top_risks}
              roster={report.roster}
              swappingCharacter={swappingCharacter}
              onSwap={handleSwap}
              onPreview={handlePreview}
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
          swapDelta={
            swapDelta?.characterName &&
            recommendation.cluster.selections.some((s) => s.character.name === swapDelta.characterName)
              ? swapDelta
              : null
          }
          linkedName={linkedName}
          onLinkChange={setLinkedName}
        />
      </div>
    </Panel>
  )
}
