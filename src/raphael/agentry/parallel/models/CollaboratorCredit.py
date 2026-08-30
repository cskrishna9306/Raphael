# Import standard packages
from pydantic import BaseModel, Field


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
