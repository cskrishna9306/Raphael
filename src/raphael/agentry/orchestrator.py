# Import standard packages
import asyncio

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI

# Import custom packages
from src.raphael.agentry.config import config
from src.raphael.agentry.screenplay_breakdown import ScreenplayBreakdownAgent
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.agentry.casting_director import CastingDirectorAgent
from src.raphael.agentry.enrichment import EnrichmentAgent
from src.raphael.agentry.risk_management import RiskManagementAgent
from src.raphael.chemistry.engine import ChemistryEngine
from src.raphael.recommendation.engine import RecommendationEngine
from src.raphael.recommendation.models import RecommendationReport


class Raphael:
    """
    Main orchestrator.
    """

    def __init__(self, model_id: str | None = config.MODEL_ID):
        """
        Initialize the orchestrator.
        """
        # GCP creds are picked up automatically via ADC
        self.llm = ChatGoogleGenerativeAI(
            model=model_id,
            vertexai=True,
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
        )

        # Built once and reused across every run, same convention
        # CastingDirectorAgent follows for its own sub-agent(s). All are
        # cheap to construct (no heavy state) -- EnrichmentAgent's
        # ClickHouseHandler MCP session is opened per ainvoke() call, not
        # here, see EnrichmentAgent's docstring.
        self.screenplay_breakdown_agent = ScreenplayBreakdownAgent()
        self.casting_director_agent = CastingDirectorAgent()
        self.enrichment_agent = EnrichmentAgent()
        self.risk_management_agent = RiskManagementAgent()
        self.chemistry_engine = ChemistryEngine()
        self.recommendation_engine = RecommendationEngine()

        return

    def run(self, input: str) -> str:
        """
        Invokes the model synchronously w/o streaming.
        """
        try:
            # Call the model
            # This is a blocking action
            response = self.llm.invoke(input)

            return response.content

        except Exception as e:
            # Catch any unforseen errors
            # Not sure if we need to re-raise the exception here
            print(f"Error: Ran into trouble while invoking the LLM: {e}")

        return ""

    async def analyze(self, document: str) -> Screenplay:
        """
        Runs just the breakdown step over a raw screenplay document.
        """
        # In terms of the UI flow, this will be the first endpoint that will
        # be triggered by our frontend
        return await self.screenplay_breakdown_agent.ainvoke(document)

    async def recommend(self, screenplay: Screenplay) -> RecommendationReport:
        """
        Runs the rest of the pipeline over an already-broken-down screenplay from the /analyze endpoint.
        """
        casting_report = await self.casting_director_agent.ainvoke(screenplay)

        # Enrichment and risk assessment are independent hence ran concurrently!
        enrichment_report, risk_report = await asyncio.gather(
            self.enrichment_agent.ainvoke(casting_report),
            self.risk_management_agent.ainvoke(casting_report),
        )

        # Upgrade each candidate's shallow, search-prefilled dossier to the fuller
        # researched/cached one before scoring chemistry, so shared-credit scoring sees
        # full filmography/collaborators data. The raw EnrichmentReport is fully absorbed
        # here, so it isn't returned separately.
        enriched_casting_report = enrichment_report.merge_into(casting_report)
        chemistry_report = self.chemistry_engine.invoke(enriched_casting_report)
        recommendations = self.recommendation_engine.invoke(chemistry_report, risk_report)

        return recommendations


