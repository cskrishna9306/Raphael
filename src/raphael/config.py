# Import standard packages
import os
from dotenv import load_dotenv

def _parse_origins(raw: str) -> list[str]:
    """
    Splits an ALLOWED_ORIGINS value on commas or whitespace, dropping quotes
    and blanks. Tolerant on purpose -- see the ALLOWED_ORIGINS comment below.
    """
    # Quotes are stripped after splitting, so an entry that was nothing but
    # quotes drops out rather than becoming an empty allowed origin.
    cleaned = (origin.strip().strip("\"'") for origin in raw.replace(",", " ").split())
    return [origin for origin in cleaned if origin]


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

        # Origins allowed to call this API cross-origin, as a comma- (or
        # whitespace-) separated list. Falls back to the frontend's local dev
        # server and its deployed origin so a local run needs no
        # ALLOWED_ORIGINS in .env.
        #
        # Entries are unquoted before use: a deploy pipeline that quotes the
        # whole list to protect its commas can leave a stray quote welded to
        # the first origin, and an origin that doesn't match exactly is an
        # origin CORSMiddleware silently refuses -- which reads in the browser
        # as the API being down rather than as a config error.
        self.ALLOWED_ORIGINS: list[str] = _parse_origins(os.getenv("ALLOWED_ORIGINS", "")) or [
            "http://localhost:5173",
            "https://raphael.saichaparala.com"
        ]

        return
    
config = Config()