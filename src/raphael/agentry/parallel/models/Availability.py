# Import standard packages
from pydantic import BaseModel, Field


class Availability(BaseModel):
    """
    Scheduling information drawn from reported facts, not projections or generalizations.
    """
    current_and_upcoming_commitments: list[str] = Field(default_factory=list, description="Specific announced/reported current or upcoming projects, each with its reported timeframe")
    union_affiliation: list[str] = Field(default_factory=list, description="Union/guild memberships (e.g. SAG-AFTRA, DGA, WGA)")
