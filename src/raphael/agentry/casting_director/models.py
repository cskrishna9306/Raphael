# Import standard packages
import operator
from typing import Annotated, TypedDict
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.models import (
    Screenplay,
    CharacterProfile,
    CastingCandidate,
    CastingCharacter,
    CastingReport,
)

class CandidateSearchResult(BaseModel):
    """
    Internal structured-output shape used to parse a character's raw search
    findings into casting candidates. Not a shared domain model.
    """
    candidates: list[CastingCandidate] = Field(default_factory=list)

class CastingDirectorState(TypedDict):
    """
    Overall state for the casting_director graph.
    """
    screenplay: Screenplay
    castings: Annotated[list[CastingCharacter], operator.add]
    report: CastingReport

class CharacterSearchState(TypedDict):
    """
    Per-branch state: a single character to find candidates for.
    """
    character: CharacterProfile
