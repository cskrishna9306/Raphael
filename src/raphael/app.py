# Import third-party packages
from fastapi import FastAPI, File, UploadFile

# Import custom modules
from src.raphael.agentry.orchestrator import Raphael
from src.raphael.agentry.utils import extract_text
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
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

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> Screenplay:
    """
    Runs just the screenplay breakdown step over an uploaded screenplay document.
    """
    
    # In terms of the UI flow, this will be the first endpoint that will
    # be triggered by our frontend
    content = await file.read()
    document = extract_text(file.filename, content)
    return await raphael.analyze(document)

@app.post("/recommend")
async def recommend(screenplay: Screenplay) -> RecommendationReport:
    """
    Runs the rest of the pipeline (casting, enrichment, risk assessment,
    chemistry scoring, recommendation ranking) over a Screenplay produced by
    /analyze, and returns the resulting RecommendationReport.
    """
    return await raphael.recommend(screenplay)
