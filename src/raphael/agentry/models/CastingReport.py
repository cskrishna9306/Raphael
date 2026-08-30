# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field

# Import custom packages
from src.raphael.agentry.models import CastingCharacter

class CastingReport(BaseModel):
    """
    Models the full casting breakdown for a screenplay: every character
    paired with the candidate actors found for that role.
    """
    title: Optional[str] = Field(default=None, description="The title of the movie/screenplay being cast.")
    castings: list[CastingCharacter] = Field(default_factory=list, description="Casting candidates found for each character.")
