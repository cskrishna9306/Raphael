import sys
import json
import asyncio
from src.raphael.parallel.client import ParallelClient
from src.raphael.clickhouse.handler import ClickHouseHandler


def main():
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


if __name__ == "__main__":
    main()

