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

export interface RecommendationReport {
  title?: string | null
  recommendations: ClusterRecommendation[]
}
