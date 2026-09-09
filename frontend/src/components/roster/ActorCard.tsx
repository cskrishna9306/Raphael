import { useEffect, useRef, useState } from "react"
import type { CastingCandidate, CastingSelection, RiskAssessment, SwapPreview } from "../../api/types"
import type { AlternateCandidate } from "../../utils/rosterGrouping"
import { riskAssessmentFor } from "../../utils/rosterGrouping"
import { Avatar } from "../common/Avatar"
import { RiskBadge } from "../common/RiskBadge"
import { Shimmer } from "../common/Shimmer"
import { toDisplayName } from "../../utils/format"
import styles from "./ActorCard.module.css"

interface ActorCardProps {
  selection: CastingSelection
  risk?: RiskAssessment
  alternates: AlternateCandidate[]
  riskAssessments: RiskAssessment[]
  swapping: boolean
  onSwap: (candidate: CastingCandidate) => void
  onPreview: () => Promise<SwapPreview[]>
  emphasize?: boolean
  size?: "lg" | "md" | "sm"
  /** True while this actor is hovered anywhere else (e.g. the risk register). */
  linked?: boolean
  onLinkChange?: (name: string | null) => void
}

// One 2:3 headshot ratio at three scales, so faces crop identically down the
// page instead of being squared off at one size and portrait at another.
const AVATAR_WIDTH: Record<NonNullable<ActorCardProps["size"]>, number> = { lg: 72, md: 56, sm: 40 }

function formatDelta(delta: number): string {
  const rounded = Math.round(delta * 100) / 100
  return `${rounded >= 0 ? "+" : ""}${rounded.toFixed(2)}`
}

export function ActorCard({
  selection,
  risk,
  alternates,
  riskAssessments,
  swapping,
  onSwap,
  onPreview,
  emphasize,
  size = "md",
  linked,
  onLinkChange,
}: ActorCardProps) {
  const [showRationale, setShowRationale] = useState(false)
  const [showSwapPicker, setShowSwapPicker] = useState(false)
  const [previews, setPreviews] = useState<SwapPreview[] | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const { character, candidate } = selection
  const width = AVATAR_WIDTH[size]

  const canSwap = alternates.length > 0 && !swapping

  // Click-anywhere-outside closes the picker, same as any dropdown/popover convention.
  useEffect(() => {
    if (!showSwapPicker) return
    const handleOutsideClick = (event: MouseEvent) => {
      if (cardRef.current && !cardRef.current.contains(event.target as Node)) {
        setShowSwapPicker(false)
      }
    }
    document.addEventListener("mousedown", handleOutsideClick)
    return () => document.removeEventListener("mousedown", handleOutsideClick)
  }, [showSwapPicker])

  // Fetch chemistry-ranked previews only once the picker is actually opened, not on every render.
  useEffect(() => {
    if (!showSwapPicker) return
    let cancelled = false
    setPreviews(null)
    setPreviewError(null)
    onPreview()
      .then((result) => {
        if (!cancelled) setPreviews(result)
      })
      .catch(() => {
        if (!cancelled) setPreviewError("Could not preview these swaps.")
      })
    return () => {
      cancelled = true
    }
  }, [showSwapPicker, onPreview])

  const handlePick = (alternate: CastingCandidate) => {
    setShowSwapPicker(false)
    onSwap(alternate)
  }

  return (
    <div
      ref={cardRef}
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
      <div
        className={[styles.body, canSwap ? styles.swappable : ""].filter(Boolean).join(" ")}
        onClick={canSwap ? () => setShowSwapPicker((open) => !open) : undefined}
      >
        <Avatar src={candidate.headshot_url} alt={candidate.name} width={width} height={Math.round(width * 1.5)} />

        <div className={styles.info}>
          {/* Character and role on their own lines: this mapping is the whole
              product, and it used to truncate mid-word on both halves. */}
          <div className={styles.character}>{toDisplayName(character.name)}</div>
          {swapping ? (
            <Shimmer width="80%" height={18} />
          ) : (
            <div className={styles.candidateName}>{candidate.name}</div>
          )}
          <div className={styles.metaRow}>
            <span className={styles.role}>{character.role_presence}</span>
            {risk ? <RiskBadge level={risk.risk_level} /> : null}
          </div>
          {canSwap ? <span className={styles.swapHint}>⇄ Swap</span> : null}
        </div>
      </div>

      {/* Hidden while the picker is open so the two never stack on one card. */}
      {candidate.fit_rationale && !showSwapPicker ? (
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

      {showSwapPicker ? (
        <div className={styles.popover}>
          <div className={styles.popoverLabel}>
            Swap in for {toDisplayName(character.name)} · ranked by chemistry impact
          </div>
          <div className={styles.swapList}>
            {previewError ? (
              <div className={styles.swapError}>{previewError}</div>
            ) : !previews ? (
              <>
                <Shimmer height={34} />
                <Shimmer height={34} />
              </>
            ) : (
              previews.map((preview) => {
                const altRisk = riskAssessmentFor(preview.candidate.name, riskAssessments)
                return (
                  <button
                    key={preview.candidate.name}
                    type="button"
                    className={styles.swapOption}
                    onClick={() => handlePick(preview.candidate)}
                  >
                    <div className={styles.swapOptionRow}>
                      <span className={styles.swapOptionName}>{preview.candidate.name}</span>
                      <span
                        className={[
                          preview.delta >= 0 ? styles.deltaPositive : styles.deltaNegative,
                          preview.estimated ? styles.estimated : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        title={
                          preview.estimated
                            ? "No shared-credit history with this cast -- rough estimate, not observed evidence"
                            : undefined
                        }
                      >
                        {formatDelta(preview.delta)}
                        {preview.estimated ? "*" : ""}
                      </span>
                      {altRisk ? <RiskBadge level={altRisk.risk_level} /> : null}
                    </div>
                    {preview.per_costar.length > 0 || preview.estimated || preview.used_in_other_cluster ? (
                      <div className={styles.costarRow}>
                        {preview.per_costar.map((costar) => (
                          <span
                            key={costar.name}
                            className={costar.delta >= 0 ? styles.deltaPositive : styles.deltaNegative}
                          >
                            {costar.name} {formatDelta(costar.delta)}
                          </span>
                        ))}
                        {preview.estimated ? (
                          <span className={styles.estimatedNote}>
                            * no shared-credit history with this cast -- estimated
                          </span>
                        ) : null}
                        {preview.used_in_other_cluster ? (
                          <span className={styles.estimatedNote}>⚠ already leads another cluster</span>
                        ) : null}
                      </div>
                    ) : null}
                  </button>
                )
              })
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
