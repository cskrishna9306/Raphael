# Import third-party packages
from fastapi import FastAPI

# Import custom modules
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.orchestrator import Raphael
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
async def recommend(casting_report: CastingReport) -> RecommendationReport:
    """
    Runs the post-casting pipeline (enrichment, risk assessment, chemistry
    scoring, recommendation ranking) over a draft CastingReport and returns
    the resulting RecommendationReport.
    """
    return await raphael.run_async(casting_report)
