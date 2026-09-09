# Import standard packages
import hashlib
import itertools
import random
from typing import NamedTuple, Optional

# Import custom modules
from src.raphael.chemistry.config import config
from src.raphael.chemistry.utils import normalize_name, shared_production_credits, shared_collaborator_count, npmi, adamic_adar
from src.raphael.chemistry.models import (
    ChemistryNode,
    ChemistryEdge,
    ChemistryGraph,
    ChemistryStrength,
    CastingSelection,
    CastingCluster,
    ChemistryReport,
    CoStarDelta,
    SwapPreview,
    PredictedAffinity,
    AffinityMethod,
)
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.screenplay_breakdown.models import RolePresence
from src.raphael.agentry.risk_management.models import RiskAssessment, RiskLevel


class _ScoringContext(NamedTuple):
    """
    Bundles the three lookups the scoring objective needs, so
    search_clusters/score_selection/preview_swaps thread one object instead
    of an ever-growing list of positional dicts. See ChemistryEngine._scoring_context.
    """
    weight_lookup: dict
    real_pairs: dict
    actor_adjustment: dict


class ChemistryEngine:
    """Scores pairwise actor chemistry from a CastingReport's embedded dossiers and searches for the best-chemistry alternative casts."""

    def invoke(self, report: CastingReport, risk_assessments: Optional[dict[str, RiskAssessment]] = None) -> ChemistryReport:
        """
        Builds a scored ChemistryGraph from `report` and returns its top
        clusters. `risk_assessments` (name -> RiskAssessment, typically
        every unique candidate's from the same /recommend run's RiskReport)
        feeds chemistry_score's per-actor risk penalty -- see build_graph/
        _actor_adjustment. Omit to score without a risk adjustment.
        """
        graph = self.build_graph(report, risk_assessments)
        clusters = self.search_clusters(report, graph)
        return ChemistryReport(title=report.title, clusters=clusters)

    def build_graph(self, report: CastingReport, risk_assessments: Optional[dict[str, RiskAssessment]] = None) -> ChemistryGraph:
        """
        Builds and scores the collaboration graph over every unique
        candidate in `report`. Each node also carries the two per-actor (not
        pairwise) signals chemistry_score now includes: CastingCandidate.
        fit_score (role alignment, already embedded per candidate from
        casting_director's search) and this actor's risk_level from
        `risk_assessments`, if supplied -- see _actor_adjustment.
        """
        candidates = report.unique_candidates()
        risk_assessments = risk_assessments or {}

        total_credits = {
            name: len({normalize_name(item.title) for item in c.dossier.filmography}) if c.dossier else 0
            for name, c in candidates.items()
        }
        # Corpus size approximates the known production universe as every distinct title
        # mentioned across these candidates' own dossiers -- no external corpus wired up yet.
        corpus_size = len({
            normalize_name(item.title)
            for c in candidates.values() if c.dossier
            for item in c.dossier.filmography
        })

        nodes = [
            ChemistryNode(
                name=name,
                total_credits=total_credits[name],
                role_fit=candidates[name].fit_score,
                risk_level=risk_assessments[name].risk_level if name in risk_assessments else None,
            )
            for name in candidates
        ]

        edges = []
        for a_name, b_name in itertools.combinations(candidates, 2):
            credits = shared_production_credits(candidates[a_name].dossier, candidates[b_name].dossier)
            if not credits:
                continue  # no shared history -- no edge, by design (see ChemistryEdge)

            edge_npmi = npmi(len(credits), total_credits[a_name], total_credits[b_name], corpus_size)
            edge_adamic_adar = adamic_adar(credits)
            weight = (edge_npmi or 0.0) + config.ADAMIC_ADAR_WEIGHT * (edge_adamic_adar or 0.0)

            edges.append(ChemistryEdge(
                source=a_name, target=b_name, shared_credits=credits,
                npmi=edge_npmi, adamic_adar=edge_adamic_adar, weight=weight,
            ))

        # Sparsity backoff: most candidate pairs pulled from an open casting search have
        # simply never worked together, so most pairs get no ChemistryEdge at all -- without
        # this, the search/preview can't differentiate any of them. For every edge-less pair,
        # count documented collaborators/co-stars the two share even without a direct credit
        # ("friends of friends") as a PredictedAffinity -- kept deliberately separate from
        # ChemistryEdge/weight (see both models' docstrings), consumed only via
        # _scoring_context's `weight_lookup`, and never mistaken for observed history.
        edged_pairs = {frozenset((edge.source, edge.target)) for edge in edges}
        predicted_affinities = []
        for a_name, b_name in itertools.combinations(candidates, 2):
            if frozenset((a_name, b_name)) in edged_pairs:
                continue
            shared = shared_collaborator_count(candidates[a_name].dossier, candidates[b_name].dossier)
            if shared:
                predicted_affinities.append(PredictedAffinity(
                    source=a_name, target=b_name,
                    method=AffinityMethod.SHARED_COLLABORATORS,
                    score=float(min(shared, config.MAX_PREDICTED_SHARED_COLLABORATORS)),
                ))

        return ChemistryGraph(nodes=nodes, edges=edges, predicted_affinities=predicted_affinities)

    def _scoring_context(self, graph: ChemistryGraph) -> _ScoringContext:
        """
        Builds the full scoring context from a ChemistryGraph: `weight_lookup`
        (real edges plus PredictedAffinity's small backoff for edge-less
        pairs -- see build_graph), `real_pairs` (real edges only, kept
        available wherever code needs to know if a pair's signal is real vs.
        predicted, e.g. preview_swaps' `estimated`), and `actor_adjustment`
        (per-actor role-fit/risk contribution, see _actor_adjustment).
        """
        edge_weight = {frozenset((e.source, e.target)): e.weight for e in graph.edges}
        effective_weight = dict(edge_weight)
        for predicted in graph.predicted_affinities:
            pair = frozenset((predicted.source, predicted.target))
            if pair not in effective_weight:
                effective_weight[pair] = config.PREDICTED_AFFINITY_WEIGHT * predicted.score

        actor_adjustment = {node.name: self._actor_adjustment(node) for node in graph.nodes}

        return _ScoringContext(weight_lookup=effective_weight, real_pairs=edge_weight, actor_adjustment=actor_adjustment)

    def _actor_adjustment(self, node: ChemistryNode) -> float:
        """
        Per-actor (not pairwise) contribution to chemistry_score: how well
        this actor fits their specific role (ChemistryNode.role_fit, scaled
        by ROLE_FIT_WEIGHT) plus a risk penalty from their risk_level, when
        either is available. Both default to no contribution -- a
        director-specified preferred_actor has no fit_score, and a graph
        built without risk_assessments has no risk_level.
        """
        adjustment = 0.0
        if node.role_fit is not None:
            adjustment += config.ROLE_FIT_WEIGHT * node.role_fit
        if node.risk_level is not None:
            adjustment += {
                RiskLevel.LOW: config.RISK_PENALTY_LOW,
                RiskLevel.MEDIUM: config.RISK_PENALTY_MEDIUM,
                RiskLevel.HIGH: config.RISK_PENALTY_HIGH,
            }[node.risk_level]
        return adjustment

    def _seed_for(self, report: CastingReport) -> int:
        """
        Deterministic seed derived from the report's actual candidate data --
        same CastingReport always explores the same random-restart sequence
        and returns the same top clusters, removing search_clusters's own RNG
        as a source of run-to-run variance. This does NOT make the whole
        /recommend pipeline idempotent by itself -- casting_director's live
        web search can still return different candidates between runs on the
        same screenplay, and no amount of seeding here changes that -- but it
        does guarantee "same candidates in -> same clusters out", which
        wasn't true before (every run reshuffled which local optima got
        discovered even over identical data).
        """
        keys = sorted(report.unique_candidates().keys())
        material = f"{report.title or ''}|{'|'.join(keys)}"
        return int(hashlib.sha256(material.encode()).hexdigest(), 16) % (2**32)

    def search_clusters(self, report: CastingReport, graph: ChemistryGraph) -> list[CastingCluster]:
        """
        Runs 1-swap local search with random restarts to find the top-scoring
        alternative casts, then picks the top clusters so they vary who plays
        *every* named role across clusters, not just the lead(s), rather than
        all converging on the same strongest cast with only a handful of
        roles differing.
        """
        characters = [casting.character for casting in report.castings]
        candidate_lists = [casting.candidates for casting in report.castings]
        if not characters or any(not c for c in candidate_lists):
            return []

        context = self._scoring_context(graph)
        rng = random.Random(self._seed_for(report))

        found: dict[tuple, float] = {}
        for _ in range(config.NUM_RANDOM_RESTARTS):
            start = [rng.randrange(len(cands)) for cands in candidate_lists]
            assignment, score = self._local_search(start, candidate_lists, context)
            found[tuple(assignment)] = score

        # Anchored restarts, lead roles: a free random start almost always climbs
        # into the single strongest lead combination's basin of attraction, so
        # unanchored restarts alone rarely surface a genuinely different
        # combination (with 2+ lead roles, even anchoring one lead at a time isn't
        # enough -- the OTHER lead's hill-climb just settles back onto its own
        # usual favorite, so a combination like (Ben=Idris, Barbara=Florence) can
        # go entirely undiscovered even though each half was individually
        # anchored). Anchor every combination of lead-role candidates
        # *simultaneously* (fixing ALL lead positions at once, not just one) so
        # every combination gets a genuine best-cast-around-them search. Capped
        # and sampled if the full cartesian product would be large, since it
        # grows multiplicatively with the number of lead roles.
        lead_positions = [i for i, character in enumerate(characters) if character.role_presence == RolePresence.LEAD]
        if lead_positions:
            combinations = list(itertools.product(*(range(len(candidate_lists[pos])) for pos in lead_positions)))
            if len(combinations) > config.MAX_LEAD_ANCHOR_COMBINATIONS:
                combinations = rng.sample(combinations, config.MAX_LEAD_ANCHOR_COMBINATIONS)
            for combo in combinations:
                start = [rng.randrange(len(cands)) for cands in candidate_lists]
                fixed = dict(zip(lead_positions, combo))
                for pos, idx in fixed.items():
                    start[pos] = idx
                assignment, score = self._local_search(start, candidate_lists, context, fixed=fixed)
                found[tuple(assignment)] = score

        # Anchored restarts, every other role (supporting/minor): the same
        # "unanchored restarts converge on one favorite" problem applies here too
        # -- without this, only leads ever varied across clusters, because only
        # leads were ever anchored. A full cartesian like leads get would be
        # combinatorially intractable once there are more than a couple of
        # roles, so this anchors one position at a time instead: still
        # guarantees every supporting/minor candidate gets a genuine
        # best-cast-around-them search, just without the "every combination
        # simultaneously" guarantee the (much smaller) lead cartesian gives.
        # Capped and sampled if there are many named characters with many
        # candidates each.
        non_lead_positions = [i for i in range(len(characters)) if i not in lead_positions]
        non_lead_anchors = [(pos, idx) for pos in non_lead_positions for idx in range(len(candidate_lists[pos]))]
        if len(non_lead_anchors) > config.MAX_NON_LEAD_ANCHOR_RESTARTS:
            non_lead_anchors = rng.sample(non_lead_anchors, config.MAX_NON_LEAD_ANCHOR_RESTARTS)
        for position, idx in non_lead_anchors:
            start = [rng.randrange(len(cands)) for cands in candidate_lists]
            start[position] = idx
            assignment, score = self._local_search(start, candidate_lists, context, fixed={position: idx})
            found[tuple(assignment)] = score

        # An anchor can force an impossible combination -- e.g. anchoring one
        # position to the same actor who is some *other* position's only
        # candidate leaves the hill-climb no way to escape a double-booking
        # (neither position can swap away: one is fixed, the other has
        # nothing else to swap to). _score_names already scores that -inf;
        # drop those here so an invalid, double-cast assignment can never
        # surface as a "cluster" regardless of how it was discovered -- fewer
        # than NUM_CLUSTERS valid, distinct combinations is fine (see
        # ChemistryReport.clusters), an invalid one is not.
        found = {assignment: score for assignment, score in found.items() if score != float("-inf")}

        if not found:
            return []

        lo, hi = min(found.values()), max(found.values())
        ranked = sorted(found.items(), key=lambda kv: kv[1], reverse=True)
        diverse_positions = list(range(len(characters)))
        selected = self._diverse_top(ranked, diverse_positions, candidate_lists, config.NUM_CLUSTERS)

        return [
            CastingCluster(
                selections=[
                    CastingSelection(character=characters[i], candidate=candidate_lists[i][idx])
                    for i, idx in enumerate(assignment)
                ],
                chemistry_score=score,
                strength=self._strength(score, lo, hi),
            )
            for assignment, score in selected
        ]

    def _diverse_top(self, ranked: list[tuple[tuple, float]], diverse_positions: list[int], candidate_lists, n: int) -> list[tuple[tuple, float]]:
        """
        Picks up to n assignments so that no actor plays any tracked role
        (`diverse_positions` -- every named character, not just leads) in
        more than one selected cluster -- once someone is cast anywhere,
        they're fully excluded from seeding another cluster's cast, not just
        from repeating the exact same combination (a cluster reusing the
        same actor as a *different* character still counts as a repeat).
        Falls back to the next-best score (reuse allowed) only once there
        aren't enough fully-disjoint options left, so this never returns
        fewer clusters than picking straight off `ranked` would have.
        """
        if not diverse_positions:
            return ranked[:n]

        selected: list[tuple[tuple, float]] = []
        leftover: list[tuple[tuple, float]] = []
        used_names: set[str] = set()

        for assignment, score in ranked:
            names = {candidate_lists[i][assignment[i]].name for i in diverse_positions}
            if names & used_names:
                leftover.append((assignment, score))
                continue
            used_names |= names
            selected.append((assignment, score))
            if len(selected) == n:
                return selected

        selected.extend(leftover[: n - len(selected)])
        return selected

    def _shaped_score(self, assignment, candidate_lists, context: _ScoringContext) -> float:
        """Team-search objective: pairwise chemistry sum plus per-actor adjustments, penalized for over-consolidated pair density. -inf if an actor is double-booked across characters."""
        names = [candidate_lists[i][idx].name for i, idx in enumerate(assignment)]
        return self._score_names(names, context)

    def _score_names(self, names: list[str], context: _ScoringContext) -> float:
        """
        Shared scoring objective, keyed by candidate name rather than
        candidate_lists index -- lets score_selection() score one ad-hoc
        assignment (e.g. a single swap) without needing the full per-
        character candidate_lists the random-restart search walks. -inf if
        an actor is double-booked across characters.

        `context.weight_lookup` (real edges plus PredictedAffinity's
        backoff) drives the pairwise sum; `context.real_pairs` (edges only)
        drives the density term on purpose -- density measures how much of
        this cast is grounded in *observed* relationships, so a
        predicted/estimated pair must never count toward it. Without this
        split, a tiny positive backoff nudge could push density up enough
        to make the penalty term outweigh the nudge itself, scoring a
        candidate with weak real signal *worse* than one with none at all.
        `context.actor_adjustment` adds each cast member's own role-fit/risk
        contribution once per actor, independent of any pairing.
        """
        if len(set(names)) != len(names):
            return float("-inf")

        pairs = list(itertools.combinations(names, 2))
        raw = sum(context.weight_lookup.get(frozenset(p), 0.0) for p in pairs)
        density = sum(1 for p in pairs if frozenset(p) in context.real_pairs) / len(pairs) if pairs else 0.0
        per_actor = sum(context.actor_adjustment.get(name, 0.0) for name in names)
        return raw + per_actor - config.LAMBDA_DENSITY_PENALTY * (density - config.TARGET_DENSITY) ** 2

    def score_selection(
        self,
        casting_report: CastingReport,
        selections: list[CastingSelection],
        reference_scores: list[float],
        risk_assessments: Optional[dict[str, RiskAssessment]] = None,
    ) -> CastingCluster:
        """
        Scores one ad-hoc, caller-provided cast assignment (e.g. `selections`
        with a single character's candidate swapped out) against the same
        objective search_clusters optimizes, without re-running the
        random-restart search.

        Rebuilds the graph from `casting_report` -- cheap, pure computation
        over already-embedded dossiers, no agent/Parallel/ClickHouse calls --
        so the edge weight between a not-previously-selected substitute and
        every other selected actor is available even if that pairing never
        appeared in any of the originally-ranked clusters. `risk_assessments`
        (typically the Roster's) feeds the same per-actor risk penalty
        build_graph/invoke apply, so a committed swap's score stays
        consistent with the cluster search that produced the original
        recommendations.

        `reference_scores` (typically the chemistry_score of the clusters
        this selection was drawn from) stands in for the local-search score
        range _strength() normally buckets against, since there's no
        multi-restart search here to derive a range from.

        Raises ValueError if `selections` double-books an actor across
        characters (the same failure search_clusters silently scores -inf
        and discards -- here it's a real user-facing error instead).
        """
        graph = self.build_graph(casting_report, risk_assessments)
        context = self._scoring_context(graph)

        names = [selection.candidate.name for selection in selections]
        if len(set(names)) != len(names):
            dupe = next(name for name in names if names.count(name) > 1)
            raise ValueError(f"'{dupe}' is already cast elsewhere in this cluster.")

        score = self._score_names(names, context)
        lo, hi = min(reference_scores), max(reference_scores)
        return CastingCluster(selections=selections, chemistry_score=score, strength=self._strength(score, lo, hi))

    def preview_swaps(
        self,
        casting_report: CastingReport,
        selections: list[CastingSelection],
        character_name: str,
        used_elsewhere: list[str] | None = None,
        risk_assessments: Optional[dict[str, RiskAssessment]] = None,
    ) -> list[SwapPreview]:
        """
        For one character in a cluster, scores every OTHER candidate in
        their shortlist as a hypothetical replacement -- without committing
        to any of them -- so the frontend can show each alternative's real
        score delta and a per-co-star breakdown of *why*, ranked by
        chemistry impact, before the user picks one. This is the chemistry
        half of "based on both role fit and group chemistry": every
        candidate here already passed casting_director's role-fit search
        (see CastingDirectorAgent.find_candidates), so ranking them by delta
        combines both signals without re-running any search. `risk_assessments`
        (typically the Roster's) folds each alternate's own risk penalty into
        that same delta, consistent with build_graph/invoke.

        `used_elsewhere` (typically every actor already cast in this report's
        *other* clusters, across every role, not just leads) is never
        dropped from the alternates offered here -- with a small shortlist
        and several clusters each maximizing cast diversity (see
        _diverse_top), a hard filter can exhaust the entire shortlist and
        leave nothing to swap to at all. Instead each such alternate is
        flagged `used_in_other_cluster=True` so the frontend can surface it
        as a soft warning and still let the user pick it deliberately.

        Rebuilds the graph from `casting_report` -- cheap, pure computation
        over already-embedded dossiers, same as score_selection. Uses the
        same real-plus-predicted `weight_lookup` search_clusters/
        score_selection use (see _scoring_context/build_graph), so a
        candidate with no direct shared-credit history still ranks
        differently from another such candidate instead of tying flat at
        zero -- `real_pairs` is kept alongside just to label which
        candidates that backoff actually applied to (`estimated`).
        """
        graph = self.build_graph(casting_report, risk_assessments)
        context = self._scoring_context(graph)
        edge_weight = context.real_pairs

        current_names = [selection.candidate.name for selection in selections]
        current_score = self._score_names(current_names, context)

        current_selection = next(s for s in selections if s.character.name == character_name)
        current_candidate_name = current_selection.candidate.name
        other_names = [name for name in current_names if name != current_candidate_name]

        character_casting = next(casting for casting in casting_report.castings if casting.character.name == character_name)
        shortlist = character_casting.candidates
        used_elsewhere_set = set(used_elsewhere or [])

        previews = []
        for alternate in shortlist:
            # Skip the current pick (nothing to preview) and anyone already cast as a
            # *different* character in this same cluster -- offering them would just
            # double-book the cluster (score_selection would reject it outright; here,
            # silently excluding it is more useful than showing a nonsensical -inf delta).
            if alternate.name == current_candidate_name or alternate.name in other_names:
                continue

            trial_selections = [
                s.model_copy(update={"candidate": alternate}) if s.character.name == character_name else s
                for s in selections
            ]
            trial_names = [s.candidate.name for s in trial_selections]
            trial_score = self._score_names(trial_names, context)

            # Real-only (edge_weight, not effective_weight) on purpose: per_costar and
            # `estimated` are about what's actually observed, independent of whether the
            # backoff nudged this alternate's ranking above.
            per_costar = []
            has_direct_evidence = False
            for other_name in other_names:
                before = edge_weight.get(frozenset((current_candidate_name, other_name)), 0.0)
                after = edge_weight.get(frozenset((alternate.name, other_name)), 0.0)
                if after:
                    has_direct_evidence = True
                if before or after:
                    # Real -- either the outgoing actor's connection being lost (before) or the
                    # alternate's own (after); both are legitimate to show, independent of
                    # `estimated` below, which only asks whether THIS alternate brings any real
                    # evidence of their own.
                    per_costar.append(CoStarDelta(name=other_name, delta=after - before))

            previews.append(SwapPreview(
                candidate=alternate,
                delta=trial_score - current_score,
                per_costar=per_costar,
                estimated=not has_direct_evidence,
                used_in_other_cluster=alternate.name in used_elsewhere_set,
            ))

        previews.sort(key=lambda preview: preview.delta, reverse=True)
        return previews

    def _local_search(self, assignment, candidate_lists, context: _ScoringContext, fixed: dict[int, int] | None = None) -> tuple[list[int], float]:
        """
        Hill-climbs by swapping one character's actor at a time until no swap
        improves the shaped objective. `fixed` (character position -> forced
        candidate index) excludes those positions from the swap loop -- used
        by search_clusters to hold a lead role's actor in place so the rest
        of the cast genuinely optimizes around them, instead of the hill
        climb immediately swapping away to whichever lead scores highest.
        """
        fixed = fixed or {}
        best = list(assignment)
        best_score = self._shaped_score(best, candidate_lists, context)

        for _ in range(config.MAX_SWAP_PASSES):
            improved = False
            for i, candidates in enumerate(candidate_lists):
                if i in fixed:
                    continue
                for idx in range(len(candidates)):
                    if idx == best[i]:
                        continue
                    trial = list(best)
                    trial[i] = idx
                    score = self._shaped_score(trial, candidate_lists, context)
                    if score > best_score:
                        best, best_score, improved = trial, score, True
            if not improved:
                break

        return best, best_score

    def _strength(self, score: float, lo: float, hi: float) -> ChemistryStrength:
        """Buckets a cluster's score into high/medium/low, relative to the range of every local optimum this search found."""
        if hi == lo:
            return ChemistryStrength.HIGH
        position = (score - lo) / (hi - lo)
        if position >= 2 / 3:
            return ChemistryStrength.HIGH
        if position >= 1 / 3:
            return ChemistryStrength.MEDIUM
        return ChemistryStrength.LOW
