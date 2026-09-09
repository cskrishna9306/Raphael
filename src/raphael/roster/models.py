# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.risk_management.models import RiskAssessment


class Roster(BaseModel):
    """
    Every character's full candidate shortlist (dossier-enriched), plus every
    unique candidate's risk assessment -- the superset RecommendationReport's
    ranked clusters are picked from.

    EnrichmentAgent/RiskManagementAgent already fan out over
    CastingReport.unique_candidates() -- every candidate shortlisted for
    every character, not just the ones a cluster happened to pick -- so this
    is data /recommend's pipeline already computes; Roster just stops it
    from being discarded once the top clusters are chosen, so the frontend
    can offer substitutes for any character.
    """
    title: Optional[str] = Field(default=None, description="Title of the source screenplay/casting report, carried through for display.")
    casting_report: CastingReport = Field(description="Full per-character candidate shortlist, each candidate's dossier already merged in.")
    risk_assessments: list[RiskAssessment] = Field(default_factory=list, description="One assessment per unique candidate actor across the whole report -- not just each cluster's top 3.")
