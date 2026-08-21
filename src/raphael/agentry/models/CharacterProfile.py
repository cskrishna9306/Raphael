# Import standard packages
from pydantic import BaseModel, Field
from typing import Optional

# Import custom packages
from src.raphael.agentry.models import RolePresence
from src.raphael.agentry.models import Gender

class CharacterProfile(BaseModel):
    """
    Models a single character from a production.
    """

    # Meta attributes
    name: str = Field(description="The name of this character from the movie.")
    aliases: Optional[list[str]] = Field(default=None, description="Any aliases that this character may have been referenced in this production.")
    role_presence: RolePresence

    # Character profile
    gender: Gender = Gender.UNSPECIFIED
    age_range: Optional[str] = Field(default=None, description="The character's age or age range, as specified in the screenplay otherwise inferred.")
    description: Optional[str] = Field(default=None, description="A short description of the part played by the character in this production.")
    traits: Optional[list[str]] = Field(default=None, description="A list of short 1-3 word personality, physical, and mental traits of this character.")

