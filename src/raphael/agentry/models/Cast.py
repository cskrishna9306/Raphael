# Import standard packages
from pydantic import BaseModel, Field

# Import custom packages
from src.raphael.agentry.models import CharacterProfile

class Cast(BaseModel):
    """
    Models the cast for the screenplay production.
    """
    characters: list[CharacterProfile] = Field(default_factory=list)

