# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.chemistry.models import CastingCluster, CastingSelection, SwapPreview
from src.raphael.agentry.risk_management.models import RiskAssessment
from src.raphael.roster.models import Roster


class ClusterRecommendation(BaseModel):
    """One ranked cast alternative (from ChemistryReport.clusters) plus its risk-aware summary layer."""
    cluster: CastingCluster = Field(description="The underlying chemistry-scored cast alternative, carried through unchanged.")
    top_risks: list[RiskAssessment] = Field(
        default_factory=list,
        description=(
            "This cluster's actors' RiskAssessments, walked high -> medium -> low and "
            "accumulated a whole severity band at a time (never split mid-band), stopping "
            "once the running total reaches >= 3. A floor, not a hard cap -- e.g. 5 high-risk "
            "actors all appear rather than arbitrarily dropping 2. Empty if none of this "
            "cluster's actors have a matching RiskReport assessment."
        ),
    )


class RecommendationReport(BaseModel):
    """Output of the recommendation engine: ChemistryReport's ranked clusters, each annotated with its actors' top risks."""
    title: Optional[str] = Field(default=None, description="Title of the source screenplay/casting report, carried through for display.")
    # recommendations[0] is the best cluster -- index position is the rank, no separate rank field,
    # same convention as ChemistryReport.clusters.
    recommendations: list[ClusterRecommendation] = Field(
        default_factory=list,
        description="One entry per ChemistryReport cluster, same order (rank) as ChemistryReport.clusters.",
    )
    roster: Roster = Field(
        description=(
            "The full candidate pool every recommendation was picked from -- every "
            "character's whole shortlist (dossiers included) plus every candidate's risk "
            "assessment. Lets the frontend offer substitutes per character; see /swap."
        )
    )


class SwapRequest(BaseModel):
    """
    Request body for POST /swap: recompute chemistry/risk for one cluster
    with a single character's candidate substituted, without re-running the
    search or any agents. Deliberately stateless -- roster is round-tripped
    from an earlier RecommendationReport rather than cached server-side.
    """
    roster: Roster = Field(description="The Roster from a prior RecommendationReport -- supplies every candidate's dossier/risk for graph rebuilding.")
    selections: list[CastingSelection] = Field(description="The full cluster's selections (one candidate per character) with the swap already applied.")
    reference_scores: list[float] = Field(description="chemistry_score of the prior RecommendationReport's recommendations, used to bucket this ad-hoc score into the same high/medium/low bands.")


class SwapPreviewRequest(BaseModel):
    """Request body for POST /swap/preview: score every other candidate for one character as a hypothetical swap, without committing to any of them."""
    roster: Roster = Field(description="The Roster from a prior RecommendationReport -- supplies every candidate's dossier for graph rebuilding.")
    selections: list[CastingSelection] = Field(description="The cluster's current selections (one candidate per character) to preview alternatives against.")
    character_name: str = Field(description="Which character's shortlist to preview alternatives for.")
    used_elsewhere: list[str] = Field(
        default_factory=list,
        description=(
            "Actors already cast in this report's OTHER clusters, across every role -- flagged "
            "(not dropped) on the alternates offered here via SwapPreview.used_in_other_cluster. "
            "Mirrors search_clusters' 'no actor appears in more than one cluster' rule so the "
            "picker can warn about, without blocking, a swap that would reintroduce a duplicate."
        ),
    )


class SwapPreviewResponse(BaseModel):
    previews: list[SwapPreview] = Field(
        default_factory=list,
        description="One entry per other candidate in the character's shortlist, ranked by delta descending -- best chemistry improvement first.",
    )
