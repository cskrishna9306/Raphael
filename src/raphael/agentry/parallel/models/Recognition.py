# Import standard packages
from pydantic import BaseModel, Field


class Recognition(BaseModel):
    """
    Documented, citable awards and controversies. Excludes subjective reputation summaries.
    """
    awards_and_nominations: list[str] = Field(default_factory=list, description="Specific major awards and nominations, with year and project")
    documented_controversies: list[str] = Field(default_factory=list, description="Specific, reported controversies or public disputes tied to a project or date, with source; omit if none are documented")
