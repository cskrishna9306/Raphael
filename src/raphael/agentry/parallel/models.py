# Import standard packages
from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum

class ParallelAgentType(Enum):
    """
    Describes the different types of parallel sub-agents.
    """
    SEARCH = "search"
    EXTRACT = "extract"

class ParallelSearchRequest(BaseModel):
    """
    Models the params required for querying Parallel's Search API.
    """
    search_queries: list[str]
    objective: Optional[str]
    mode: str

class ParallelExtractRequest(BaseModel):
    """
    Models the params required for querying Parallel's Extract API.
    Think of Extract API for scraping web-pages into structured format.
    """
    # Required params
    urls: list[str]

    # Advanced options
    search_queries: Optional[list[str]]
    search_objective: Optional[str]
    excerpts: Optional[dict[Any, Any]]
    full_content: Optional[bool]
    fetch_policy: Optional[dict[Any, Any]]
