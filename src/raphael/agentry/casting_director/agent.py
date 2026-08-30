# Import standard packages
import asyncio
from pathlib import Path

# Import LangGraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.screenplay_breakdown.models import Screenplay, CharacterProfile
from src.raphael.agentry.parallel.abstract import ParallelAbstractAgent
from src.raphael.agentry.parallel.models import ParallelAgentType
# PersonDossier import dropped -- only referenced by the commented-out
# enrich_candidate below; re-add it alongside re-enabling that method.
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
        Fans out one branch per character in the screenplay's cast.
        """
        return [
            Send("search_candidates", {"character": character})
            for character in state["screenplay"].cast.characters
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
        """
        findings = await self.search_agent.ainvoke(character_query(character))

        result: CandidateSearchResult = await structuring_model(CandidateSearchResult, config.CASTING_DIRECTOR_MODEL_ID).ainvoke(
            f"Extract the candidate actors from these casting search findings "
            f"for the character {character.name}: their name, a fit rationale, "
            f"and a dossier prefilled with whatever casting-relevant facts "
            f"(bio, notable roles, age/nationality/build, etc.) the findings "
            f"happen to mention. Leave dossier fields unset rather than "
            f"guessing if the findings don't support them -- this is a "
            f"best-effort prefill from search, not deep research.\n\n{findings}"
        )

        return result.candidates

    # Deep-research enrichment is disabled -- find_candidates prefills each
    # candidate's dossier from search findings alone instead (see above).
    # Left commented out, not deleted, since it depends on self.research_agent
    # (also disabled in __init__); re-enable both together to restore it.
    #
    # async def enrich_candidate(self, candidate: CastingCandidate) -> CastingCandidate:
    #     """
    #     Runs Parallel's deep-research task on a single candidate to ground
    #     their dossier in real, citable facts.
    #     """
    #     findings = await self.research_agent.ainvoke(f"Compile a casting dossier on {candidate.name}.")
    #
    #     dossier: PersonDossier = await structuring_model(PersonDossier, config.CASTING_DIRECTOR_MODEL_ID).ainvoke(
    #         f"Extract {candidate.name}'s casting dossier from this research:\n\n{findings}"
    #     )
    #
    #     return candidate.model_copy(update={"dossier": dossier})

    async def search_candidates(self, state: CharacterSearchState) -> dict:
        """
        Finds candidates for a single character, each with a best-effort
        dossier already prefilled from search alone.
        """
        character = state["character"]
        candidates = await self.find_candidates(character)

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
