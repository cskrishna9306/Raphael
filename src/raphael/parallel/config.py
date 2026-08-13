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
        self.PARALLEL_API_KEY: str = os.getenv("PARALLEL_API_KEY")
        self.PARALLEL_PROCESSOR: str = "base"
        self.PARALLEL_API_TIMEOUT: str = "60"

        return


config = Config()
