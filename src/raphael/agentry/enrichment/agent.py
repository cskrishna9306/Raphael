# Import standard packages
import asyncio
from typing import Optional

# Import LangGraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Import custom modules
from src.raphael.clickhouse.handler import ClickHouseHandler
from src.raphael.parallel.client import ParallelClient
from src.raphael.agentry.casting_director.models import CastingCandidate, CastingReport
from src.raphael.agentry.enrichment.models import (
    EnrichmentAssessment,
    EnrichmentSource,
    EnrichmentReport,
    EnrichmentState,
    CandidateEnrichmentState,
)


class EnrichmentAgent:
    """
    Given a CastingReport, fans out a parallel ClickHouse-first,
    Parallel-fallback dossier lookup per unique candidate (deduped across
    every character, since the same actor shortlisted for multiple roles
    only needs enriching once -- see CastingReport.unique_candidates) and
    returns an EnrichmentReport keyed by actor name.

    Mirrors RiskManagementAgent's shape (StateGraph, fan_out via Send, a
    build_report reduce node, async-only with a sync invoke() wrapper), but
    needs no LLM/structuring_model() call and no ParallelAbstractAgent
    sub-agent -- "research" is a direct SDK-level ParallelClient call,
    already encapsulated inside ClickHouseHandler.find_or_research_dossier.

    Unlike RiskManagementAgent's search_agent (stateless, buildable once in
    __init__), ClickHouseHandler is an async context manager wrapping a live
    MCP subprocess/session -- it can't be opened in a sync __init__. Instead,
    ainvoke() opens ONE ClickHouseHandler session for the entire graph run,
    stashes it on self._handler, and every enrich_candidate branch (which
    all run concurrently under that same ainvoke() call) reuses that single
    session -- the closest async analogue to "build once, reuse across every
    branch". Not safe to call ainvoke() twice concurrently on the same
    instance as a result -- accepted MVP limitation, see ainvoke().
    """

    def __init__(self, parallel_client: Optional[ParallelClient] = None):
        """
        Builds the enrichment graph: fan out over unique candidates, then
        per candidate look up (or research + store) a dossier, then reduce
        into an EnrichmentReport.

        ParallelClient is cheap/stateless (lazy API clients -- see
        ParallelClient.client/.async_client) so it's safe to build once
        here, same as RiskManagementAgent builds its search_agent once. The
        ClickHouseHandler is NOT built here -- see ainvoke().
        """
        self.parallel_client = parallel_client or ParallelClient()
        self._handler: Optional[ClickHouseHandler] = None

        # Initialize the graph and its nodes
        graph = StateGraph(EnrichmentState)
        graph.add_node("enrich_candidate", self.enrich_candidate)
        graph.add_node("build_report", self.build_report)

        # Add edges between the nodes
        graph.add_conditional_edges(START, self.fan_out, ["enrich_candidate"])
        graph.add_edge("enrich_candidate", "build_report")
        graph.add_edge("build_report", END)

        self.graph = graph.compile()

        return

    def fan_out(self, state: EnrichmentState) -> list[Send]:
        """
        Fans out one branch per unique candidate across the whole casting
        report -- the same actor shortlisted for multiple characters is
        enriched once, not once per character.
        """
        candidates = state["casting_report"].unique_candidates()
        return [
            Send("enrich_candidate", {"candidate": candidate})
            for candidate in candidates.values()
        ]

    def build_report(self, state: EnrichmentState) -> dict:
        """
        Assembles the final enrichment report once every candidate branch
        has finished.
        """
        return {
            "report": EnrichmentReport(
                title=state["casting_report"].title,
                assessments=state["assessments"],
            )
        }

    async def enrich(self, candidate: CastingCandidate) -> EnrichmentAssessment:
        """
        Looks up (or researches + stores) a full PersonDossier for a named
        candidate actor via the shared ClickHouseHandler session.
        """
        assert self._handler is not None, "enrich() called outside an active ainvoke() -- no open ClickHouseHandler session"

        dossier, was_cache_hit = await self._handler.find_or_research_dossier(
            self.parallel_client,
            candidate.name,
            additional_context=candidate.fit_rationale,
        )

        if dossier is None:
            return EnrichmentAssessment(name=candidate.name, dossier=None, source=EnrichmentSource.FAILED)

        source = EnrichmentSource.CACHE if was_cache_hit else EnrichmentSource.RESEARCH
        return EnrichmentAssessment(name=candidate.name, dossier=dossier, source=source)

    async def enrich_candidate(self, state: CandidateEnrichmentState) -> dict:
        """
        Enriches a single candidate's dossier.
        """
        candidate = state["candidate"]
        assessment = await self.enrich(candidate)

        return {"assessments": [assessment]}

    def invoke(self, casting_report: CastingReport) -> EnrichmentReport:
        """
        Synchronously runs the enrichment graph for a casting report.

        This is a thin wrapper around ainvoke() -- enrich_candidate (and
        everything it calls) is async-only, so graph.invoke() would raise
        `TypeError: No synchronous function provided`. Do not call this from
        inside a running event loop -- asyncio.run() raises RuntimeError
        there; call ainvoke() directly from async code instead.
        """
        return asyncio.run(self.ainvoke(casting_report))

    async def ainvoke(self, casting_report: CastingReport) -> EnrichmentReport:
        """
        Asynchronously runs the enrichment graph for a casting report.

        Opens exactly one ClickHouseHandler MCP session for the whole run,
        shared by every fan-out branch (see class docstring), and tears it
        down once the graph finishes -- success or failure -- via `async
        with`/`finally`. Not safe to call this twice concurrently on the
        same instance, since the second call's `async with` would overwrite
        self._handler mid-flight of the first.
        """
        async with ClickHouseHandler() as handler:
            self._handler = handler
            try:
                result = await self.graph.ainvoke({"casting_report": casting_report, "assessments": []})
            finally:
                self._handler = None
        return result["report"]
