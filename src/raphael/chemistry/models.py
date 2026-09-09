# Import standard packages
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

# Import custom modules
from src.raphael.agentry.casting_director.models import CastingCandidate
from src.raphael.agentry.screenplay_breakdown.models import CharacterProfile
from src.raphael.agentry.risk_management.models import RiskLevel


class ProductionCredit(BaseModel):
    """
    A single production two or more actors are both credited on -- the
    hyperedge in the underlying actor-film bipartite graph. Kept as one unit
    of evidence rather than pre-collapsed into a pair, so cast size and year
    are still available for Adamic-Adar normalization and temporal decay
    downstream.
    """
    title: str = Field(description="Title of the shared production.")
    year: Optional[int] = Field(default=None, description="Release year, used for temporal decay -- a 1997 collaboration counts for less than a 2024 one.")
    cast_size: Optional[int] = Field(default=None, description="Total credited cast size on this production. Used to down-weight ensemble films relative to two-handers (Adamic-Adar); unknown cast size just drops that credit from the Adamic-Adar sum, not the edge.")


class ChemistryNode(BaseModel):
    """
    A single actor as a node in the collaboration graph. Carries the two
    per-actor (not pairwise) signals that also factor into chemistry_score
    now -- role fit and risk -- alongside the graph-native total_credits, so
    a node is a complete record of everything about this actor the scoring
    objective considers outside of pairwise edges.
    """
    name: str = Field(description="The actor's full name; used as the node's identity/key.")
    total_credits: Optional[int] = Field(default=None, description="The actor's total known filmography size -- the marginal count NPMI normalizes co-occurrence against. Not the same as len(shared_credits) on any one edge.")
    role_fit: Optional[float] = Field(default=None, description="CastingCandidate.fit_score for this actor in this specific role -- how well their real-world type/persona matches the character, 0-1. None if never judged (e.g. a director-specified preferred_actor).")
    risk_level: Optional[RiskLevel] = Field(default=None, description="This actor's RiskAssessment.risk_level, if a RiskReport was supplied to build_graph. None if risk wasn't assessed (or not supplied) for this actor.")


class AffinityMethod(Enum):
    """
    Link-prediction methods usable as a sparsity backoff for actor pairs with
    no observed shared history. See PredictedAffinity for why this stays a
    separate model from ChemistryEdge.
    """
    KATZ = "katz"
    SIMRANK = "simrank"
    NODE2VEC = "node2vec"
    # Common-neighbors count over each dossier's own documented collaborators/key_collaborators
    # -- "do X and Y separately name someone in common, even though they've never worked
    # together" -- the one of these four actually wired up (see ChemistryEngine.build_graph);
    # the other three remain unimplemented placeholders for a future, richer backoff.
    SHARED_COLLABORATORS = "shared_collaborators"


class ChemistryEdge(BaseModel):
    """
    Observed pairwise relationship between two actors, grounded in real
    shared credits.

    A pair with zero shared history simply has no ChemistryEdge in
    ChemistryGraph.edges -- that absence IS the "no shared history" band.
    Never backfill a missing edge with a PredictedAffinity score to make a
    pair look like it has one; that's a modeled guess, not evidence, and the
    two must stay visibly distinct (see PredictedAffinity).
    """
    source: str = Field(description="Name of one actor in the pair. Order is arbitrary, not directional.")
    target: str = Field(description="Name of the other actor in the pair.")
    shared_credits: list[ProductionCredit] = Field(default_factory=list, description="Productions both actors are credited on together. Non-empty by construction -- an edge only exists because this list is non-empty.")
    npmi: Optional[float] = Field(default=None, description="Normalized PMI of the pair's co-occurrence, corrected for how prolific each actor is individually. Bounded [-1, 1].")
    adamic_adar: Optional[float] = Field(default=None, description="Sum of 1/log(cast_size) over shared_credits with a known cast_size -- rewards small-cast collaborations over ensemble co-appearances.")
    weight: Optional[float] = Field(default=None, description="Final combined edge weight (NPMI + Adamic-Adar, temporal decay applied) used by the team-search objective. None until scored.")


class PredictedAffinity(BaseModel):
    """
    Backoff signal for a pair with no observed shared history, produced by a
    link-prediction method over the collaboration graph (e.g. shared
    neighbors at distance 2+). Deliberately its own model rather than a
    field on ChemistryEdge or a fallback value for `weight`: this is a guess
    used only to keep the team-search optimizer from getting stuck on flat
    zero-regions, never evidence, and must never be surfaced to a user as if
    it were an observed score.
    """
    source: str = Field(description="Name of one actor in the pair.")
    target: str = Field(description="Name of the other actor in the pair.")
    method: AffinityMethod = Field(description="Link-prediction method used to produce this score.")
    score: float = Field(description="Predicted affinity score. Different scale/derivation than ChemistryEdge.weight -- not directly comparable to it.")


class ChemistryGraph(BaseModel):
    """
    The actor collaboration graph scoped to one casting search: every
    candidate actor under consideration as a node, every actor pair with
    real shared history as an edge.

    This is the k-partite graph the team-search step (max edge-weight
    selection, one actor per character) runs over -- see the roadmap's
    chemistry-scoring step. `predicted_affinities` is an optional, clearly
    separate layer for that search's use only; nodes/edges alone are the
    ground truth.
    """
    nodes: list[ChemistryNode] = Field(default_factory=list)
    edges: list[ChemistryEdge] = Field(default_factory=list)
    predicted_affinities: list[PredictedAffinity] = Field(default_factory=list, description="Backoff signals for pairs absent from `edges`, for the optimizer's search step only -- kept separate from edges/weight by design (see PredictedAffinity).")


class ChemistryStrength(Enum):
    """Discrete high/medium/low label for a cluster's chemistry_score."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CastingSelection(BaseModel):
    """One character's chosen actor within a specific cluster."""
    character: CharacterProfile
    candidate: CastingCandidate


class CastingCluster(BaseModel):
    """One complete alternative cast: one candidate chosen per character, plus its chemistry score."""
    # An actor shouldn't repeat across selections in one cluster (same person can't play two
    # roles) -- the engine that builds these is responsible for that invariant, not this model.
    selections: list[CastingSelection] = Field(default_factory=list, description="One selection per character in the source CastingReport.")
    chemistry_score: float = Field(description="Value clusters are ranked by.")
    # Threshold logic (what score counts as "high") lives in the engine that assigns this.
    strength: ChemistryStrength = Field(description="Discrete classification of chemistry_score.")


class ChemistryReport(BaseModel):
    """Output of the chemistry engine: top clusters from a CastingReport, ranked by chemistry_score descending."""
    title: Optional[str] = Field(default=None, description="Title of the source screenplay/casting report, carried through for display.")
    # clusters[0] is the best cluster -- index position is the rank, no separate rank field.
    # Expected to hold up to 5 entries; fewer is valid if the search space can't produce 5
    # distinct full-cast combinations (e.g. very small casts) -- not validator-enforced.
    clusters: list[CastingCluster] = Field(default_factory=list, description="Top clusters, ranked descending by chemistry_score.")


class CoStarDelta(BaseModel):
    """Change in one specific pair's chemistry if a swap were made -- the 'why' behind a SwapPreview's total delta."""
    name: str = Field(description="The other currently-cast actor this delta is relative to.")
    delta: float = Field(description="Change in this pair's edge weight if the swap were made -- positive means more chemistry with this co-star, negative means less.")


class SwapPreview(BaseModel):
    """
    One alternate candidate's projected impact if swapped in for a
    character, without committing to it -- lets the frontend show a clear
    +/- and a per-co-star reason before the user picks. Candidates here
    already passed casting_director's role-fit search (see
    CastingDirectorAgent.find_candidates); this is the chemistry half of
    "based on both role fit and group chemistry."
    """
    candidate: CastingCandidate = Field(description="The alternate candidate this preview is for.")
    delta: float = Field(description="This cluster's chemistry_score if this candidate were swapped in, minus its current chemistry_score. Includes a tiny 2-hop backoff nudge only when estimated=True (see `estimated`); the committed /swap score never includes it.")
    per_costar: list[CoStarDelta] = Field(
        default_factory=list,
        description="Pairwise chemistry change against each other currently-cast actor with real shared history before or after the swap -- omits actors with no edge either way, so this only ever shows an actual reason.",
    )
    estimated: bool = Field(
        default=False,
        description=(
            "True when this candidate has zero direct shared-credit evidence with anyone currently "
            "cast (per_costar is empty) -- delta is then a rough 2-hop 'shared collaborators' estimate "
            "used only to break ties, not real evidence, and should be labeled differently in the UI. "
            "The actual committed /swap score for this candidate would not include this nudge."
        ),
    )
    used_in_other_cluster: bool = Field(
        default=False,
        description=(
            "True when this alternate is already a lead in one of this report's other clusters. "
            "A soft warning, not a filter -- picking them anyway is allowed; it just means the "
            "cross-cluster 'no actor leads more than one cluster' property (see "
            "ChemistryEngine._diverse_top) would no longer hold after this swap."
        ),
    )
