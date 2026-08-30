# Import standard packages
from pydantic import BaseModel, Field

# Import custom packages
from src.raphael.agentry.models import CharacterProfile
from src.raphael.agentry.models import CastingCandidate

class CastingCharacter(BaseModel):
    """
    Models the casting candidates found for a single character.
    """
    character: CharacterProfile = Field(description="The character being cast.")
    candidates: list[CastingCandidate] = Field(default_factory=list, description="Candidate actors found for this character.")
