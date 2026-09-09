import { useState } from "react"
import type { CastingSelection, RiskAssessment } from "../../api/types"
import { Avatar } from "../common/Avatar"
import { RiskBadge } from "../common/RiskBadge"
import { toDisplayName } from "../../utils/format"
import styles from "./ActorCard.module.css"

interface ActorCardProps {
  selection: CastingSelection
  risk?: RiskAssessment
  emphasize?: boolean
  size?: "lg" | "md" | "sm"
  /** True while this actor is hovered anywhere else (e.g. the risk register). */
  linked?: boolean
  onLinkChange?: (name: string | null) => void
}

// One 2:3 headshot ratio at three scales, so faces crop identically down the
// page instead of being squared off at one size and portrait at another.
const AVATAR_WIDTH: Record<NonNullable<ActorCardProps["size"]>, number> = { lg: 72, md: 56, sm: 40 }

export function ActorCard({ selection, risk, emphasize, size = "md", linked, onLinkChange }: ActorCardProps) {
  const [showRationale, setShowRationale] = useState(false)
  const { character, candidate } = selection
  const width = AVATAR_WIDTH[size]

  return (
    <div
      className={[
        styles.card,
        emphasize ? styles.emphasized : "",
        linked ? styles.linked : "",
        size === "lg" ? styles.large : "",
        size === "sm" ? styles.compact : "",
      ]
        .filter(Boolean)
        .join(" ")}
      onMouseEnter={() => onLinkChange?.(candidate.name)}
      onMouseLeave={() => onLinkChange?.(null)}
    >
      <div className={styles.body}>
        <Avatar src={candidate.headshot_url} alt={candidate.name} width={width} height={Math.round(width * 1.5)} />

        <div className={styles.info}>
          {/* Character and role on their own lines: this mapping is the whole
              product, and it used to truncate mid-word on both halves. */}
          <div className={styles.character}>{toDisplayName(character.name)}</div>
          <div className={styles.candidateName}>{candidate.name}</div>
          <div className={styles.metaRow}>
            <span className={styles.role}>{character.role_presence}</span>
            {risk ? <RiskBadge level={risk.risk_level} /> : null}
          </div>
        </div>
      </div>

      {candidate.fit_rationale ? (
        <>
          {/* Was hover-only, so the reasoning -- the product's differentiator --
              was unreachable by keyboard and invisible on touch. */}
          <button
            type="button"
            className={styles.rationaleToggle}
            aria-expanded={showRationale}
            onClick={() => setShowRationale((open) => !open)}
          >
            <span className={styles.rationaleLead}>{candidate.fit_rationale}</span>
            <span className={styles.rationaleChevron} aria-hidden="true">
              {showRationale ? "−" : "+"}
            </span>
          </button>
          {showRationale ? <div className={styles.rationaleFull}>{candidate.fit_rationale}</div> : null}
        </>
      ) : null}
    </div>
  )
}
