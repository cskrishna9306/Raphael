# Import standard packages
import asyncio

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI

# Import custom packages
from src.raphael.agentry.config import config
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.enrichment import EnrichmentAgent
from src.raphael.agentry.risk_management import RiskManagementAgent
from src.raphael.agentry.risk_management.models import RiskReport
from src.raphael.chemistry.engine import ChemistryEngine
from src.raphael.chemistry.models import ChemistryReport


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
        # CastingDirectorAgent follows for its own sub-agent(s). All three
        # are cheap to construct (no heavy state) -- EnrichmentAgent's
        # ClickHouseHandler MCP session is opened per ainvoke() call, not
        # here, see EnrichmentAgent's docstring.
        self.enrichment_agent = EnrichmentAgent()
        self.risk_management_agent = RiskManagementAgent()
        self.chemistry_engine = ChemistryEngine()

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

    async def run_async(self, casting_report: CastingReport) -> tuple[CastingReport, ChemistryReport, RiskReport]:
        """
        Runs the post-casting pipeline over a draft CastingReport.
        Async-only, same as its sub-agents.
        """
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
        
        return enriched_casting_report, chemistry_report, risk_report


