# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field


class CastingAttributes(BaseModel):
    """
    Physical and demographic attributes relevant for casting. Purely factual/reported values.
    """
    age: Optional[int] = Field(default=None, description="Approximate or actual age")
    gender: Optional[str] = Field(default=None, description="Gender identity")
    nationality: Optional[str] = Field(default=None, description="Nationality / origin")
    physical_characteristics: Optional[str] = Field(default=None, description="Reported physical build and height")
    social_media_following: Optional[str] = Field(default=None, description="Reported follower count on a major platform, with platform and approximate date")
