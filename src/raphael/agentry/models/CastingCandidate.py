# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field

# Import custom packages
from src.raphael.agentry.parallel.models import PersonDossier

class CastingCandidate(BaseModel):
    """
    Models a single actor considered for a character role.
    """
    name: str = Field(description="The candidate actor's full name.")
    fit_rationale: Optional[str] = Field(default=None, description="Brief reasoning for why this actor could play the role.")
    dossier: Optional[PersonDossier] = Field(default=None, description="Structured research dossier on this candidate, once researched.")
