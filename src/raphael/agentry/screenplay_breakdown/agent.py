# Import standard packages
from pathlib import Path
from typing import Any

# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI

# Import custom modules
from src.raphael.agentry.config import config
from src.raphael.agentry.screenplay_breakdown.models import Screenplay

# The system prompt lives alongside this agent
PROMPT_PATH = Path(__file__).parent / "PROMPT.md"

class ScreenplayBreakdownAgent:
    """
    Lightweight harness that parses a screenplay/script document into a
    structured Screenplay object (title + cast breakdown) using an LLM.
    """

    def __init__(self, model_id: str | None = None):
        """
        Initializes the screenplay breakdown agent.
        """
        # Define this agent's system prompt
        self.system_prompt = PROMPT_PATH.read_text()

        # Initialize the LLM (GCP creds are picked up automatically via ADC).
        # Longer timeout than other agents' -- this call consumes a whole
        # screenplay document, not a handful of already-fetched search findings.
        self.model = ChatGoogleGenerativeAI(
            model=model_id or config.SCREENPLAY_BREAKDOWN_MODEL_ID,
            vertexai=True,
            project=config.GOOGLE_CLOUD_PROJECT,
            location=config.GOOGLE_CLOUD_LOCATION,
            timeout=config.SCREENPLAY_BREAKDOWN_TIMEOUT_SECONDS,
            max_retries=config.LLM_MAX_RETRIES,
        )

        # Constrain the model to always respond with a Screenplay object
        self.structured_model = self.model.with_structured_output(Screenplay)

        return

    def invoke(self, document: str, **kwargs: Any) -> Screenplay:
        """
        Synchronously parses a screenplay document into a Screenplay object.
        """
        return self.structured_model.invoke(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": document},
            ],
            **kwargs,
        )

    async def ainvoke(self, document: str, **kwargs: Any) -> Screenplay:
        """
        Asynchronously parses a screenplay document into a Screenplay object.
        """
        return await self.structured_model.ainvoke(
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": document},
            ],
            **kwargs,
        )
