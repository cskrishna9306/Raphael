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
    Rebuilds a RecommendationReport with `transform` applied to every candidate,
    in the ranked clusters AND in roster.casting_report. Copies at every level,
    so the caller's report is never mutated.
    """

    # The roster carries every character's whole shortlist with dossiers merged
    # in -- a superset of what the clusters picked, and by far the larger half
    # of the document. Packing only the clusters would leave most of the weight
    # behind and push a real report past Firestore's per-document ceiling.
    roster = report.roster
    packed_roster = roster.model_copy(
        update={
            "casting_report": roster.casting_report.model_copy(
                update={
                    "castings": [
                        casting.model_copy(
                            update={"candidates": [transform(candidate) for candidate in casting.candidates]},
                        )
                        for casting in roster.casting_report.castings
                    ],
                },
            ),
        },
    )

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
            "roster": packed_roster,
        },
    )


def pack_report(report: RecommendationReport) -> PackedReport:
    """
    Splits a report into a dossier-free report plus one copy of each distinct
    candidate's dossier, so a document stores each dossier once instead of
    once per cluster the actor appears in (see PackedReport).
    """
    dossiers: dict[str, PersonDossier] = {}

    def collect(candidate: CastingCandidate) -> None:
        # First-seen wins, same convention as CastingReport.unique_candidates().
        if candidate.dossier is not None:
            dossiers.setdefault(candidate.name, candidate.dossier)

    for recommendation in report.recommendations:
        for selection in recommendation.cluster.selections:
            collect(selection.candidate)
    # The same actor appears in the roster's shortlist and in any cluster that
    # picked them, so both sides share one dossier table.
    for casting in report.roster.casting_report.castings:
        for candidate in casting.candidates:
            collect(candidate)

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
