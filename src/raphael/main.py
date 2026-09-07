# Import third-party packages
import uvicorn

# Import custom modules
from src.raphael.config import config


def main():
    """
    Process entrypoint: boots the FastAPI app defined in app.py behind uvicorn.
    """
    uvicorn.run("src.raphael.app:app", host=config.HOST, port=config.PORT)
    
    return

if __name__ == "__main__":
    main()
