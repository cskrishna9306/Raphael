# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """
    Env-driven settings for the TMDB client.
    """

    def __init__(self):
        """
        Initialize all the necessary class variables.
        """

        load_dotenv()

        # TMDB's v4 "API Read Access Token" -- a free account at themoviedb.org,
        # used as a Bearer token (not the older v3 api_key query param).
        self.TMDB_API_KEY: str | None = os.getenv("TMDB_API_KEY")
        self.TMDB_BASE_URL: str = os.getenv("TMDB_BASE_URL", "https://api.themoviedb.org/3")
        self.TMDB_IMAGE_BASE_URL: str = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p/w500")
        self.TMDB_TIMEOUT: float = float(os.getenv("TMDB_TIMEOUT", "30"))

        return


config = Config()
