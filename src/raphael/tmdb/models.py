# Import standard packages
from typing import Optional
from pydantic import BaseModel, Field


class MovieSearchResult(BaseModel):
    """
    A single hit from TMDB's /search/movie endpoint.
    """
    id: int = Field(description="TMDB movie id")
    title: str = Field(description="Movie title")


class PersonSearchResult(BaseModel):
    """
    A single hit from TMDB's /search/person endpoint.
    """
    id: int = Field(description="TMDB person id")
    name: str = Field(description="Person's name")
    profile_path: Optional[str] = Field(default=None, description="Relative path to the person's profile image, if TMDB has one on file")


class CastMember(BaseModel):
    """
    One cast member on a movie's credits.
    """
    id: int = Field(description="TMDB person id")
    name: str = Field(description="Actor's name")
    character: Optional[str] = Field(default=None, description="Character name portrayed")
    order: Optional[int] = Field(default=None, description="Billing order")


class CrewMember(BaseModel):
    """
    One crew member on a movie's credits.
    """
    id: int = Field(description="TMDB person id")
    name: str = Field(description="Crew member's name")
    job: Optional[str] = Field(default=None, description="Specific role, e.g. Director, Producer")
    department: Optional[str] = Field(default=None, description="Department, e.g. Directing, Production")


class MovieCredits(BaseModel):
    """
    Full cast/crew credits for one movie, as returned by /movie/{id}/credits.
    """
    cast: list[CastMember] = Field(default_factory=list)
    crew: list[CrewMember] = Field(default_factory=list)


class PersonMovieCredit(BaseModel):
    """
    One movie credit from a person's /person/{id}/movie_credits -- cast side only,
    since actor-graph traversal only walks other actors' filmographies, not crew.
    """
    id: int = Field(description="TMDB movie id")
    title: str = Field(description="Movie title")
    character: Optional[str] = Field(default=None, description="Character name portrayed")
    popularity: Optional[float] = Field(default=None, description="TMDB popularity score, used to rank which movies to expand traversal through")


class PersonMovieCredits(BaseModel):
    """
    A person's cast-side movie credits, as returned by /person/{id}/movie_credits.
    The crew list from that same endpoint is intentionally not modeled here.
    """
    cast: list[PersonMovieCredit] = Field(default_factory=list)
