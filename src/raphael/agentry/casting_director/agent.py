# Import standard packages
import asyncio
from pathlib import Path

# Import LangGraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.screenplay_breakdown.models import Screenplay, CharacterProfile, RolePresence
from src.raphael.agentry.parallel.abstract import ParallelAbstractAgent
from src.raphael.agentry.parallel.models import ParallelAgentType
from src.raphael.tmdb.client import TMDBClient
from src.raphael.agentry.casting_director.models import (
    CastingCandidate,
    CastingCharacter,
    CastingReport,
    CastingDirectorState,
    CharacterSearchState,
    CandidateSearchResult,
)
from src.raphael.agentry.utils import structuring_model, character_query

# Each stage's system prompt lives in its own markdown file
SEARCH_PROMPT = (Path(__file__).parent / "SEARCH_PROMPT.md").read_text()
RESEARCH_PROMPT = (Path(__file__).parent / "RESEARCH_PROMPT.md").read_text()

class CastingDirectorAgent:
    """
    Given a screenplay's cast breakdown, fans out a parallel candidate
    search per character and returns a CastingReport. Each candidate's
    dossier is prefilled best-effort from search findings alone -- no
    separate deep-research call (see find_candidates/enrich_candidate).

    search_candidates (and everything it calls) is async-only: every
    character branch needs to run concurrently. Because of that this graph
    can only be *driven* through ainvoke()/astream() -- see invoke()'s
    docstring.
    """

    def __init__(self):
        """
        Builds the casting_director graph: fan out over characters, then
        per character search for and research candidates, then reduce into
        a CastingReport.

        The Parallel search sub-agent is built once here and reused across
        every character branch -- its system prompt is fixed, so there's
        nothing per-call to rebuild.

        The Parallel research sub-agent is disabled for now (see
        enrich_candidate) -- find_candidates prefills whatever dossier
        fields it can straight from search findings instead. Left commented
        out, not deleted, so deep-research enrichment is a one-line revert
        away if we want it back.
        """
        # Instantiate the Parallel sub-agent(s)
        self.search_agent = ParallelAbstractAgent(system_prompt=SEARCH_PROMPT, type=ParallelAgentType.SEARCH)
        # self.research_agent = ParallelAbstractAgent(system_prompt=RESEARCH_PROMPT, type=ParallelAgentType.RESEARCH)

        # Headshot lookup for candidates
        self.tmdb_client = TMDBClient()

        # Initialize the graph and its nodes
        graph = StateGraph(CastingDirectorState)
        graph.add_node("search_candidates", self.search_candidates)
        graph.add_node("build_report", self.build_report)

        # Add edges between the nodes
        graph.add_conditional_edges(START, self.fan_out, ["search_candidates"])
        graph.add_edge("search_candidates", "build_report")
        graph.add_edge("build_report", END)

        self.graph = graph.compile()

        return

    def fan_out(self, state: CastingDirectorState) -> list[Send]:
        """
        Fans out one branch per named/principal character in the screenplay's cast.
        """
        
        # BACKGROUND and EXTRA characters are skipped -- they aren't cast
        # with a named actor in practice
        
        return [
            Send("search_candidates", {"character": character})
            for character in state["screenplay"].cast.characters
            if character.role_presence not in (RolePresence.BACKGROUND, RolePresence.EXTRA)
        ]

    def build_report(self, state: CastingDirectorState) -> dict:
        """
        Assembles the final casting report once every character branch has
        finished.
        """
        return {
            "report": CastingReport(
                title=state["screenplay"].title,
                castings=state["castings"]
            )
        }

    async def find_candidates(self, character: CharacterProfile) -> list[CastingCandidate]:
        """
        Searches for real actors who could plausibly play a character, and
        structures the findings into name + fit rationale + a best-effort
        dossier prefilled from whatever the search findings happen to
        surface (no deep research call -- see enrich_candidate).

        A character with zero candidates sinks the entire report downstream
        (see ChemistryEngine.search_clusters), so an empty first pass gets
        one retry with a broadened query before it's accepted -- this is for
        named/principal characters only (BACKGROUND/EXTRA never reach here,
        see fan_out) where an empty result is more likely search flakiness
        than a genuine "no real actor fits this" case.
        """
        candidates = await self.search_and_structure(character_query(character), character.name)

        if not candidates:
            broadened_query = character_query(character) + (
                "\n\nYour first search found no solid candidates for this description. "
                "Broaden your search and name the best real, working actor who plausibly "
                "fits the character's role size, gender, and general type, even if the "
                "match isn't exact -- only decline again if truly no real actor search "
                "result supports even a loose fit."
            )
            candidates = await self.search_and_structure(broadened_query, character.name)

        return candidates

    async def search_and_structure(self, query: str, character_name: str) -> list[CastingCandidate]:
        """
        Runs one search + structuring pass for a character and returns
        whatever candidates it extracts (possibly none).
        """
        findings = await self.search_agent.ainvoke(query)

        result: CandidateSearchResult = await structuring_model(CandidateSearchResult, config.CASTING_DIRECTOR_MODEL_ID).ainvoke(
            f"Extract the candidate actors from these casting search findings "
            f"for the character {character_name}: their name, a fit rationale, "
            f"and a dossier prefilled with whatever casting-relevant facts "
            f"(bio, notable roles, age/nationality/build, etc.) the findings "
            f"happen to mention. Leave dossier fields unset rather than "
            f"guessing if the findings don't support them -- this is a "
            f"best-effort prefill from search, not deep research.\n\n{findings}"
        )

        return result.candidates

    async def attach_headshots(self, candidates: list[CastingCandidate]) -> list[CastingCandidate]:
        """
        Augment our current list of CastingCandidates w/ their respective headshot URLs.
        """
        headshot_urls = await asyncio.gather(
            *(self.tmdb_client.find_headshot_url(candidate.name) for candidate in candidates)
        )
        for candidate, headshot_url in zip(candidates, headshot_urls):
            candidate.headshot_url = headshot_url
        return candidates

    async def search_candidates(self, state: CharacterSearchState) -> dict:
        """
        Finds candidates for a single character, each with a best-effort
        dossier already prefilled from search alone.
        """
        character = state["character"]

        # Ignores a Parallel search call if the user provides custom actors of their choice
        if character.preferred_actor:
            candidates = [
                CastingCandidate(
                    name=character.preferred_actor,
                    fit_rationale="User-specified casting choice.",
                )
            ]
        else:
            candidates = await self.find_candidates(character)

        candidates = await self.attach_headshots(candidates)

        # NOTE: Moved the deep research enrichment agent to exist as its own agent
        # Deep-research enrichment disabled -- see enrich_candidate above.
        # enriched_candidates = await asyncio.gather(
        #     *(self.enrich_candidate(candidate) for candidate in candidates)
        # )

        return {
            "castings": [
                CastingCharacter(
                    character=character,
                    candidates=candidates
                )
            ]
        }

    def invoke(self, screenplay: Screenplay) -> CastingReport:
        """
        Synchronously runs the casting_director graph for a screenplay.

        This is a thin wrapper around ainvoke() -- search_candidates (and
        everything it calls) is async-only, so graph.invoke() would raise
        `TypeError: No synchronous function provided`. Do not call this from
        inside a running event loop -- asyncio.run() raises RuntimeError
        there; call ainvoke() directly from async code instead.
        """
        return asyncio.run(self.ainvoke(screenplay))

    async def ainvoke(self, screenplay: Screenplay) -> CastingReport:
        """
        Asynchronously runs the casting_director graph for a screenplay.
        """
        result = await self.graph.ainvoke({"screenplay": screenplay, "castings": []})
        return result["report"]
