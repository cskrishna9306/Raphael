import type { CastingCandidate, CastingSelection, RiskAssessment, RolePresence, Roster } from "../api/types"

export type StoryWeightBucket = "Lead" | "Supporting" | "Ensemble"

const BUCKET_BY_ROLE: Record<RolePresence, StoryWeightBucket> = {
  lead: "Lead",
  supporting: "Supporting",
  minor: "Ensemble",
  background: "Ensemble",
  extra: "Ensemble",
}

const BUCKET_ORDER: StoryWeightBucket[] = ["Lead", "Supporting", "Ensemble"]

/**
 * Groups a cluster's selections by story weight (lead -> supporting ->
 * ensemble), the same visual hierarchy as the roster wireframe's formation
 * tree, derived from CharacterProfile.role_presence since the API doesn't
 * return a separate "story weight" field.
 */
export function groupSelectionsByStoryWeight(selections: CastingSelection[]): Array<[StoryWeightBucket, CastingSelection[]]> {
  const buckets = new Map<StoryWeightBucket, CastingSelection[]>()
  for (const selection of selections) {
    const bucket = BUCKET_BY_ROLE[selection.character.role_presence]
    const existing = buckets.get(bucket)
    if (existing) existing.push(selection)
    else buckets.set(bucket, [selection])
  }
  return BUCKET_ORDER.filter((bucket) => buckets.has(bucket)).map((bucket) => [bucket, buckets.get(bucket)!])
}

/** Finds the RiskAssessment for a candidate in any RiskAssessment list -- a cluster's top_risks or the full roster's risk_assessments. */
export function riskAssessmentFor(name: string, risks: RiskAssessment[]): RiskAssessment | undefined {
  return risks.find((risk) => risk.name === name)
}

export interface AlternateCandidate {
  candidate: CastingCandidate
  risk?: RiskAssessment
}

/**
 * The other candidates a character could be swapped to -- everyone in that
 * character's shortlist (Roster.casting_report) besides whoever is
 * currently selected, each paired with their risk assessment for display.
 */
export function alternatesFor(characterName: string, currentCandidateName: string, roster: Roster): AlternateCandidate[] {
  const shortlist = roster.casting_report.castings.find((casting) => casting.character.name === characterName)?.candidates ?? []
  return shortlist
    .filter((candidate) => candidate.name !== currentCandidateName)
    .map((candidate) => ({ candidate, risk: riskAssessmentFor(candidate.name, roster.risk_assessments) }))
}
