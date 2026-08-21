# Import standard packages
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.models import Cast

class Screenplay(BaseModel):
    """
    Models the entire screenplay.
    """
    title: str = Field(description="The title of the movie/screenplay.")
    cast: Cast = Field(default_factory=Cast)
