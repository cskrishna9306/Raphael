# Import standard packages
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Gender(Enum):
    """
    Describes a character's gender as portrayed in the screenplay.
    """
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    UNSPECIFIED = "unspecified"


class RolePresence(Enum):
    """
    Describes how central a character is to the screenplay.
    """
    LEAD = "lead"
    SUPPORTING = "supporting"
    MINOR = "minor"
    BACKGROUND = "background"
    EXTRA = "extra"


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


class Cast(BaseModel):
    """
    Models the cast for the screenplay production.
    """
    characters: list[CharacterProfile] = Field(default_factory=list)


class Screenplay(BaseModel):
    """
    Models the entire screenplay.
    """
    title: str = Field(description="The title of the movie/screenplay.")
    cast: Cast = Field(default_factory=Cast)
