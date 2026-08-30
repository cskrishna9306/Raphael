# Import standard packages
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.parallel.models import (
    FilmographyItem,
    CollaboratorCredit,
    Recognition,
    CastingAttributes,
    Availability,
    Skills,
)


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
