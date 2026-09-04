# Import custom modules
from src.raphael.agentry.parallel.models import PersonDossier
from src.raphael.agentry.screenplay_breakdown.models import CharacterProfile, RolePresence
from src.raphael.agentry.casting_director.models import CastingReport, CastingCharacter, CastingCandidate
from src.raphael.chemistry.models import ChemistryGraph


def build_roster_report(title: str, dossiers: list[PersonDossier]) -> CastingReport:
    """
    Wrap a fixed, real roster as a CastingReport with exactly one CastingCandidate per
    "character" (the person themselves) -- lets ChemistryEngine.build_graph() score this
    roster as-is. Deliberately does not feed this into search_clusters: that step
    searches across *multiple* candidates per role to find an optimal alternative cast,
    which isn't this use case (a roster someone already picked, not one being searched for).
    """
    return CastingReport(
        title=title,
        castings=[
            CastingCharacter(
                character=CharacterProfile(name=dossier.name, role_presence=RolePresence.LEAD),
                candidates=[CastingCandidate(name=dossier.name, dossier=dossier)],
            )
            for dossier in dossiers
        ],
    )


def team_chemistry(graph: ChemistryGraph, names: list[str]) -> float:
    """
    Sum of edge weights across every pair present in `names` -- the roster's overall
    chemistry score. Deliberately not the engine's private _shaped_score: that objective
    includes a density penalty meant to discourage an all-star cast during *search*, not
    to score a roster someone actually picked.
    """
    name_set = set(names)
    return sum(
        edge.weight or 0.0
        for edge in graph.edges
        if edge.source in name_set and edge.target in name_set
    )
