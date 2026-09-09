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

// Tier hierarchy comes from card scale and a minimum track width rather than a
// fixed column count: the grid fits as many columns as the width allows and
// never squeezes a card below the point where names have to break mid-word.
const MIN_TRACK: Record<StoryWeightBucket, string> = {
  Lead: "250px",
  Supporting: "178px",
  Ensemble: "172px",
}

interface FormationSectionProps {
  bucket: StoryWeightBucket
  selections: CastingSelection[]
  topRisks: RiskAssessment[]
  linkedName: string | null
  onLinkChange: (name: string | null) => void
}

export function FormationSection({ bucket, selections, topRisks, linkedName, onLinkChange }: FormationSectionProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.label}>{bucket}</h3>
        <span className={styles.count}>
          {selections.length} {selections.length === 1 ? "role" : "roles"}
        </span>
      </div>
      <div className={styles.cards} style={{ "--min": MIN_TRACK[bucket] } as React.CSSProperties}>
        {selections.map((selection) => (
          <ActorCard
            key={selection.character.name}
            selection={selection}
            risk={riskAssessmentFor(selection.candidate.name, topRisks)}
            emphasize={bucket === "Lead"}
            size={CARD_SIZE[bucket]}
            linked={linkedName === selection.candidate.name}
            onLinkChange={onLinkChange}
          />
        ))}
      </div>
    </section>
  )
}
