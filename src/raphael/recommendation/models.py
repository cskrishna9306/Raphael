# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.chemistry.models import CastingCluster
from src.raphael.agentry.risk_management.models import RiskAssessment


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
