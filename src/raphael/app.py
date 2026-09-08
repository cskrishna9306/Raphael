# Import standard packages
from contextlib import asynccontextmanager

# Import third-party packages
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Import custom modules
from src.raphael.agentry.orchestrator import Raphael
from src.raphael.agentry.utils import extract_text
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.config import config
from src.raphael.recommendation.models import RecommendationReport

raphael = Raphael()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Opens raphael's ClickHouseHandler MCP session once for the life of the
    process (spinning up the MCP subprocess and running ensure_schema()
    exactly once, instead of per /recommend request -- see
    EnrichmentAgent/ClickHouseHandler docstrings), and tears it down on
    shutdown.
    """
    async with raphael.clickhouse_handler:
        yield

# Instantiate a single FastAPI server
app = FastAPI(title="Raphael", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
