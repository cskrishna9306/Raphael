# Import standard packages
from typing import Callable

# Import custom modules
from src.raphael.agentry.casting_director.models import CastingCandidate
from src.raphael.agentry.parallel.models import PersonDossier
from src.raphael.history.models import DossierEntry, PackedReport
from src.raphael.recommendation.models import RecommendationReport


def _map_candidates(
    report: RecommendationReport,
    transform: Callable[[CastingCandidate], CastingCandidate],
) -> RecommendationReport:
    """
    Rebuilds a RecommendationReport with `transform` applied to every
    candidate. Copies at every level, so the caller's report is never mutated.
    """
    return report.model_copy(
        update={
            "recommendations": [
                recommendation.model_copy(
                    update={
                        "cluster": recommendation.cluster.model_copy(
                            update={
                                "selections": [
                                    selection.model_copy(update={"candidate": transform(selection.candidate)})
                                    for selection in recommendation.cluster.selections
                                ],
                            },
                        ),
                    },
                )
                for recommendation in report.recommendations
            ],
        },
    )


def pack_report(report: RecommendationReport) -> PackedReport:
    """
    Splits a report into a dossier-free report plus one copy of each distinct
    candidate's dossier, so a document stores each dossier once instead of
    once per cluster the actor appears in (see PackedReport).
    """
    dossiers: dict[str, PersonDossier] = {}
    for recommendation in report.recommendations:
        for selection in recommendation.cluster.selections:
            candidate = selection.candidate
            # First-seen wins, same convention as CastingReport.unique_candidates().
            if candidate.dossier is not None:
                dossiers.setdefault(candidate.name, candidate.dossier)

    return PackedReport(
        report=_map_candidates(report, lambda candidate: candidate.model_copy(update={"dossier": None})),
        dossiers=[
            DossierEntry(candidate_name=name, dossier=dossier)
            for name, dossier in dossiers.items()
        ],
    )


def unpack_report(packed: PackedReport) -> RecommendationReport:
    """
    Inverse of pack_report: puts each stored dossier back on every candidate
    that carries its name. A candidate with no stored dossier keeps None,
    which is exactly what it had going in.
    """
    dossiers_by_name = {entry.candidate_name: entry.dossier for entry in packed.dossiers}
    return _map_candidates(
        packed.report,
        lambda candidate: (
            candidate.model_copy(update={"dossier": dossiers_by_name[candidate.name]})
            if candidate.name in dossiers_by_name
            else candidate
        ),
    )
