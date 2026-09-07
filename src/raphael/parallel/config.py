# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """
    Settings to support the Parallel module/client.
    """

    def __init__(self):
        """
        Initialize all the env-driven variables.
        """

        # I guess this is run everytime we create a new Config object
        load_dotenv()

        # Initialize all the necessary class variables
        self.PARALLEL_API_KEY: str | None = os.getenv("PARALLEL_API_KEY")
        self.PARALLEL_PROCESSOR: str = os.getenv("PARALLEL_PROCESSOR", "base")
        self.PARALLEL_RESEARCH_PROCESSOR: str = os.getenv("PARALLEL_RESEARCH_PROCESSOR", "pro-fast")
        # pro-fast has a documented 30s-5min latency
        # A short-time window of 120s preemptively shuts down the research agent
        self.PARALLEL_API_TIMEOUT: float = float(os.getenv("PARALLEL_API_TIMEOUT", "300"))

        return


config = Config()

