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

        # Minimum candidates find_candidates tries to secure per character (even minor
        # roles), so every character has real alternatives for the frontend's swap picker
        self.CASTING_DIRECTOR_MIN_CANDIDATES: int = 3

        # LEAD roles get a bigger target -- ChemistryEngine's cluster search and the
        # frontend's swap picker can only ever be as diverse as the candidate pool they
        # draw from, and leads are exactly where users want real alternatives, not just
        # the same ~3 names in every cluster
        self.CASTING_DIRECTOR_MIN_CANDIDATES_LEAD: int = 6

        # The Vertex AI model ID used by the risk_management agent
        self.RISK_MANAGEMENT_MODEL_ID: str = "gemini-3.5-flash-lite"

        # The Vertex AI model ID used by the enrichment agent's shallow-search fallback
        self.ENRICHMENT_MODEL_ID: str = "gemini-3.5-flash-lite"
        
        # Set of supported documents that we can read
        self.SUPPORTED_EXTENSIONS: set[str] = (".txt", ".pdf")

        return

config = Config()
