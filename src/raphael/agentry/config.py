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

        return


config = Config()
