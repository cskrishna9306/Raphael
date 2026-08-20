import sys
import json
from src.raphael.parallel.client import ParallelClient


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
            print(f"  - {c.name} ({c.role}): {c.relationship_sentiment} on {', '.join(c.shared_projects)}")
            if c.chemistry_notes:
                print(f"    Notes: {c.chemistry_notes}")
        print(f"\nPersonality & Style:")
        print(f"  Working Style: {dossier.personality.working_style}")
        print(f"  Acclaim: {', '.join(dossier.personality.critical_acclaim[:3])}")
    else:
        print("No dossier returned or research failed.")


if __name__ == "__main__":
    main()

