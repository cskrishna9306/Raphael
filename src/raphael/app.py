# Import standard packages
import json
from contextlib import asynccontextmanager

# Import third-party packages
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Import custom modules
from src.raphael.agentry.orchestrator import Raphael
from src.raphael.agentry.utils import extract_text
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.auth import verify_token
from src.raphael.config import config
from src.raphael.recommendation.models import (
    ClusterRecommendation,
    RecommendationReport,
    SwapPreviewRequest,
    SwapPreviewResponse,
    SwapRequest,
)

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
async def analyze(
    file: UploadFile = File(...),
    _claims: dict = Depends(verify_token),
) -> Screenplay:
    """
    Runs just the screenplay breakdown step over an uploaded screenplay
    document. Requires a Firebase ID token in the Authorization header.
    """

    # In terms of the UI flow, this will be the first endpoint that will
    # be triggered by our frontend
    content = await file.read()
    document = extract_text(file.filename, content)
    return await raphael.analyze(document)

@app.post("/recommend")
async def recommend(
    screenplay: Screenplay,
    _claims: dict = Depends(verify_token),
) -> RecommendationReport:
    """
    Runs the rest of the pipeline (casting, enrichment, risk assessment,
    chemistry scoring, recommendation ranking) over a Screenplay produced by
    /analyze, and returns the resulting RecommendationReport. Requires a
    Firebase ID token in the Authorization header.
    """
    return await raphael.recommend(screenplay)

@app.post("/recommend/stream")
async def recommend_stream(
    screenplay: Screenplay,
    _claims: dict = Depends(verify_token),
) -> StreamingResponse:
    """
    Streaming counterpart to /recommend: emits one SSE event per character
    as casting_director finishes searching for them
    (`{"type": "casting_progress", "character", "completed", "total"}`),
    then a final event carrying the same RecommendationReport /recommend
    returns (`{"type": "recommend_complete", "report"}`) -- lets the
    frontend show real per-character progress instead of a fake timed
    loader while the casting search is in flight. Requires a Firebase ID
    token in the Authorization header, same as /recommend.

    Errors surface as an in-stream `{"type": "error", "message"}` event
    rather than an HTTP error status -- by the time a failure can happen
    here, the 200 response has already started streaming, so there's no
    HTTP status left to change.
    """
    async def event_source():
        try:
            async for event in raphael.astream_recommend(screenplay):
                payload = dict(event)
                if "report" in payload:
                    payload["report"] = payload["report"].model_dump(mode="json")
                yield f"data: {json.dumps(payload)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")

@app.post("/swap")
def swap(request: SwapRequest, _claims: dict = Depends(verify_token)) -> ClusterRecommendation:
    """
    Recomputes chemistry/risk for one cluster with a single character's
    candidate substituted in, using the Roster from an earlier
    RecommendationReport -- no agents, no ClickHouse, no Parallel calls, just
    a deterministic recompute over data /recommend already produced. Requires
    a Firebase ID token in the Authorization header, same as /recommend.
    """
    risk_by_name = {assessment.name: assessment for assessment in request.roster.risk_assessments}
    try:
        cluster = raphael.chemistry_engine.score_selection(
            request.roster.casting_report, request.selections, request.reference_scores, risk_by_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return raphael.recommendation_engine.build_single(cluster, request.roster.risk_assessments)

@app.post("/swap/preview")
def swap_preview(request: SwapPreviewRequest, _claims: dict = Depends(verify_token)) -> SwapPreviewResponse:
    """
    Scores every other candidate in one character's shortlist as a
    hypothetical swap, without committing to any of them -- so the frontend
    can show each alternative's real chemistry delta and a per-co-star
    breakdown before the user picks. Same deterministic recompute as /swap,
    just over the whole shortlist instead of one chosen candidate. Requires
    a Firebase ID token in the Authorization header, same as /recommend.
    """
    risk_by_name = {assessment.name: assessment for assessment in request.roster.risk_assessments}
    previews = raphael.chemistry_engine.preview_swaps(
        request.roster.casting_report, request.selections, request.character_name, request.excluded_leads, risk_by_name
    )
    return SwapPreviewResponse(previews=previews)
