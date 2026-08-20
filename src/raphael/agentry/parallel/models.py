# Import standard packages
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ParallelAgentType(Enum):
    """
    Describes the different types of parallel sub-agents.
    """
    SEARCH = "search"
    EXTRACT = "extract"
    RESEARCH = "research"



class ParallelSearchRequest(BaseModel):
    """
    Models the params required for querying Parallel's Search API.
    """
    search_queries: list[str]
    objective: Optional[str] = None
    mode: str = "base"


class ParallelExtractRequest(BaseModel):
    """
    Models the params required for querying Parallel's Extract API.
    Think of Extract API for scraping web-pages into structured format.
    """
    urls: list[str]
    search_queries: Optional[list[str]] = None
    search_objective: Optional[str] = None
    excerpts: Optional[dict[Any, Any]] = None
    full_content: Optional[bool] = None
    fetch_policy: Optional[dict[Any, Any]] = None


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


class CollaboratorRelation(BaseModel):
    """
    Details of a past collaboration and the working dynamic/sentiment between two individuals.
    """
    name: str = Field(description="Name of the collaborator (actor, director, writer, cinematographer, etc.)")
    role: str = Field(description="Collaborator's primary role on shared projects")
    shared_projects: list[str] = Field(default_factory=list, description="List of movies or shows they worked on together")
    relationship_sentiment: str = Field(description="Sentiment/dynamic: e.g. 'Strong Chemistry / Frequent Partner', 'Positive', 'Neutral', 'Difficult / Conflicted'")
    chemistry_notes: Optional[str] = Field(default=None, description="Qualitative observations on their chemistry, collaboration frequency, or public comments about working together")


class PersonalityAndCritique(BaseModel):
    """
    Reputation, working style, and critical commentary.
    """
    working_style: Optional[str] = Field(default=None, description="Working style or approach (e.g. Method acting, improvisational, highly disciplined, auteur-driven)")
    critical_acclaim: list[str] = Field(default_factory=list, description="Major awards, nominations, and career milestones")
    public_reputation: Optional[str] = Field(default=None, description="General industry and public perception/reputation")
    known_critiques_or_controversies: list[str] = Field(default_factory=list, description="Known critiques, personality clashes, or artistic controversies if any")


class CastingAttributes(BaseModel):
    """
    Physical and demographic attributes relevant for casting.
    """
    age: Optional[int] = Field(default=None, description="Approximate or actual age")
    gender: Optional[str] = Field(default=None, description="Gender identity")
    nationality: Optional[str] = Field(default=None, description="Nationality / origin")
    physical_characteristics: Optional[str] = Field(default=None, description="Physical build, height, notable features")
    screen_presence_traits: list[str] = Field(default_factory=list, description="Key presence traits (e.g. 'intense', 'charismatic', 'comedic timing', 'commanding')")


class PersonDossier(BaseModel):
    """
    Structured deep research dossier on a cinema professional (Actor, Director, Writer, Crew).
    """
    name: str = Field(description="Full name of the person")
    primary_roles: list[str] = Field(default_factory=list, description="Primary roles (e.g. Actor, Director, Cinematographer)")
    bio_summary: str = Field(description="Brief biographical and career summary")
    filmography: list[FilmographyItem] = Field(default_factory=list, description="Key movie/production credits")
    collaborators: list[CollaboratorRelation] = Field(default_factory=list, description="Key collaborators and chemistry dynamics")
    personality: PersonalityAndCritique = Field(default_factory=PersonalityAndCritique, description="Reputation, working style, and critiques")
    attributes: CastingAttributes = Field(default_factory=CastingAttributes, description="Casting and physical attributes")

