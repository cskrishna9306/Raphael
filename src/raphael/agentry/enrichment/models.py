# Import standard packages
import operator
from enum import Enum
from typing import Annotated, Optional, TypedDict
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.casting_director.models import CastingCandidate, CastingCharacter, CastingReport
from src.raphael.agentry.parallel.models import PersonDossier


class EnrichmentSource(Enum):
    """Where an EnrichmentAssessment's dossier came from."""
    CACHE = "cache"
    RESEARCH = "research"
    FAILED = "failed"


class EnrichmentAssessment(BaseModel):
    """
    Enrichment result for a single actor -- their full research dossier,
    either reconstructed from ClickHouse or freshly researched via Parallel,
    plus which of those paths produced it.
    """
    name: str = Field(description="The candidate actor's full name -- matches CastingCandidate.name, the join key back to casting data.")
    dossier: Optional[PersonDossier] = Field(default=None, description="Full research dossier for this candidate; None only if source is FAILED.")
    source: EnrichmentSource = Field(description="Whether the dossier was served from ClickHouse, freshly researched, or unavailable.")


class EnrichmentReport(BaseModel):
    """Output of EnrichmentAgent: an enrichment dossier for every unique candidate across a CastingReport."""
    title: Optional[str] = Field(default=None, description="Title of the source screenplay/casting report, carried through for display.")
    assessments: list[EnrichmentAssessment] = Field(default_factory=list, description="One dossier-bearing assessment per unique candidate actor.")

    def merge_dossiers(self, casting_report: CastingReport) -> CastingReport:
        """
        Returns a new CastingReport with each candidate's dossier upgraded to
        this EnrichmentReport's version, by name, where one is available.
        Candidates with no matching assessment, or whose assessment's
        dossier is None (source == FAILED), keep their original (shallow,
        search-prefilled) dossier unchanged.

        Intended use: run EnrichmentAgent + RiskManagementAgent concurrently
        over a draft CastingReport, merge the enriched dossiers back in via
        this method, then run ChemistryEngine over the result -- so chemistry
        scoring sees full filmography/collaborators data instead of whatever
        CastingDirectorAgent's shallow search pass happened to surface.
        """
        dossiers_by_name = {
            assessment.name: assessment.dossier
            for assessment in self.assessments
            if assessment.dossier is not None
        }
        return CastingReport(
            title=casting_report.title,
            castings=[
                CastingCharacter(
                    character=casting.character,
                    candidates=[
                        candidate.model_copy(update={"dossier": dossiers_by_name[candidate.name]})
                        if candidate.name in dossiers_by_name
                        else candidate
                        for candidate in casting.candidates
                    ],
                )
                for casting in casting_report.castings
            ],
        )


class EnrichmentState(TypedDict):
    """
    Overall state for the enrichment graph.
    """
    casting_report: CastingReport
    assessments: Annotated[list[EnrichmentAssessment], operator.add]
    report: EnrichmentReport


class CandidateEnrichmentState(TypedDict):
    """
    Per-branch state: a single candidate actor to enrich.
    """
    candidate: CastingCandidate
