import type { CastingSelection, RiskAssessment, RolePresence } from "../api/types"

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

/** Finds the RiskAssessment for a candidate, if RecommendationReport's top_risks included them. */
export function riskAssessmentFor(name: string, topRisks: RiskAssessment[]): RiskAssessment | undefined {
  return topRisks.find((risk) => risk.name === name)
}
