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

    ClickHouseHandler is an async context manager wrapping a live MCP
    subprocess/session, so it can't be opened in a sync __init__. There are
    two ways to supply one, both ending with self._handler set to an
    OPEN handler before enrich_candidate branches run:

    - Preferred (this is what Raphael/app.py does): pass an already-open
      `clickhouse_handler` (opened once, at application startup, by
      app.py's lifespan handler -- see orchestrator.py) into __init__. Every
      ainvoke() call then just reuses that one long-lived session -- no
      per-request MCP subprocess spin-up or ensure_schema() re-run, and
      it's safe to call ainvoke() concurrently since no lifecycle is being
      managed per call.
    - Fallback (standalone use, e.g. the README smoke test, with no handler
      injected): ainvoke() opens and tears down its own ClickHouseHandler
      session for that one call. Not safe to call ainvoke() twice
      concurrently on the same instance in this mode, since the second
      call's `async with` would overwrite self._handler mid-flight of the
      first.
    """

    def __init__(
        self,
        parallel_client: Optional[ParallelClient] = None,
        clickhouse_handler: Optional[ClickHouseHandler] = None,
    ):
        """
        Builds the enrichment graph: fan out over unique candidates, then
        per candidate look up (or research + store) a dossier, then reduce
        into an EnrichmentReport.

        ParallelClient is cheap/stateless (lazy API clients -- see
        ParallelClient.client/.async_client) so it's safe to build once
        here, same as RiskManagementAgent builds its search_agent once.

        clickhouse_handler, if given, is assumed to already be open (or
        about to be opened externally before ainvoke() runs) and is reused
        for the lifetime of this agent -- see class docstring. If omitted,
        ainvoke() falls back to opening/closing its own session per call.
        """
        self.parallel_client = parallel_client or ParallelClient()
        self._owns_handler = clickhouse_handler is None
        self._handler: Optional[ClickHouseHandler] = clickhouse_handler

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

        If a clickhouse_handler was injected at construction (see class
        docstring), it's already open and reused as-is -- no session
        open/close here, safe to call concurrently. Otherwise (standalone
        use), opens exactly one ClickHouseHandler MCP session for this run,
        shared by every fan-out branch, and tears it down once the graph
        finishes -- success or failure -- via `async with`/`finally`. Not
        safe to call this twice concurrently on the same instance in that
        mode, since the second call's `async with` would overwrite
        self._handler mid-flight of the first.
        """
        if not self._owns_handler:
            assert self._handler is not None, "EnrichmentAgent given no clickhouse_handler and none was injected before ainvoke()"
            result = await self.graph.ainvoke({"casting_report": casting_report, "assessments": []})
            return result["report"]

        async with ClickHouseHandler() as handler:
            self._handler = handler
            try:
                result = await self.graph.ainvoke({"casting_report": casting_report, "assessments": []})
            finally:
                self._handler = None
        return result["report"]
