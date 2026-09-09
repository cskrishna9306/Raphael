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

        # Bounds every Vertex AI chat call. Without an explicit timeout, a stalled
        # connection (e.g. a transient network drop reaching Google's OAuth token
        # endpoint) can hang far longer than a single request should before even
        # attempting a retry.
        self.LLM_TIMEOUT_SECONDS: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

        # ChatGoogleGenerativeAI defaults to 6 retries with backoff -- reasonable in
        # isolation, but combined with dozens of candidates fanning out concurrently
        # (see MAX_CONCURRENT_CANDIDATES below), that default can turn one flaky
        # connection into a very long wait before it's even reflected as a real
        # failure. Trimmed down for a snappier, still-resilient interactive path.
        self.LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))

        # ScreenplayBreakdownAgent consumes a whole document in one call (see its own
        # NOTE above) rather than a handful of already-fetched search findings, so it
        # gets a longer timeout than the general LLM_TIMEOUT_SECONDS above.
        self.SCREENPLAY_BREAKDOWN_TIMEOUT_SECONDS: float = float(os.getenv("SCREENPLAY_BREAKDOWN_TIMEOUT_SECONDS", "120"))

        # Caps how many candidates EnrichmentAgent/RiskManagementAgent/
        # CastingDirectorAgent process at once (LangGraph's `max_concurrency` config).
        # A large cast can otherwise fan out to dozens of simultaneous Vertex
        # AI/Parallel/ClickHouse connections at once -- exactly the kind of
        # self-inflicted load that turns a handful of real transient failures into a
        # flood of them (seen live: a burst of "Connection pool is full" /
        # OAuth-token connection-refused errors during a large-cast run).
        self.MAX_CONCURRENT_CANDIDATES: int = int(os.getenv("MAX_CONCURRENT_CANDIDATES", "10"))

        return

config = Config()
