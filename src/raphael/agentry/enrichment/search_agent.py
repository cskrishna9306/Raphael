# Import standard packages
from pathlib import Path
from typing import Optional

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.parallel.abstract import ParallelAbstractAgent
from src.raphael.agentry.parallel.models import ParallelAgentType, PersonDossier
from src.raphael.agentry.utils import structuring_model

# The system prompt lives alongside this agent
SEARCH_PROMPT = (Path(__file__).parent / "SEARCH_PROMPT.md").read_text()


class PersonSearchAgent:
    """
    Shallow, live-Parallel-search-based PersonDossier builder -- the deep-research-free
    alternative to ParallelClient.aresearch_person, used only by EnrichmentAgent on a
    ClickHouse cache miss. Mirrors the exact shallow-search-and-structure pattern already
    used by CastingDirectorAgent._search_and_structure and RiskManagementAgent.assess: one
    Parallel search call, then one Gemini call to structure the findings.

    Deliberately not a deep-research call -- report whatever a single search pass turns up,
    leave the rest unset. The etl/populate.py CLI tools are the only place deep research
    (ParallelClient.aresearch_person) still happens.
    """

    def __init__(self):
        """
        Builds the shallow search sub-agent once, reused across every research() call --
        its system prompt is fixed, so there's nothing per-call to rebuild.
        """
        self.search_agent = ParallelAbstractAgent(system_prompt=SEARCH_PROMPT, type=ParallelAgentType.SEARCH)

    async def research(self, name: str, additional_context: Optional[str] = None) -> Optional[PersonDossier]:
        """
        Searches for documented facts about `name` and structures the findings into a
        best-effort PersonDossier. Returns None if the search or structuring step fails --
        never raises, so a single failed lookup doesn't take down the whole enrichment fan-out.
        """
        query = f"Person: {name}" + (f"\nContext: {additional_context}" if additional_context else "")

        try:
            findings = await self.search_agent.ainvoke(query)
            return await structuring_model(PersonDossier, config.ENRICHMENT_MODEL_ID).ainvoke(
                f"Extract a casting dossier for {name} from these search findings -- "
                f"leave fields unset rather than guessing if they aren't supported.\n\n{findings}"
            )
        except Exception as e:
            print(f"[PersonSearchAgent] Error researching '{name}': {e}")
            return None
