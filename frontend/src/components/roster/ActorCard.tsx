import { useState } from "react"
import type { CastingSelection, RiskAssessment } from "../../api/types"
import { AvatarPlaceholder } from "../common/AvatarPlaceholder"
import { RiskBadge } from "../common/RiskBadge"
import styles from "./ActorCard.module.css"

interface ActorCardProps {
  selection: CastingSelection
  risk?: RiskAssessment
  emphasize?: boolean
  size?: "lg" | "md" | "sm"
}

const AVATAR_SIZE: Record<NonNullable<ActorCardProps["size"]>, { width: number; height: number }> = {
  lg: { width: 74, height: 92 },
  md: { width: 56, height: 72 },
  sm: { width: 56, height: 56 },
}

export function ActorCard({ selection, risk, emphasize, size = "md" }: ActorCardProps) {
  const [showRationale, setShowRationale] = useState(false)
  const { character, candidate } = selection
  const avatar = AVATAR_SIZE[size]

  return (
    <div
      className={[
        styles.card,
        emphasize ? styles.emphasized : "",
        size === "sm" ? styles.compact : "",
        size === "lg" ? styles.large : "",
      ].join(" ")}
      onMouseEnter={() => setShowRationale(true)}
      onMouseLeave={() => setShowRationale(false)}
    >
      <div className={styles.body}>
        <AvatarPlaceholder width={avatar.width} height={avatar.height} />
        <div className={styles.info}>
          <div className={styles.characterLine}>
            {character.name} · {character.role_presence}
          </div>
          <div className={styles.candidateName}>{candidate.name}</div>
          {risk ? (
            <div className={styles.riskRow}>
              <RiskBadge level={risk.risk_level} />
            </div>
          ) : null}
        </div>
      </div>
      {showRationale && candidate.fit_rationale ? (
        <div className={styles.popover}>
          <div className={styles.popoverLabel}>Fit rationale</div>
          <div className={styles.popoverBody}>{candidate.fit_rationale}</div>
        </div>
      ) : null}
    </div>
  )
}
