# Import standard packages
import asyncio
from pathlib import Path

# Import LangGraph packages
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.casting_director.models import CastingCandidate, CastingReport
from src.raphael.agentry.parallel.abstract import ParallelAbstractAgent
from src.raphael.agentry.parallel.models import ParallelAgentType
from src.raphael.agentry.risk_management.models import (
    RiskAssessment,
    RiskReport,
    RiskManagementState,
    CandidateRiskState,
)
from src.raphael.agentry.utils import structuring_model, candidate_risk_query

# Each stage's system prompt lives in its own markdown file
SEARCH_PROMPT = (Path(__file__).parent / "SEARCH_PROMPT.md").read_text()

class RiskManagementAgent:
    """
    Given a CastingReport, fans out a parallel risk-research search per
    unique candidate actor (deduped across every character, since the same
    actor shortlisted for multiple roles only needs researching once -- see
    CastingReport.unique_candidates) and returns a RiskReport keyed by actor
    name.

    Mirrors CastingDirectorAgent's shape: async-only, fan_out via Send, a
    per-branch async node, a build_report reduce node. Can only be driven
    through ainvoke()/astream() -- see invoke()'s docstring.
    """

    def __init__(self):
        """
        Builds the risk_management graph: fan out over unique candidates,
        then per candidate search for and structure a risk assessment, then
        reduce into a RiskReport.

        The Parallel search sub-agent is built once here and reused across
        every candidate branch -- its system prompt is fixed, so there's
        nothing per-call to rebuild.
        """
        # Instantiate the Parallel sub-agent
        self.search_agent = ParallelAbstractAgent(system_prompt=SEARCH_PROMPT, type=ParallelAgentType.SEARCH)

        # Initialize the graph and its nodes
        graph = StateGraph(RiskManagementState)
        graph.add_node("assess_candidate", self.assess_candidate)
        graph.add_node("build_report", self.build_report)

        # Add edges between the nodes
        graph.add_conditional_edges(START, self.fan_out, ["assess_candidate"])
        graph.add_edge("assess_candidate", "build_report")
        graph.add_edge("build_report", END)

        self.graph = graph.compile()

        return

    def fan_out(self, state: RiskManagementState) -> list[Send]:
        """
        Fans out one branch per unique candidate across the whole casting
        report -- the same actor shortlisted for multiple characters is
        researched once, not once per character.
        """
        candidates = state["casting_report"].unique_candidates()
        return [
            Send("assess_candidate", {"candidate": candidate})
            for candidate in candidates.values()
        ]

    def build_report(self, state: RiskManagementState) -> dict:
        """
        Assembles the final risk report once every candidate branch has
        finished.
        """
        return {
            "report": RiskReport(
                title=state["casting_report"].title,
                assessments=state["assessments"],
            )
        }

    async def assess(self, candidate: CastingCandidate) -> RiskAssessment:
        """
        Searches for real, citable controversy/legal/reputational signal
        about a named candidate actor, and structures the findings into a
        RiskAssessment.
        """
        findings = await self.search_agent.ainvoke(candidate_risk_query(candidate))

        assessment: RiskAssessment = await structuring_model(RiskAssessment, config.RISK_MANAGEMENT_MODEL_ID).ainvoke(
            f"Extract a risk assessment for {candidate.name} from these search "
            f"findings: an overall risk_level (low/medium/high), a short "
            f"rationale, and any specific flags (category + description + "
            f"source) the findings support. If nothing concerning turns up, "
            f"return risk_level=low with an empty flags list and a rationale "
            f"noting no red flags were found -- do not invent flags.\n\n{findings}"
        )

        # Force the join key rather than trust the model to echo it back
        # verbatim (e.g. it could paraphrase/normalize the name) -- this is
        # what downstream consumers join RiskAssessment back onto
        # CastingCandidate.name by.
        return assessment.model_copy(update={"name": candidate.name})

    async def assess_candidate(self, state: CandidateRiskState) -> dict:
        """
        Assesses a single candidate's risk profile.
        """
        candidate = state["candidate"]
        assessment = await self.assess(candidate)

        return {"assessments": [assessment]}

    def invoke(self, casting_report: CastingReport) -> RiskReport:
        """
        Synchronously runs the risk_management graph for a casting report.

        This is a thin wrapper around ainvoke() -- assess_candidate (and
        everything it calls) is async-only, so graph.invoke() would raise
        `TypeError: No synchronous function provided`. Do not call this from
        inside a running event loop -- asyncio.run() raises RuntimeError
        there; call ainvoke() directly from async code instead.
        """
        return asyncio.run(self.ainvoke(casting_report))

    async def ainvoke(self, casting_report: CastingReport) -> RiskReport:
        """
        Asynchronously runs the risk_management graph for a casting report.
        """
        result = await self.graph.ainvoke({"casting_report": casting_report, "assessments": []})
        return result["report"]
