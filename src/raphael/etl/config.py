# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """
    Env-driven settings for the ETL discovery/populate pipeline.
    """

    def __init__(self):
        """
        Initialize all the necessary class variables.
        """

        load_dotenv()

        # Graph-traversal budget: how many actor-generations deep and how wide
        # `discover` walks the TMDB actor/movie graph before stopping. These are
        # counts, not durations, so int() (not the float() convention used for
        # timeouts in the other Config classes) is the correct cast here.
        self.ETL_TRAVERSAL_MAX_DEPTH: int = int(os.getenv("ETL_TRAVERSAL_MAX_DEPTH", "3"))
        self.ETL_TRAVERSAL_MAX_ACTORS: int = int(os.getenv("ETL_TRAVERSAL_MAX_ACTORS", "150"))
        self.ETL_TRAVERSAL_MOVIES_PER_ACTOR: int = int(os.getenv("ETL_TRAVERSAL_MOVIES_PER_ACTOR", "5"))
        self.ETL_TRAVERSAL_CAST_PER_MOVIE: int = int(os.getenv("ETL_TRAVERSAL_CAST_PER_MOVIE", "10"))

        # Bounded concurrency -- neither TMDBClient nor ParallelClient rate-limit
        # themselves, so a wide traversal/research batch needs a client-side cap.
        self.ETL_TMDB_CONCURRENCY: int = int(os.getenv("ETL_TMDB_CONCURRENCY", "5"))
        self.ETL_PARALLEL_RESEARCH_CONCURRENCY: int = int(os.getenv("ETL_PARALLEL_RESEARCH_CONCURRENCY", "3"))

        return


config = Config()
