# Import standard packages
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

# Import the sub-modules leaf-first to avoid circular dependencies
from .FilmographyItem import FilmographyItem
from .CollaboratorCredit import CollaboratorCredit
from .Recognition import Recognition
from .CastingAttributes import CastingAttributes
from .Availability import Availability
from .Skills import Skills
from .PersonDossier import PersonDossier


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


__all__ = [
    "ParallelAgentType",
    "ParallelSearchRequest",
    "ParallelExtractRequest",
    "FilmographyItem",
    "CollaboratorCredit",
    "Recognition",
    "CastingAttributes",
    "Availability",
    "Skills",
    "PersonDossier",
]
