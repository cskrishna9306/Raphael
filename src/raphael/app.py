# Import third-party packages
from fastapi import FastAPI, File, UploadFile

# Import custom modules
from src.raphael.agentry.orchestrator import Raphael
from src.raphael.agentry.utils import extract_text
from src.raphael.recommendation.models import RecommendationReport

# Instantiate a single FastAPI server and Raphael object
app = FastAPI(title="Raphael")
raphael = Raphael()

@app.get("/health")
def health() -> dict:
    """
    Liveness probe: process is up and serving requests.
    """
    return {"status": "ok"}

@app.get("/ready")
def ready() -> dict:
    """
    Readiness probe: service can accept /recommend traffic.
    """
    return {"status": "ok"}

@app.post("/recommend")
async def recommend(file: UploadFile = File(...)) -> RecommendationReport:
    """
    Runs the full pipeline (screenplay breakdown, casting, enrichment, risk
    assessment, chemistry scoring, recommendation ranking) over an uploaded
    screenplay document (.txt or .pdf) and returns the resulting
    RecommendationReport.
    """
    content = await file.read()
    document = extract_text(file.filename, content)
    return await raphael.run_async(document)
