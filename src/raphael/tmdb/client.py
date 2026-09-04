# Import standard packages
from typing import Any, Optional
import httpx

# Import custom modules
from src.raphael.tmdb.config import config
from src.raphael.tmdb.models import MovieSearchResult, MovieCredits, CastMember, CrewMember


class TMDBClient:
    """
    Thin wrapper over TMDB's official API. Only the search + credits endpoints
    needed to go from a movie title to its people are implemented here (see the
    "Call to get people from movie" ticket).
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the TMDB client.
        """
        self._api_key = api_key or config.TMDB_API_KEY
        self._base_url = base_url or config.TMDB_BASE_URL

    async def _get(self, path: str, params: dict[str, Any]) -> Optional[dict]:
        """
        Run a GET request against the TMDB API and return its JSON body.
        """
        if not self._api_key:
            print("[TMDB] TMDB_API_KEY is not set. Please add it to your .env.")
            return None

        try:
            async with httpx.AsyncClient(timeout=config.TMDB_TIMEOUT) as client:
                response = await client.get(
                    f"{self._base_url}/{path}",
                    params=params,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[TMDB] Error calling {path}: {e}")
            return None

    async def search_movie(self, title: str) -> Optional[MovieSearchResult]:
        """
        Find the first search hit for `title`. Doesn't disambiguate between
        multiple candidates (e.g. remakes) -- takes whatever TMDB ranks first.
        """
        data = await self._get("search/movie", {"query": title})
        if data is None:
            return None
        results = data.get("results", [])
        if not results:
            return None
        return MovieSearchResult(**results[0])

    async def get_movie_credits(self, movie_id: int) -> Optional[MovieCredits]:
        """
        Fetch a movie's full cast/crew credits by its TMDB id.
        """
        data = await self._get(f"movie/{movie_id}/credits", {})
        if data is None:
            return None
        return MovieCredits(
            cast=[CastMember(**member) for member in data.get("cast", [])],
            crew=[CrewMember(**member) for member in data.get("crew", [])],
        )

    async def find_movie_credits(self, title: str) -> Optional[MovieCredits]:
        """
        Look up `title` on TMDB and return its full cast/crew credits in one call --
        the single entry point everything else (e.g. main.py's movie-cast demo) uses.
        """
        result = await self.search_movie(title)
        if result is None:
            print(f"[TMDB] No movie match found for '{title}'.")
            return None
        return await self.get_movie_credits(result.id)
