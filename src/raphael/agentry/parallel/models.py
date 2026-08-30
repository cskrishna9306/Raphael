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


class CollaboratorCredit(BaseModel):
    """
    A verifiable record of having worked with another industry professional.

    Deliberately factual: which projects, not a sentiment/chemistry judgment about the
    relationship. Judgments like that are computed downstream from these facts, not asked
    of the research call (see Raphael's own chemistry-scoring step).
    """
    name: str = Field(description="Name of the collaborator (actor, director, writer, cinematographer, etc.)")
    role: str = Field(description="Collaborator's primary role on shared projects")
    shared_projects: list[str] = Field(default_factory=list, description="List of movies or shows they worked on together")
    public_statements_about_collaboration: list[str] = Field(default_factory=list, description="Direct, citable quotes or reported statements (by either person, press, or reviewers) specifically about working together, if any exist")


class Recognition(BaseModel):
    """
    Documented, citable awards and controversies. Excludes subjective reputation summaries.
    """
    awards_and_nominations: list[str] = Field(default_factory=list, description="Specific major awards and nominations, with year and project")
    documented_controversies: list[str] = Field(default_factory=list, description="Specific, reported controversies or public disputes tied to a project or date, with source; omit if none are documented")


class CastingAttributes(BaseModel):
    """
    Physical and demographic attributes relevant for casting. Purely factual/reported values.
    """
    age: Optional[int] = Field(default=None, description="Approximate or actual age")
    gender: Optional[str] = Field(default=None, description="Gender identity")
    nationality: Optional[str] = Field(default=None, description="Nationality / origin")
    physical_characteristics: Optional[str] = Field(default=None, description="Reported physical build and height")
    social_media_following: Optional[str] = Field(default=None, description="Reported follower count on a major platform, with platform and approximate date")


class Availability(BaseModel):
    """
    Scheduling information drawn from reported facts, not projections or generalizations.
    """
    current_and_upcoming_commitments: list[str] = Field(default_factory=list, description="Specific announced/reported current or upcoming projects, each with its reported timeframe")
    union_affiliation: list[str] = Field(default_factory=list, description="Union/guild memberships (e.g. SAG-AFTRA, DGA, WGA)")


class Skills(BaseModel):
    """
    Reported skills relevant to casting fit. Only include what is documented, not inferred.
    """
    languages_and_accents: list[str] = Field(default_factory=list, description="Languages spoken and accents performed, per reported/documented sources")
    physical_skills: list[str] = Field(default_factory=list, description="Documented stunts, martial arts, singing, dancing, or other trained physical/performance skills")


class PersonDossier(BaseModel):
    """
    Structured research dossier of verifiable, citable facts about a cinema professional (Actor, Director, Writer, Crew).

    Deliberately excludes synthesized judgments (chemistry scores, sentiment, working-style characterizations) -- those are computed by Raphael from these facts in a separate downstream step, not requested from the research call itself.
    """
    name: str = Field(description="Full name of the person")
    primary_roles: list[str] = Field(default_factory=list, description="Primary roles (e.g. Actor, Director, Cinematographer)")
    bio_summary: str = Field(description="Brief biographical and career summary")
    filmography: list[FilmographyItem] = Field(default_factory=list, description="Key movie/production credits")
    collaborators: list[CollaboratorCredit] = Field(default_factory=list, description="Key collaborators and the specific projects shared with them")
    recognition: Recognition = Field(default_factory=Recognition, description="Documented awards and controversies")
    attributes: CastingAttributes = Field(default_factory=CastingAttributes, description="Casting and physical attributes")
    availability: Availability = Field(default_factory=Availability, description="Scheduling and commitment information")
    skills: Skills = Field(default_factory=Skills, description="Documented skills relevant to casting fit")
