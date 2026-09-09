# Import standard packages
import math
from typing import Optional

# Import custom modules
from src.raphael.agentry.parallel.models import PersonDossier, FilmographyItem
from src.raphael.chemistry.models import ProductionCredit


def normalize_name(name: str) -> str:
    """Lowercases and strips a name for matching across dossiers."""
    return name.strip().lower()


def lookup_cast_size(title: str) -> Optional[int]:
    """Looks up a past production's true credited cast size. Not wired up yet -- the single seam a future ClickHouse-backed lookup plugs into; None means "unknown", not zero."""
    return None


def _known_titles(dossier: PersonDossier) -> dict[str, FilmographyItem]:
    """Maps normalized title -> FilmographyItem for everything in a dossier's filmography."""
    return {normalize_name(item.title): item for item in dossier.filmography}


def shared_production_credits(a: Optional[PersonDossier], b: Optional[PersonDossier]) -> list[ProductionCredit]:
    """Reconstructs the productions two actors share, cross-referencing both dossiers' filmography and collaborator lists since either can be incomplete on its own."""
    if not a or not b:
        return []

    a_titles, b_titles = _known_titles(a), _known_titles(b)
    a_name, b_name = normalize_name(a.name), normalize_name(b.name)

    # Either side's collaborator list can name a shared project the other's filmography omits,
    # and vice versa for key_collaborators on a specific filmography entry -- union all four.
    shared_titles: set[str] = set()
    shared_titles.update(normalize_name(t) for c in a.collaborators if normalize_name(c.name) == b_name for t in c.shared_projects)
    shared_titles.update(normalize_name(t) for c in b.collaborators if normalize_name(c.name) == a_name for t in c.shared_projects)
    shared_titles.update(title for title, item in a_titles.items() if b_name in {normalize_name(n) for n in item.key_collaborators})
    shared_titles.update(title for title, item in b_titles.items() if a_name in {normalize_name(n) for n in item.key_collaborators})

    credits = []
    for title in shared_titles:
        item = a_titles.get(title) or b_titles.get(title)
        display_title = item.title if item else title
        credits.append(ProductionCredit(title=display_title, year=item.year if item else None, cast_size=lookup_cast_size(display_title)))
    return credits


def npmi(joint: int, marginal_a: int, marginal_b: int, corpus_size: int) -> Optional[float]:
    """Normalized PMI for a pair's co-occurrence against an approximated corpus size. Bounded [-1, 1]; None when it can't be computed."""
    if joint <= 0 or corpus_size <= 0 or marginal_a <= 0 or marginal_b <= 0:
        return None

    p_a, p_b, p_ab = marginal_a / corpus_size, marginal_b / corpus_size, joint / corpus_size
    if p_ab >= 1:
        return 1.0  # degenerate case: this pair IS the entire known corpus
    return math.log(p_ab / (p_a * p_b)) / -math.log(p_ab)


def adamic_adar(credits: list[ProductionCredit]) -> Optional[float]:
    """Sum of 1/log(cast_size) over credits with a known cast_size -- rewards small-cast collaborations over ensemble co-appearances. None until cast_size is populated (see lookup_cast_size)."""
    scored = [c.cast_size for c in credits if c.cast_size and c.cast_size >= 2]
    if not scored:
        return None
    return sum(1 / math.log(size) for size in scored)


def _known_collaborator_names(dossier: PersonDossier) -> set[str]:
    """All names a dossier documents this person as connected to -- their own collaborators list plus every filmography entry's key_collaborators. Used only as a weak 2-hop backoff signal (see shared_collaborator_count), never treated as observed shared history itself."""
    names = {normalize_name(c.name) for c in dossier.collaborators}
    names.update(normalize_name(n) for item in dossier.filmography for n in item.key_collaborators)
    return names


def shared_collaborator_count(a: Optional[PersonDossier], b: Optional[PersonDossier]) -> int:
    """
    Count of people both dossiers separately name as a collaborator/co-star
    -- a "friends of friends" backoff signal for pairs with no direct shared
    credit (see shared_production_credits). Used only to break ties among
    otherwise-indistinguishable zero-evidence candidates in
    ChemistryEngine.preview_swaps -- deliberately never folded into
    shared_production_credits/ChemistryEdge itself, since it isn't observed
    history.
    """
    if not a or not b:
        return 0
    return len(_known_collaborator_names(a) & _known_collaborator_names(b))
