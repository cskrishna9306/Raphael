# Import standard packages
import itertools
import random

# Import custom modules
from src.raphael.chemistry.config import config
from src.raphael.chemistry.utils import normalize_name, shared_production_credits, npmi, adamic_adar
from src.raphael.chemistry.models import (
    ChemistryNode,
    ChemistryEdge,
    ChemistryGraph,
    ChemistryStrength,
    CastingSelection,
    CastingCluster,
    ChemistryReport,
)
from src.raphael.agentry.casting_director.models import CastingReport


class ChemistryEngine:
    """Scores pairwise actor chemistry from a CastingReport's embedded dossiers and searches for the best-chemistry alternative casts."""

    def invoke(self, report: CastingReport) -> ChemistryReport:
        """Builds a scored ChemistryGraph from `report` and returns its top clusters."""
        graph = self.build_graph(report)
        clusters = self.search_clusters(report, graph)
        return ChemistryReport(title=report.title, clusters=clusters)

    def build_graph(self, report: CastingReport) -> ChemistryGraph:
        """Builds and scores the collaboration graph over every unique candidate in `report`."""
        candidates = report.unique_candidates()

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

        nodes = [ChemistryNode(name=name, total_credits=total_credits[name]) for name in candidates]

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

        return ChemistryGraph(nodes=nodes, edges=edges)

    def search_clusters(self, report: CastingReport, graph: ChemistryGraph) -> list[CastingCluster]:
        """Runs 1-swap local search with random restarts to find the top-scoring alternative casts."""
        characters = [casting.character for casting in report.castings]
        candidate_lists = [casting.candidates for casting in report.castings]
        if not characters or any(not c for c in candidate_lists):
            return []

        edge_weight = {frozenset((e.source, e.target)): e.weight for e in graph.edges}

        found: dict[tuple, float] = {}
        for _ in range(config.NUM_RANDOM_RESTARTS):
            start = [random.randrange(len(cands)) for cands in candidate_lists]
            assignment, score = self._local_search(start, candidate_lists, edge_weight)
            found[tuple(assignment)] = score

        if not found:
            return []

        lo, hi = min(found.values()), max(found.values())
        ranked = sorted(found.items(), key=lambda kv: kv[1], reverse=True)[:config.NUM_CLUSTERS]

        return [
            CastingCluster(
                selections=[
                    CastingSelection(character=characters[i], candidate=candidate_lists[i][idx])
                    for i, idx in enumerate(assignment)
                ],
                chemistry_score=score,
                strength=self._strength(score, lo, hi),
            )
            for assignment, score in ranked
        ]

    def _shaped_score(self, assignment, candidate_lists, edge_weight) -> float:
        """Team-search objective: pairwise chemistry sum, penalized for over-consolidated pair density. -inf if an actor is double-booked across characters."""
        names = [candidate_lists[i][idx].name for i, idx in enumerate(assignment)]
        if len(set(names)) != len(names):
            return float("-inf")

        pairs = list(itertools.combinations(names, 2))
        raw = sum(edge_weight.get(frozenset(p), 0.0) for p in pairs)
        density = sum(1 for p in pairs if frozenset(p) in edge_weight) / len(pairs) if pairs else 0.0
        return raw - config.LAMBDA_DENSITY_PENALTY * (density - config.TARGET_DENSITY) ** 2

    def _local_search(self, assignment, candidate_lists, edge_weight) -> tuple[list[int], float]:
        """Hill-climbs by swapping one character's actor at a time until no swap improves the shaped objective."""
        best = list(assignment)
        best_score = self._shaped_score(best, candidate_lists, edge_weight)

        for _ in range(config.MAX_SWAP_PASSES):
            improved = False
            for i, candidates in enumerate(candidate_lists):
                for idx in range(len(candidates)):
                    if idx == best[i]:
                        continue
                    trial = list(best)
                    trial[i] = idx
                    score = self._shaped_score(trial, candidate_lists, edge_weight)
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
