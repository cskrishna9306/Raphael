import type { CastingCandidate, CastingSelection, RiskAssessment, Roster, SwapPreview } from "../../api/types"
import type { StoryWeightBucket } from "../../utils/rosterGrouping"
import { alternatesFor, riskAssessmentFor } from "../../utils/rosterGrouping"
import { ActorCard } from "./ActorCard"
import styles from "./FormationSection.module.css"

const CARD_SIZE: Record<StoryWeightBucket, "lg" | "md" | "sm"> = {
  Lead: "lg",
  Supporting: "md",
  Ensemble: "sm",
}

interface FormationSectionProps {
  bucket: StoryWeightBucket
  selections: CastingSelection[]
  topRisks: RiskAssessment[]
  roster: Roster
  swappingCharacter: string | null
  onSwap: (characterName: string, candidate: CastingCandidate) => void
  onPreview: (characterName: string) => Promise<SwapPreview[]>
}

export function FormationSection({ bucket, selections, topRisks, roster, swappingCharacter, onSwap, onPreview }: FormationSectionProps) {
  return (
    <div className={styles.section}>
      <div className={styles.label}>{bucket}</div>
      <div className={styles.cards}>
        {selections.map((selection) => (
          <ActorCard
            key={selection.character.name}
            selection={selection}
            risk={riskAssessmentFor(selection.candidate.name, topRisks)}
            alternates={alternatesFor(selection.character.name, selection.candidate.name, roster)}
            riskAssessments={roster.risk_assessments}
            swapping={swappingCharacter === selection.character.name}
            onSwap={(candidate) => onSwap(selection.character.name, candidate)}
            onPreview={() => onPreview(selection.character.name)}
            emphasize={bucket === "Lead"}
            size={CARD_SIZE[bucket]}
          />
        ))}
      </div>
    </div>
  )
}
