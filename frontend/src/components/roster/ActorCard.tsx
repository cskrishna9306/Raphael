import { useEffect, useRef, useState } from "react"
import type { CastingCandidate, CastingSelection, RiskAssessment, SwapPreview } from "../../api/types"
import type { AlternateCandidate } from "../../utils/rosterGrouping"
import { riskAssessmentFor } from "../../utils/rosterGrouping"
import { Avatar } from "../common/Avatar"
import { RiskBadge } from "../common/RiskBadge"
import { Shimmer } from "../common/Shimmer"
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
}

const AVATAR_SIZE: Record<NonNullable<ActorCardProps["size"]>, { width: number; height: number }> = {
  lg: { width: 74, height: 92 },
  md: { width: 56, height: 72 },
  sm: { width: 56, height: 56 },
}

function formatDelta(delta: number): string {
  const rounded = Math.round(delta * 100) / 100
  return `${rounded >= 0 ? "+" : ""}${rounded.toFixed(2)}`
}

export function ActorCard({ selection, risk, alternates, riskAssessments, swapping, onSwap, onPreview, emphasize, size = "md" }: ActorCardProps) {
  const [showRationale, setShowRationale] = useState(false)
  const [showSwapPicker, setShowSwapPicker] = useState(false)
  const [previews, setPreviews] = useState<SwapPreview[] | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const { character, candidate } = selection
  const avatar = AVATAR_SIZE[size]

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
        size === "sm" ? styles.compact : "",
        size === "lg" ? styles.large : "",
      ].join(" ")}
      onMouseEnter={() => setShowRationale(true)}
      onMouseLeave={() => setShowRationale(false)}
    >
      <div
        className={[styles.body, canSwap ? styles.swappable : ""].join(" ")}
        onClick={canSwap ? () => setShowSwapPicker((open) => !open) : undefined}
      >
        <Avatar src={candidate.headshot_url} alt={candidate.name} width={avatar.width} height={avatar.height} />
        <div className={styles.info}>
          <div className={styles.characterLine}>
            {character.name} · {character.role_presence}
          </div>
          {swapping ? (
            <Shimmer width="80%" height={16} />
          ) : (
            <div className={styles.candidateName}>{candidate.name}</div>
          )}
          {risk ? (
            <div className={styles.riskRow}>
              <RiskBadge level={risk.risk_level} />
            </div>
          ) : null}
          {canSwap ? <span className={styles.swapHint}>⇄ Tap to swap</span> : null}
        </div>
      </div>
      {showRationale && !showSwapPicker && candidate.fit_rationale ? (
        <div className={styles.popover}>
          <div className={styles.popoverLabel}>Fit rationale</div>
          <div className={styles.popoverBody}>{candidate.fit_rationale}</div>
        </div>
      ) : null}
      {showSwapPicker ? (
        <div className={styles.popover}>
          <div className={styles.popoverLabel}>Swap in for {character.name} · ranked by chemistry impact</div>
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
                        className={[preview.delta >= 0 ? styles.deltaPositive : styles.deltaNegative, preview.estimated ? styles.estimated : ""].join(" ")}
                        title={preview.estimated ? "No shared-credit history with this cast -- rough estimate, not observed evidence" : undefined}
                      >
                        {formatDelta(preview.delta)}
                        {preview.estimated ? "*" : ""}
                      </span>
                      {altRisk ? <RiskBadge level={altRisk.risk_level} /> : null}
                    </div>
                    {preview.per_costar.length > 0 || preview.estimated || preview.used_in_other_cluster ? (
                      <div className={styles.costarRow}>
                        {preview.per_costar.map((costar) => (
                          <span key={costar.name} className={costar.delta >= 0 ? styles.deltaPositive : styles.deltaNegative}>
                            {costar.name} {formatDelta(costar.delta)}
                          </span>
                        ))}
                        {preview.estimated ? <span className={styles.estimatedNote}>* no shared-credit history with this cast -- estimated</span> : null}
                        {preview.used_in_other_cluster ? (
                          <span className={styles.estimatedNote}>⚠ already cast in another cluster</span>
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
