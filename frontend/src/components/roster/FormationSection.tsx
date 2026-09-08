import type { CastingSelection, RiskAssessment } from "../../api/types"
import type { StoryWeightBucket } from "../../utils/rosterGrouping"
import { riskAssessmentFor } from "../../utils/rosterGrouping"
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
}

export function FormationSection({ bucket, selections, topRisks }: FormationSectionProps) {
  return (
    <div className={styles.section}>
      <div className={styles.label}>{bucket}</div>
      <div className={styles.cards}>
        {selections.map((selection) => (
          <ActorCard
            key={selection.character.name}
            selection={selection}
            risk={riskAssessmentFor(selection.candidate.name, topRisks)}
            emphasize={bucket === "Lead"}
            size={CARD_SIZE[bucket]}
          />
        ))}
      </div>
    </div>
  )
}
