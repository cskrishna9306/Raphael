# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """Tunables for the chemistry engine's scoring and cluster search. All computation is local -- no credentials needed."""

    def __init__(self):
        load_dotenv()

        # Top clusters returned in a ChemistryReport
        self.NUM_CLUSTERS: int = int(os.getenv("CHEMISTRY_NUM_CLUSTERS", "5"))

        # 1-swap local search: random restarts, and the cap on swap passes per restart before giving up on convergence
        self.NUM_RANDOM_RESTARTS: int = int(os.getenv("CHEMISTRY_NUM_RANDOM_RESTARTS", "20"))
        self.MAX_SWAP_PASSES: int = int(os.getenv("CHEMISTRY_MAX_SWAP_PASSES", "25"))

        # Caps the cartesian product of lead-role candidate combinations search_clusters anchors
        # restarts on -- grows multiplicatively with the number of lead roles (candidates^leads),
        # so this bounds worst-case restart count for scripts with several lead characters
        self.MAX_LEAD_ANCHOR_COMBINATIONS: int = int(os.getenv("CHEMISTRY_MAX_LEAD_ANCHOR_COMBINATIONS", "200"))

        # Caps the one-at-a-time anchored restarts search_clusters runs for non-lead roles
        # (supporting/minor) -- grows additively with total candidates across those roles
        # (not multiplicatively like the lead cartesian above), but still bounded for casts
        # with many named characters
        self.MAX_NON_LEAD_ANCHOR_RESTARTS: int = int(os.getenv("CHEMISTRY_MAX_NON_LEAD_ANCHOR_RESTARTS", "300"))

        # Relative weight of Adamic-Adar vs NPMI when combining into one edge weight
        self.ADAMIC_ADAR_WEIGHT: float = float(os.getenv("CHEMISTRY_ADAMIC_ADAR_WEIGHT", "1.0"))

        # Shaped-objective penalty: discourages an all-star cast where every pair already has real shared history
        self.TARGET_DENSITY: float = float(os.getenv("CHEMISTRY_TARGET_DENSITY", "0.35"))
        self.LAMBDA_DENSITY_PENALTY: float = float(os.getenv("CHEMISTRY_LAMBDA_DENSITY_PENALTY", "1.0"))

        # Weight applied to PredictedAffinity's 2-hop "shared collaborators" backoff signal when
        # a pair has no real ChemistryEdge -- lets both the cluster search and the swap preview
        # differentiate/rank actor pairs who've simply never worked together (the common case),
        # instead of every such pair flattening to the exact same zero contribution. Deliberately
        # tiny relative to a real edge (commonly ~0.5-2+) combined with the cap below, so it can
        # never outrank real evidence -- see ChemistryEngine._weight_lookup/build_graph.
        self.PREDICTED_AFFINITY_WEIGHT: float = float(os.getenv("CHEMISTRY_PREDICTED_AFFINITY_WEIGHT", "0.02"))

        # Caps shared_collaborator_count's raw overlap count before it's scaled by the weight
        # above, so one very prolific/well-documented actor's long collaborator list can't push
        # a predicted score up near real-edge magnitude
        self.MAX_PREDICTED_SHARED_COLLABORATORS: int = int(os.getenv("CHEMISTRY_MAX_PREDICTED_SHARED_COLLABORATORS", "5"))

        # Per-actor terms (not pairwise -- see ChemistryEngine._actor_adjustment), added once per
        # actor in the cast on top of the pairwise chemistry sum. ROLE_FIT_WEIGHT scales
        # CastingCandidate.fit_score (already 0-1), so 0.5 means a perfect-fit actor contributes
        # about as much as one real shared credit; a poor-fit actor (near 0) contributes ~nothing.
        # Risk penalties are asymmetric by design -- low risk costs nothing, medium is a mild
        # nudge, high is a real (but not disqualifying) drag, comparable in magnitude to losing a
        # real shared-credit connection.
        self.ROLE_FIT_WEIGHT: float = float(os.getenv("CHEMISTRY_ROLE_FIT_WEIGHT", "0.5"))
        self.RISK_PENALTY_LOW: float = float(os.getenv("CHEMISTRY_RISK_PENALTY_LOW", "0.0"))
        self.RISK_PENALTY_MEDIUM: float = float(os.getenv("CHEMISTRY_RISK_PENALTY_MEDIUM", "-0.3"))
        self.RISK_PENALTY_HIGH: float = float(os.getenv("CHEMISTRY_RISK_PENALTY_HIGH", "-1.0"))

        return


config = Config()
