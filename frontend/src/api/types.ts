/**
 * TypeScript mirrors of the pydantic models returned by Raphael's FastAPI
 * server (src/raphael/**\/models.py). Kept in one file since they map 1:1
 * to the backend response/request shapes for /analyze and /recommend --
 * split it up if it ever grows beyond that.
 */

export type Gender = "male" | "female" | "non_binary" | "unspecified"

export type RolePresence = "lead" | "supporting" | "minor" | "background" | "extra"

export interface CharacterProfile {
  name: string
  aliases?: string[] | null
  role_presence: RolePresence
  gender: Gender
  age_range?: string | null
  description?: string | null
  traits?: string[] | null
  /** Director-supplied casting choice for this role -- set before /recommend to cast this actor directly, skipping candidate search. */
  preferred_actor?: string | null
}

export interface Cast {
  characters: CharacterProfile[]
}

export interface Screenplay {
  title: string
  cast: Cast
}

// -- /recommend response --------------------------------------------------

export interface FilmographyItem {
  title: string
  year?: number | null
  role: string
  character_or_contribution?: string | null
  box_office?: string | null
  critical_reception?: string | null
  key_collaborators: string[]
}

export interface CollaboratorCredit {
  name: string
  role: string
  shared_projects: string[]
  public_statements_about_collaboration: string[]
}

export interface Recognition {
  awards_and_nominations: string[]
  documented_controversies: string[]
}

export interface CastingAttributes {
  age?: number | null
  gender?: string | null
  nationality?: string | null
}

export interface PersonDossier {
  name: string
  primary_roles: string[]
  bio_summary?: string | null
  filmography: FilmographyItem[]
  collaborators: CollaboratorCredit[]
  recognition: Recognition
  attributes: CastingAttributes
}

export interface CastingCandidate {
  name: string
  fit_rationale?: string | null
  dossier?: PersonDossier | null
  headshot_url?: string | null
}

export interface CastingCharacter {
  character: CharacterProfile
  candidates: CastingCandidate[]
}

export interface CastingReport {
  title?: string | null
  castings: CastingCharacter[]
}

export interface CastingSelection {
  character: CharacterProfile
  candidate: CastingCandidate
}

export type ChemistryStrength = "high" | "medium" | "low"

export interface CastingCluster {
  selections: CastingSelection[]
  chemistry_score: number
  strength: ChemistryStrength
}

export type RiskLevel = "low" | "medium" | "high"

export interface RiskFlag {
  category: string
  description: string
  source?: string | null
}

export interface RiskAssessment {
  name: string
  risk_level: RiskLevel
  rationale: string
  flags: RiskFlag[]
}

export interface ClusterRecommendation {
  cluster: CastingCluster
  top_risks: RiskAssessment[]
}

export interface Roster {
  title?: string | null
  /** Every character's full candidate shortlist, dossiers already merged in -- the pool swaps are drawn from. */
  casting_report: CastingReport
  /** Every unique candidate's risk assessment, not just each cluster's top 3. */
  risk_assessments: RiskAssessment[]
}

export interface RecommendationReport {
  title?: string | null
  recommendations: ClusterRecommendation[]
  roster: Roster
}

// -- /projects (per-user history) -----------------------------------------

/** One row of the history list -- deliberately without the report, which the list never renders. */
export interface ProjectSummary {
  id: string
  title: string
  character_count: number
  has_report: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface Project {
  id: string
  title: string
  screenplay: Screenplay
  latest_report?: RecommendationReport | null
  created_at?: string | null
  updated_at?: string | null
}
// -- /swap request ----------------------------------------------------------

export interface SwapRequest {
  roster: Roster
  /** The full cluster's selections (one per character) with the swap already applied. */
  selections: CastingSelection[]
  /** chemistry_score of the prior RecommendationReport's recommendations, for high/medium/low bucketing. */
  reference_scores: number[]
}

// -- /swap/preview request/response -----------------------------------------

export interface CoStarDelta {
  /** The other currently-cast actor this delta is relative to. */
  name: string
  /** Change in this pair's edge weight if the swap were made -- positive means more chemistry with this co-star. */
  delta: number
}

export interface SwapPreview {
  /** The alternate candidate this preview is for. */
  candidate: CastingCandidate
  /** This cluster's chemistry_score if this candidate were swapped in, minus its current chemistry_score. */
  delta: number
  /** Pairwise chemistry change per other currently-cast actor with real shared history -- the "why" behind delta. */
  per_costar: CoStarDelta[]
  /** True when this candidate has zero direct shared-credit evidence -- delta is then a rough 2-hop estimate, not real evidence; label it differently. */
  estimated: boolean
  /** Soft warning (not a filter): true when this alternate already leads one of this report's other clusters. */
  used_in_other_cluster: boolean
}

export interface SwapPreviewRequest {
  roster: Roster
  /** The cluster's current selections (one per character) to preview alternatives against. */
  selections: CastingSelection[]
  character_name: string
  /** Lead actors already used in this report's other clusters -- flags (never filters) alternates when character_name is itself a lead role. */
  excluded_leads: string[]
}

export interface SwapPreviewResponse {
  /** One entry per other candidate in the character's shortlist, ranked by delta descending. */
  previews: SwapPreview[]
}

// -- /recommend/stream progress events ---------------------------------------

export type RecommendStreamEvent =
  | { type: "casting_progress"; character: string; completed: number; total: number }
  | { type: "recommend_complete"; report: RecommendationReport }
  | { type: "error"; message: string }
