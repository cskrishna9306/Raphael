# Import standard packages
import os
from dotenv import load_dotenv


class Config:
    """
    Env-driven settings for all agentic architecture.
    """

    def __init__(self):
        """
        Initialize the settings.
        """
        
        # Again load the .env file per object creation
        load_dotenv()

        self.GOOGLE_APPLICATION_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION")

        # The Vertex AI model ID to use
        self.MODEL_ID: str = "gemini-3.5-flash-lite"

        # The Vertex AI model ID used by the screenplay breakdown agent
        # NOTE: Will probably need to use a heavy-weight model for this
        # since we will be consuming the entire screenplay document and running
        # inference on top of it
        self.SCREENPLAY_BREAKDOWN_MODEL_ID: str = "gemini-3.5-flash-lite"

        # The Vertex AI model ID used by the casting_director agent
        self.CASTING_DIRECTOR_MODEL_ID: str = "gemini-3.5-flash-lite"

        # The Vertex AI model ID used by the risk_management agent
        self.RISK_MANAGEMENT_MODEL_ID: str = "gemini-3.5-flash-lite"

        return


config = Config()
