# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field


class MovieSearchResult(BaseModel):
    """
    A single hit from TMDB's /search/movie endpoint.
    """
    id: int = Field(description="TMDB movie id")
    title: str = Field(description="Movie title")


class CastMember(BaseModel):
    """
    One cast member on a movie's credits.
    """
    name: str = Field(description="Actor's name")
    character: Optional[str] = Field(default=None, description="Character name portrayed")
    order: Optional[int] = Field(default=None, description="Billing order")
    profile_path: Optional[str] = Field(default=None, description="Path fragment for a headshot image, relative to TMDB's image CDN")


class CrewMember(BaseModel):
    """
    One crew member on a movie's credits.
    """
    name: str = Field(description="Crew member's name")
    job: Optional[str] = Field(default=None, description="Specific role, e.g. Director, Producer")
    department: Optional[str] = Field(default=None, description="Department, e.g. Directing, Production")


class MovieCredits(BaseModel):
    """
    Full cast/crew credits for one movie, as returned by /movie/{id}/credits.
    """
    cast: list[CastMember] = Field(default_factory=list)
    crew: list[CrewMember] = Field(default_factory=list)
