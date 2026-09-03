import sys
import json
import asyncio
from src.raphael.parallel.client import ParallelClient
from src.raphael.clickhouse.handler import ClickHouseHandler


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "roster":
        return asyncio.run(_search_roster_demo(sys.argv[2:]))

    if len(sys.argv) > 1 and sys.argv[1] == "add-person":
        return asyncio.run(_add_person_demo(sys.argv[2:]))

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
        uv run python -m src.raphael.main roster "Christopher Nolan" "Cillian Murphy"
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
        uv run python -m src.raphael.main add-person "Some Name" "Christopher Nolan"
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


if __name__ == "__main__":
    main()

