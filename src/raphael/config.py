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

        # Origins allowed to call this API cross-origin
        # Frontend's local dev server and, once deployed, its real origin
        self.ALLOWED_ORIGINS: list[str] = [
            "http://localhost:5173",
            "https://raphael.saichaparala.com"
        ]

        return
    
config = Config()