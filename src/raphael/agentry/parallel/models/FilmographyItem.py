# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field


class FilmographyItem(BaseModel):
    """
    Credit / project in a person's filmography.
    """
    title: str = Field(description="Title of the movie or television production")
    year: Optional[int] = Field(default=None, description="Release year of the production")
    role: str = Field(description="Role in the production (e.g. Lead Actor, Director, Screenwriter, DP)")
    character_or_contribution: Optional[str] = Field(default=None, description="Character name or specific key contribution")
    box_office: Optional[str] = Field(default=None, description="Box office figures or commercial performance")
    critical_reception: Optional[str] = Field(default=None, description="Critical reception summary or ratings (e.g. Rotten Tomatoes, Metacritic)")
    key_collaborators: list[str] = Field(default_factory=list, description="Notable co-stars, directors, or producers on this project")
