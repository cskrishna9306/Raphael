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

        # Comma-separated origins allowed to call this API cross-origin (the
        # frontend's dev server and, once deployed, its real origin).
        self.ALLOWED_ORIGINS: list[str] = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        ]

        return
    
config = Config()