# Import standard packages
import operator
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.screenplay_breakdown.models import Screenplay, CharacterProfile
from src.raphael.agentry.parallel.models import PersonDossier


class CastingCandidate(BaseModel):
    """
    Models a single actor considered for a character role.
    """
    name: str = Field(description="The candidate actor's full name.")
    fit_rationale: Optional[str] = Field(default=None, description="Brief reasoning for why this actor could play the role.")
    dossier: Optional[PersonDossier] = Field(default=None, description="Structured research dossier on this candidate, once researched.")


class CastingCharacter(BaseModel):
    """
    Models the casting candidates found for a single character.
    """
    character: CharacterProfile = Field(description="The character being cast.")
    candidates: list[CastingCandidate] = Field(default_factory=list, description="Candidate actors found for this character.")


class CastingReport(BaseModel):
    """
    Models the full casting breakdown for a screenplay: every character
    paired with the candidate actors found for that role.
    """
    title: Optional[str] = Field(default=None, description="The title of the movie/screenplay being cast.")
    castings: list[CastingCharacter] = Field(default_factory=list, description="Casting candidates found for each character.")

    def unique_candidates(self) -> dict[str, "CastingCandidate"]:
        """
        First-seen dedup of candidates across every character -- the same
        actor can be shortlisted for more than one role. Shared by
        ChemistryEngine (graph nodes) and RiskManagementAgent (fan-out) so
        both walk the same unique-candidate set the same way.
        """
        seen: dict[str, CastingCandidate] = {}
        for casting in self.castings:
            for candidate in casting.candidates:
                seen.setdefault(candidate.name, candidate)
        return seen


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
