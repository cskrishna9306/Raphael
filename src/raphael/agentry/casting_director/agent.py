# Import standard packages
import asyncio
from pathlib import Path

# Import LangGraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.models import (
    Screenplay,
    CharacterProfile,
    CastingCandidate,
    CastingCharacter,
    CastingReport,
)
from src.raphael.agentry.parallel.abstract import ParallelAbstractAgent
from src.raphael.agentry.parallel.models import ParallelAgentType, PersonDossier
from src.raphael.agentry.casting_director.models import (
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
    search + dossier research per character and returns a CastingReport.

    search_candidates (and everything it calls) is async-only: every
    character branch, and every candidate's dossier research within a
    branch, needs to run concurrently. Because of that this graph can only
    be *driven* through ainvoke()/astream() -- see invoke()'s docstring.
    """

    def __init__(self):
        """
        Builds the casting_director graph: fan out over characters, then
        per character search for and research candidates, then reduce into
        a CastingReport.

        The Parallel search and research sub-agents are built once here and
        reused across every character branch and every candidate -- their
        system prompts are fixed, so there's nothing per-call to rebuild.
        """
        # Instantiate the 2 Parallel sub-agents
        self.search_agent = ParallelAbstractAgent(system_prompt=SEARCH_PROMPT, type=ParallelAgentType.SEARCH)
        self.research_agent = ParallelAbstractAgent(system_prompt=RESEARCH_PROMPT, type=ParallelAgentType.RESEARCH)

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
        structures the findings into name + fit rationale (no dossier yet).
        """
        findings = await self.search_agent.ainvoke(character_query(character))

        result: CandidateSearchResult = await structuring_model(CandidateSearchResult, config.CASTING_DIRECTOR_MODEL_ID).ainvoke(
            f"Extract the candidate actors -- name and fit rationale only, no "
            f"dossier -- from these casting search findings for the character "
            f"{character.name}:\n\n{findings}"
        )

        return result.candidates

    async def enrich_candidate(self, candidate: CastingCandidate) -> CastingCandidate:
        """
        Runs Parallel's deep-research task on a single candidate to ground
        their dossier in real, citable facts.
        """
        findings = await self.research_agent.ainvoke(f"Compile a casting dossier on {candidate.name}.")

        dossier: PersonDossier = await structuring_model(PersonDossier, config.CASTING_DIRECTOR_MODEL_ID).ainvoke(
            f"Extract {candidate.name}'s casting dossier from this research:\n\n{findings}"
        )

        return candidate.model_copy(update={"dossier": dossier})

    async def search_candidates(self, state: CharacterSearchState) -> dict:
        """
        Finds candidates for a single character, then researches every
        candidate's dossier concurrently via asyncio.gather.
        """
        character = state["character"]
        candidates = await self.find_candidates(character)

        # Perform deep research analysis on each candidate concurrently!
        # Most time-intensive part
        enriched_candidates = await asyncio.gather(
            *(self.enrich_candidate(candidate) for candidate in candidates)
        )

        return {
            "castings": [
                CastingCharacter(
                    character=character,
                    candidates=list(enriched_candidates)
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
