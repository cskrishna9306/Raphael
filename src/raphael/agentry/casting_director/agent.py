# Import standard packages
import asyncio
from pathlib import Path
from typing import AsyncIterator

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

        A character with too few candidates sinks both the chemistry search
        (see ChemistryEngine.search_clusters) and the frontend's swap picker,
        which needs real alternatives to offer for every role -- so a first
        pass short of the target gets one retry with a broadened query before
        it's accepted, the same way a fully empty pass always did. LEAD roles
        target a bigger pool than supporting/minor ones: with only ~3
        candidates to choose from, every cluster and every swap picker ends
        up offering the same handful of names regardless of how the search
        or cluster diversity logic works downstream -- real variety has to
        start with a real pool. This is for named/principal characters only
        (BACKGROUND/EXTRA never reach here, see fan_out), where a thin result
        is more likely search under-reaching than a genuine "only one real
        actor fits this" case.
        """
        target = config.CASTING_DIRECTOR_MIN_CANDIDATES_LEAD if character.role_presence == RolePresence.LEAD else config.CASTING_DIRECTOR_MIN_CANDIDATES
        candidates = await self.search_and_structure(character_query(character), character.name)

        if len(candidates) < target:
            broadened_query = character_query(character) + (
                "\n\nYour first search found too few solid candidates for this description "
                f"(need at least {target}, this role needs real, distinct alternatives to "
                "choose between). Broaden your search and name more real, working actors who "
                "plausibly fit the character's role size, gender, and general type, even if "
                "the match isn't exact -- only report fewer than that if truly no other real "
                "actor search result supports even a loose fit."
            )
            broadened = await self.search_and_structure(broadened_query, character.name)
            # Broadened pass adds to, rather than replaces, the first pass's finds --
            # a broader query shouldn't cost us candidates the tighter one already found.
            seen = {candidate.name for candidate in candidates}
            candidates = candidates + [c for c in broadened if c.name not in seen]

        return candidates

    async def search_and_structure(self, query: str, character_name: str) -> list[CastingCandidate]:
        """
        Runs one search + structuring pass for a character and returns
        whatever candidates it extracts (possibly none).

        `query` is the same character_query(character) text used for the web
        search above, so it already carries the character's role size,
        gender, age range, description, and traits -- passed through to the
        structuring step too so fit_score has an actual character to judge
        the actor's real-world type/persona against, not just the actor's
        own search findings in isolation.
        """
        findings = await self.search_agent.ainvoke(query)

        result: CandidateSearchResult = await structuring_model(CandidateSearchResult, config.CASTING_DIRECTOR_MODEL_ID).ainvoke(
            f"Extract the candidate actors from these casting search findings "
            f"for the character {character_name}: their name, a fit rationale, "
            f"a fit_score (0-1) for how well their real-world type/persona -- not "
            f"just their age/gender fit, but their general public persona, the "
            f"kinds of characters they're known for playing, range -- matches this "
            f"specific character's traits and description below, and a dossier "
            f"prefilled with whatever casting-relevant facts (bio, notable roles, "
            f"age/nationality/build, etc.) the findings happen to mention. Leave "
            f"dossier fields unset rather than guessing if the findings don't "
            f"support them -- this is a best-effort prefill from search, not deep "
            f"research.\n\nCharacter description:\n{query}\n\nSearch findings:\n{findings}"
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

    async def astream_progress(self, screenplay: Screenplay) -> AsyncIterator[dict]:
        """
        Streams one event per character as their candidate search finishes,
        then a final event carrying the full CastingReport -- fan_out
        dispatches one independent search_candidates branch per character,
        and LangGraph's "updates" stream mode surfaces each branch's
        completion as soon as it finishes rather than waiting for the whole
        fan-out (confirmed live: completions arrive spread out over the full
        run, not bunched at the end), so this gives the frontend real
        per-character progress instead of a fake timed loader.
        """
        total = len(self.fan_out({"screenplay": screenplay, "castings": []}))
        completed = 0
        castings: list[CastingCharacter] = []

        async for update in self.graph.astream({"screenplay": screenplay, "castings": []}, stream_mode="updates"):
            node_output = update.get("search_candidates")
            if node_output is None:
                continue
            for casting in node_output["castings"]:
                completed += 1
                castings.append(casting)
                yield {"type": "casting_progress", "character": casting.character.name, "completed": completed, "total": total}

        yield {"type": "casting_complete", "report": CastingReport(title=screenplay.title, castings=castings)}
