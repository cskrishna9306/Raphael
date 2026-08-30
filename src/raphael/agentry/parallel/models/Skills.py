# Import standard packages
from pydantic import BaseModel, Field


class Skills(BaseModel):
    """
    Reported skills relevant to casting fit. Only include what is documented, not inferred.
    """
    languages_and_accents: list[str] = Field(default_factory=list, description="Languages spoken and accents performed, per reported/documented sources")
    physical_skills: list[str] = Field(default_factory=list, description="Documented stunts, martial arts, singing, dancing, or other trained physical/performance skills")
