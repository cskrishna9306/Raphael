# Import standard packages
import operator
from enum import Enum
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.casting_director.models import CastingCandidate, CastingReport


class RiskLevel(Enum):
    """Discrete risk classification for a candidate's overall risk assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskFlag(BaseModel):
    """A single, specific reputational/legal/controversy signal found during risk research."""
    category: str = Field(description="Short category label, e.g. 'legal', 'scandal', 'public_statements', 'social_media'.")
    description: str = Field(description="Specific, citable description of the flagged issue.")
    source: Optional[str] = Field(default=None, description="Where this was reported/found, if the search findings surfaced one.")


class RiskAssessment(BaseModel):
    """
    Risk assessment for a single actor -- intrinsic to the actor, independent
    of any specific cast combo they might land in (this is why
    RiskManagementAgent runs over CastingReport, not ChemistryReport -- see
    module README).
    """
    name: str = Field(description="The candidate actor's full name -- matches CastingCandidate.name, the join key back to casting data.")
    risk_level: RiskLevel = Field(description="Overall risk classification.")
    rationale: str = Field(description="Brief reasoning for the assigned risk_level, grounded in what search actually turned up.")
    flags: list[RiskFlag] = Field(default_factory=list, description="Specific flagged issues supporting risk_level; empty if none were found.")


class RiskReport(BaseModel):
    """Output of RiskManagementAgent: a risk assessment for every unique candidate across a CastingReport."""
    title: Optional[str] = Field(default=None, description="Title of the source screenplay/casting report, carried through for display.")
    assessments: list[RiskAssessment] = Field(default_factory=list, description="One assessment per unique candidate actor.")


class RiskManagementState(TypedDict):
    """
    Overall state for the risk_management graph.
    """
    casting_report: CastingReport
    assessments: Annotated[list[RiskAssessment], operator.add]
    report: RiskReport


class CandidateRiskState(TypedDict):
    """
    Per-branch state: a single candidate actor to assess.
    """
    candidate: CastingCandidate
