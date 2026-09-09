# Import standard packages
import os
from dotenv import load_dotenv

class Config:
    """
    Env-driven settings for Raphael's FastAPI server.
    """
    
    def __init__(self):
        """
        Load and initialize the settings.
        """
        
        load_dotenv()
        
        # Host/port the FastAPI server binds to
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))

        # GCP project whose Firebase ID tokens this API accepts
        self.GOOGLE_CLOUD_PROJECT: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")

        # Origins allowed to call this API cross-origin, as a comma-separated
        # list. Falls back to the frontend's local dev server and its deployed
        # origin so a local run needs no ALLOWED_ORIGINS in .env.
        self.ALLOWED_ORIGINS: list[str] = [
            origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()
        ] or [
            "http://localhost:5173",
            "https://raphael.saichaparala.com"
        ]

        return
    
config = Config()