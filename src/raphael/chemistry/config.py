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

        # Relative weight of Adamic-Adar vs NPMI when combining into one edge weight
        self.ADAMIC_ADAR_WEIGHT: float = float(os.getenv("CHEMISTRY_ADAMIC_ADAR_WEIGHT", "1.0"))

        # Shaped-objective penalty: discourages an all-star cast where every pair already has real shared history
        self.TARGET_DENSITY: float = float(os.getenv("CHEMISTRY_TARGET_DENSITY", "0.35"))
        self.LAMBDA_DENSITY_PENALTY: float = float(os.getenv("CHEMISTRY_LAMBDA_DENSITY_PENALTY", "1.0"))

        return


config = Config()
