# Import standard packages
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.parallel.models import PersonDossier
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.recommendation.models import RecommendationReport


class ProjectSummary(BaseModel):
    """One row of a user's history list: enough to render the list without reading any report."""
    id: str = Field(description="Firestore document id of the project, used as the path segment on /projects/{id}.")
    title: str = Field(description="Screenplay title, copied onto the project doc so listing never has to open the screenplay.")
    character_count: int = Field(description="Number of characters in the stored breakdown, shown as a subtitle in the history list.")
    has_report: bool = Field(description="Whether a RecommendationReport has been saved against this project yet.")
    created_at: Optional[datetime] = Field(default=None, description="When the project was created. None only in the window before the server timestamp resolves.")
    updated_at: Optional[datetime] = Field(default=None, description="When the project or its latest report last changed; the field the history list is ordered by.")


class Project(BaseModel):
    """A saved screenplay plus its most recent recommendation report."""
    id: str = Field(description="Firestore document id of the project.")
    title: str = Field(description="Screenplay title, carried through for display.")
    screenplay: Screenplay = Field(description="The stored breakdown, including any role/preferred_actor edits made before /recommend.")
    latest_report: Optional[RecommendationReport] = Field(
        default=None,
        description=(
            "Most recent report saved against this project, with every candidate's dossier "
            "rehydrated (see history.serialization). None until /recommend runs for it."
        ),
    )
    created_at: Optional[datetime] = Field(default=None, description="When the project was created.")
    updated_at: Optional[datetime] = Field(default=None, description="When the project or its latest report last changed.")


class DossierEntry(BaseModel):
    """One candidate's PersonDossier, lifted out of the report so it is stored exactly once."""
    candidate_name: str = Field(
        description=(
            "The CastingCandidate.name this dossier was attached to -- the join key used to put it "
            "back. Deliberately not PersonDossier.name, which can be a differently-formatted variant "
            "of the same person (see ClickHouseHandler._resolve_canonical_name)."
        ),
    )
    dossier: PersonDossier = Field(description="The dossier itself, carried through unchanged.")


class PackedReport(BaseModel):
    """
    Storage form of a RecommendationReport: the report with every
    candidate.dossier stripped, plus one copy of each distinct dossier.
    """

    # The same actor is selected across several clusters, so the report as
    # returned by the pipeline embeds the same multi-KB dossier many times over
    # -- enough to push a large screenplay's report past Firestore's 1 MiB
    # per-document ceiling. Splitting them out is what keeps it under.
    report: RecommendationReport = Field(description="The report with every candidate's dossier set to None.")
    dossiers: list[DossierEntry] = Field(
        default_factory=list,
        # A list rather than a name-keyed map because actor names routinely
        # contain characters Firestore treats specially in field paths
        # (e.g. the '.' in "Samuel L. Jackson").
        description="One entry per distinct candidate name that had a dossier.",
    )
