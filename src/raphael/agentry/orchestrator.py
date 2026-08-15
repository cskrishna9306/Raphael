# Import LangChain packages
from langchain_google_genai import ChatGoogleGenerativeAI

# Import custom packages
from src.raphael.agentry.config import config


class Raphael:
    """
    Stub class to represent the main orchestrator.
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


