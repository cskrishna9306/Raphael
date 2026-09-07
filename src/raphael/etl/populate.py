import sys
import json
import asyncio
from typing import Optional
from src.raphael.parallel.client import ParallelClient
from src.raphael.clickhouse.handler import ClickHouseHandler
from src.raphael.tmdb.client import TMDBClient
from src.raphael.etl.config import config as etl_config


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "roster":
        return asyncio.run(_search_roster_demo(sys.argv[2:]))

    if len(sys.argv) > 1 and sys.argv[1] == "add-person":
        return asyncio.run(_add_person_demo(sys.argv[2:]))

    if len(sys.argv) > 1 and sys.argv[1] == "movie-cast":
        return asyncio.run(_movie_cast_demo(sys.argv[2:]))

    if len(sys.argv) > 1 and sys.argv[1] == "discover":
        return asyncio.run(_discover_demo(sys.argv[2:]))

    target = sys.argv[1] if len(sys.argv) > 1 else "Christopher Nolan"
    print(f"=== Raphael: Researching '{target}' via Parallel ===")

    client = ParallelClient()
    dossier = client.research_person(target)

    if dossier:
        print("\n=== Research Results ===")
        print(f"Name: {dossier.name}")
        print(f"Roles: {', '.join(dossier.primary_roles)}")
        print(f"Bio: {dossier.bio_summary}")
        print(f"\nFilmography ({len(dossier.filmography)} credits):")
        for item in dossier.filmography[:5]:
            print(f"  - {item.title} ({item.year}): {item.role}")
        print(f"\nCollaborators ({len(dossier.collaborators)} found):")
        for c in dossier.collaborators[:5]:
            print(f"  - {c.name} ({c.role}) on {', '.join(c.shared_projects)}")
            for statement in c.public_statements_about_collaboration:
                print(f"    Quote: {statement}")
        print(f"\nRecognition:")
        print(f"  Awards: {', '.join(dossier.recognition.awards_and_nominations[:3]) or 'N/A'}")
        print(f"  Controversies: {', '.join(dossier.recognition.documented_controversies) or 'N/A'}")
        print(f"\nAvailability:")
        print(f"  Commitments: {', '.join(dossier.availability.current_and_upcoming_commitments) or 'N/A'}")
        print(f"  Union Affiliation: {', '.join(dossier.availability.union_affiliation) or 'N/A'}")
        print(f"\nSkills: {', '.join(dossier.skills.languages_and_accents + dossier.skills.physical_skills) or 'N/A'}")
        print(f"Social Media Following: {dossier.attributes.social_media_following or 'N/A'}")

        print("\n=== Storing in ClickHouse ===")
        stored = asyncio.run(_store_in_clickhouse(dossier))
        print("Stored successfully." if stored else "Failed to store in ClickHouse.")
    else:
        print("No dossier returned or research failed.")


async def _store_in_clickhouse(dossier) -> bool:
    async with ClickHouseHandler() as handler:
        return await handler.insert_person(dossier)


async def _search_roster_demo(current_picks: list[str]) -> None:
    """
    Manual smoke test for search_roster:
        uv run python -m src.raphael.etl.populate roster "Christopher Nolan" "Cillian Murphy"
    """
    print(f"=== Raphael: Roster search favoring {current_picks or '(none picked yet)'} ===")
    async with ClickHouseHandler() as handler:
        result = await handler.search_roster(
            criteria={"primary_roles": ["Actor"]},
            current_picks=current_picks,
            limit=10,
        )
    print(result if result is not None else "Query failed or ClickHouse unreachable (check .env credentials).")


async def _add_person_demo(args: list[str]) -> None:
    """
    Manual smoke test for find_or_research_person -- also demonstrates the
    looked-up person joining the current roster in the same run:
        uv run python -m src.raphael.etl.populate add-person "Some Name" "Christopher Nolan"
    """
    if not args:
        print("Usage: add-person <name> [current_pick ...]")
        return
    name, current_picks = args[0], args[1:]

    print(f"=== Raphael: Looking up '{name}' (research on demand if new) ===")
    parallel_client = ParallelClient()
    async with ClickHouseHandler() as handler:
        person = await handler.find_or_research_person(parallel_client, name)
        if person is None:
            print("Lookup/research/storage failed -- check .env credentials and Parallel API key.")
            return
        print(person)

        updated_picks = current_picks + [name]
        print(f"\n=== Roster search now favoring {updated_picks} ===")
        result = await handler.search_roster(current_picks=updated_picks, limit=10)
    print(result if result is not None else "Roster query failed.")


async def _movie_cast_demo(args: list[str]) -> None:
    """
    Manual smoke test: pull a movie's cast/crew from TMDB and research each cast
    member through the existing find_or_research_person path.
        uv run python -m src.raphael.etl.populate movie-cast "Inception" --limit 3
    """
    if not args:
        print("Usage: movie-cast <title> [--limit N]")
        return
    limit = None
    if "--limit" in args:
        idx = args.index("--limit")
        limit = int(args[idx + 1])
        args = args[:idx]
    title = " ".join(args)

    print(f"=== Raphael: Pulling cast/crew for '{title}' via TMDB ===")
    tmdb_client = TMDBClient()
    credits = await tmdb_client.find_movie_credits(title)
    if credits is None:
        print(f"No TMDB match found for '{title}' (check TMDB_API_KEY / spelling).")
        return

    cast_names = [member.name for member in credits.cast]
    crew_names = [member.name for member in credits.crew]
    print(f"Cast ({len(cast_names)}): {cast_names}")
    print(f"Crew ({len(crew_names)}, not auto-researched -- MVP is actors-only): {crew_names}")

    to_research = cast_names[:limit] if limit else cast_names
    parallel_client = ParallelClient()
    async with ClickHouseHandler() as handler:
        for name in to_research:
            print(f"\n--- {name} ---")
            person = await handler.find_or_research_person(parallel_client, name)
            print(person if person is not None else "Lookup/research/storage failed.")


async def discover_actors(
    tmdb_client: TMDBClient,
    seed_title: str,
    max_depth: int = etl_config.ETL_TRAVERSAL_MAX_DEPTH,
    max_actors: int = etl_config.ETL_TRAVERSAL_MAX_ACTORS,
    movies_per_actor: int = etl_config.ETL_TRAVERSAL_MOVIES_PER_ACTOR,
    cast_per_movie: int = etl_config.ETL_TRAVERSAL_CAST_PER_MOVIE,
    tmdb_concurrency: int = etl_config.ETL_TMDB_CONCURRENCY,
) -> dict[int, str]:
    """
    BFS the TMDB actor graph outward from `seed_title`: generation 1 is the seed
    movie's own (top-billed) cast; generations 2..max_depth come from `max_depth - 1`
    further actor -> other movies -> cast hops. Returns {tmdb_person_id: name} for
    every actor touched, seed cast included -- callers filter this whole dict
    against ClickHouse in one pass via ClickHouseHandler.get_new_names, there's no
    separate seed-cast path.

    Race-free by construction: each hop is two sequential asyncio.gather stages
    with every visited/budget check done in synchronous driver code between them
    (never inside a coroutine, never with an await between a check and its add) --
    so two frontier actors referencing the same not-yet-visited movie in the same
    hop can't cause that movie's cast to be fetched twice, and a single hop's own
    fan-out can't blow past max_actors before the next hop's check would catch it.
    """
    semaphore = asyncio.Semaphore(tmdb_concurrency)

    async def _bounded(coro):
        async with semaphore:
            return await coro

    def _top_billed(cast, n):
        return sorted(cast, key=lambda m: m.order if m.order is not None else 10**9)[:n]

    # Seed movie id must come from search_movie + get_movie_credits directly --
    # find_movie_credits() discards the id, which visited_movie_ids needs.
    seed_movie = await tmdb_client.search_movie(seed_title)
    if seed_movie is None:
        return {}
    seed_credits = await tmdb_client.get_movie_credits(seed_movie.id)
    if seed_credits is None:
        return {}

    visited_movie_ids = {seed_movie.id}
    visited_actor_ids: set[int] = set()
    discovered: dict[int, str] = {}

    frontier: dict[int, str] = {}
    for member in _top_billed(seed_credits.cast, cast_per_movie):
        if len(discovered) + len(frontier) >= max_actors:
            break
        frontier[member.id] = member.name
    discovered.update(frontier)
    visited_actor_ids.update(frontier)

    for _hop in range(max_depth - 1):
        if not frontier or len(discovered) >= max_actors:
            break

        actor_ids = list(frontier)
        credit_results = await asyncio.gather(
            *[_bounded(tmdb_client.get_person_movie_credits(pid)) for pid in actor_ids],
            return_exceptions=True,
        )

        # Synchronous driver code -- no `await` below until Stage B's gather.
        candidate_movie_ids: list[int] = []
        for credits in credit_results:
            if isinstance(credits, BaseException) or credits is None:
                continue
            ranked = sorted(
                credits.cast,
                key=lambda c: c.popularity if c.popularity is not None else -1.0,
                reverse=True,
            )
            for item in ranked[:movies_per_actor]:
                if item.id not in visited_movie_ids and item.id not in candidate_movie_ids:
                    candidate_movie_ids.append(item.id)
        visited_movie_ids.update(candidate_movie_ids)

        if not candidate_movie_ids:
            break

        cast_results = await asyncio.gather(
            *[_bounded(tmdb_client.get_movie_credits(mid)) for mid in candidate_movie_ids],
            return_exceptions=True,
        )

        next_frontier: dict[int, str] = {}
        for movie_credits in cast_results:
            if isinstance(movie_credits, BaseException) or movie_credits is None:
                continue
            for member in _top_billed(movie_credits.cast, cast_per_movie):
                if member.id in visited_actor_ids or member.id in next_frontier:
                    continue
                if len(discovered) + len(next_frontier) >= max_actors:
                    break
                next_frontier[member.id] = member.name

        discovered.update(next_frontier)
        visited_actor_ids.update(next_frontier)
        frontier = next_frontier

    return discovered


_DISCOVER_FLAGS = {
    "--depth": "max_depth",
    "--max-actors": "max_actors",
    "--movies-per-actor": "movies_per_actor",
    "--cast-per-movie": "cast_per_movie",
}


def _parse_discover_args(args: list[str]) -> tuple[str, dict[str, int]]:
    """
    Unlike _movie_cast_demo's single trailing --limit, `discover` takes 4
    optional flags that can appear in any position, so this pulls out every
    recognized `--flag value` pair wherever it appears and joins whatever's
    left as the title.
    """
    overrides: dict[str, int] = {}
    title_tokens: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in _DISCOVER_FLAGS and i + 1 < len(args):
            overrides[_DISCOVER_FLAGS[token]] = int(args[i + 1])
            i += 2
        else:
            title_tokens.append(token)
            i += 1
    return " ".join(title_tokens), overrides


async def _discover_demo(args: list[str]) -> None:
    """
    Graph-traversal populate: seed from one movie, BFS outward through actors'
    other movies to discover a wider cast network, then research + store every
    newly-discovered actor not already in ClickHouse.
        uv run python -m src.raphael.etl.populate discover "Inception" --depth 2 --max-actors 40
    """
    if not args:
        print("Usage: discover <title> [--depth N] [--max-actors N] [--movies-per-actor N] [--cast-per-movie N]")
        return
    title, overrides = _parse_discover_args(args)
    if not title:
        print("Usage: discover <title> [--depth N] [--max-actors N] [--movies-per-actor N] [--cast-per-movie N]")
        return

    max_depth = overrides.get("max_depth", etl_config.ETL_TRAVERSAL_MAX_DEPTH)
    max_actors = overrides.get("max_actors", etl_config.ETL_TRAVERSAL_MAX_ACTORS)
    movies_per_actor = overrides.get("movies_per_actor", etl_config.ETL_TRAVERSAL_MOVIES_PER_ACTOR)
    cast_per_movie = overrides.get("cast_per_movie", etl_config.ETL_TRAVERSAL_CAST_PER_MOVIE)

    print(f"=== Raphael: Discovering actor graph from '{title}' (depth={max_depth}, max_actors={max_actors}) ===")
    tmdb_client = TMDBClient()
    discovered = await discover_actors(
        tmdb_client, title,
        max_depth=max_depth, max_actors=max_actors,
        movies_per_actor=movies_per_actor, cast_per_movie=cast_per_movie,
    )
    if not discovered:
        print(f"No actors discovered -- check TMDB match for '{title}' and TMDB_API_KEY.")
        return
    print(f"Discovered {len(discovered)} distinct actors across the traversal.")

    # set() dedupes exact-string name collisions across different TMDB person ids;
    # it does NOT catch name variants between two new actors in this same batch --
    # see ClickHouseHandler.get_new_names' docstring for that accepted limitation.
    candidate_names = sorted(set(discovered.values()))
    parallel_client = ParallelClient()
    research_semaphore = asyncio.Semaphore(etl_config.ETL_PARALLEL_RESEARCH_CONCURRENCY)

    async def _research_and_store(handler: ClickHouseHandler, name: str) -> Optional[bool]:
        async with research_semaphore:
            dossier = await parallel_client.aresearch_person(name)
        if dossier is None:
            return None
        # Store under TMDB's own name, not whatever free-text name the research
        # agent decided to use -- TMDB is ground truth here, and it's the name
        # get_new_names already confirmed has no existing match, so a re-run
        # against the same seed will recognize this person as already stored
        # instead of inserting a second row under the research agent's variant.
        dossier.name = name
        return await handler.insert_person(dossier)

    async with ClickHouseHandler() as handler:
        new_names = await handler.get_new_names(candidate_names)
        already_cached = len(candidate_names) - len(new_names)
        print(
            f"{already_cached} already in ClickHouse, {len(new_names)} new -- "
            f"researching (concurrency={etl_config.ETL_PARALLEL_RESEARCH_CONCURRENCY})..."
        )
        results = await asyncio.gather(
            *[_research_and_store(handler, name) for name in new_names],
            return_exceptions=True,
        )

    stored = sum(1 for r in results if r is True)
    failed = len(results) - stored
    print(
        f"\n=== Discover summary ===\n"
        f"Discovered: {len(discovered)}\n"
        f"Already cached: {already_cached}\n"
        f"Newly stored: {stored}\n"
        f"Failed (research or storage -- note insert_person can partially succeed "
        f"across people/credits/collaborations and still count as failed here): {failed}"
    )


if __name__ == "__main__":
    main()
