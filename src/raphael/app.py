# Import standard packages
import traceback
from contextlib import asynccontextmanager

# Import third-party packages
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware

# Import custom modules
from src.raphael.agentry.orchestrator import Raphael
from src.raphael.agentry.utils import extract_text
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.auth import verify_token
from src.raphael.config import config
from src.raphael.history.models import Project, ProjectSummary
from src.raphael.history.store import HistoryStore, ProjectNotFoundError
from src.raphael.recommendation.models import RecommendationReport

raphael = Raphael()
history = HistoryStore()

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

async def unhandled_error_to_json(request: Request, call_next):
    """
    Turns an unhandled exception into a JSON 500 instead of letting it reach
    Starlette's own error handler.
    """
    try:
        return await call_next(request)
    except Exception:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": "Internal server error. Check the server logs."})

# Added before CORSMiddleware so it ends up INSIDE it: add_middleware pushes
# each new layer to the outside, so the last one added wraps everything above.
app.add_middleware(BaseHTTPMiddleware, dispatch=unhandled_error_to_json)

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
    project_id: str | None = None,
    claims: dict = Depends(verify_token),
) -> RecommendationReport:
    """
    Runs the rest of the pipeline (casting, enrichment, risk assessment,
    chemistry scoring, recommendation ranking) over a Screenplay produced by
    /analyze, and returns the resulting RecommendationReport. Passing
    ?project_id= also saves the report to that project's history. Requires a
    Firebase ID token in the Authorization header.
    """

    # Checked before the pipeline runs, not after: a bad project_id is a
    # caller mistake, and it costs minutes of casting/enrichment work to find
    # out about it on the way back out.
    save_to_project = project_id
    if save_to_project is not None:
        try:
            # HistoryStore is sync (see its class comment); this endpoint has
            # to stay async for the pipeline, so its two Firestore calls go
            # through the same threadpool the sync routes below get for free.
            await run_in_threadpool(history.ensure_project_exists, claims["uid"], save_to_project)
        except ProjectNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such project.")
        except Exception as e:
            # A bad id is the caller's problem (404 above), but history being
            # unreachable is not -- run the pipeline anyway and skip the save,
            # rather than refusing to cast at all because storage is down.
            print(f"[history] History unavailable, running without saving: {e}")
            save_to_project = None

    report = await raphael.recommend(screenplay)

    if save_to_project is not None:
        # Deliberately non-fatal. The report in hand cost a full pipeline run;
        # handing it back unsaved beats failing the request and discarding it
        # over a storage problem the caller can't do anything about.
        try:
            await run_in_threadpool(history.save_report, claims["uid"], save_to_project, report, screenplay)
        except Exception as e:
            print(f"[history] Could not save report for project {save_to_project}: {e}")

    return report

# The /projects routes are declared sync so FastAPI runs them in a threadpool,
# matching HistoryStore's blocking Firestore client (see auth.verify_token for
# the same convention).

@app.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(
    screenplay: Screenplay,
    claims: dict = Depends(verify_token),
) -> Project:
    """
    Saves a Screenplay from /analyze as a new project, returning it with the
    generated id to pass to /recommend?project_id=.
    """
    return history.create_project(claims["uid"], screenplay)

@app.get("/projects")
def list_projects(claims: dict = Depends(verify_token)) -> list[ProjectSummary]:
    """
    Lists the signed-in user's saved projects, most recently touched first.
    """
    return history.list_projects(claims["uid"])

@app.get("/projects/{project_id}")
def get_project(
    project_id: str,
    claims: dict = Depends(verify_token),
) -> Project:
    """
    Returns one of the signed-in user's projects with its latest report.
    """
    project = history.get_project(claims["uid"], project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such project.")
    return project

@app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    claims: dict = Depends(verify_token),
) -> Response:
    """
    Deletes one of the signed-in user's projects and every report under it.
    """
    if not history.delete_project(claims["uid"], project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such project.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
