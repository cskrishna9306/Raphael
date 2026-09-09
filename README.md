# Raphael
Submission to the Agentic Cinema Hackathon '26

## Setup

Requires Python >=3.12 and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Copy the example env file and fill in your credentials
cp .env.example .env
```

`.env` needs GCP credentials (Vertex AI), plus Parallel, ClickHouse, and TMDB credentials -- see `.env.example` for the full list. `HOST`/`PORT` are optional and default to `0.0.0.0:8000`. `ALLOWED_ORIGINS` is also optional and defaults to `http://localhost:5173` (the frontend's dev server) -- see `frontend/README.md` for running the frontend.

Start the FastAPI server:

```bash
uv run python -m src.raphael.main
```

## Using the API

With the server running (defaults to `http://localhost:8000`):

```bash
# Liveness probe
curl http://localhost:8000/health

# Readiness probe
curl http://localhost:8000/ready

# Break down a screenplay document (.txt or .pdf) into a Screenplay
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer $ID_TOKEN" \
  -F "file=@/path/to/screenplay.pdf"

# Run the rest of the pipeline over that Screenplay
curl -X POST http://localhost:8000/recommend \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d @screenplay.json
```

Every endpoint below `/health` and `/ready` requires a Firebase ID token in the `Authorization` header. `/recommend` returns a `RecommendationReport` JSON body: the ranked cast clusters along with each cluster's top actor risk assessments.

### Per-user history

Saved screenplays and reports live in Cloud Firestore under `users/{uid}/projects`, scoped to the signed-in Google account. Firestore is reached only from the backend via the Admin SDK -- `firestore.rules` denies all direct client access.

```bash
# Save a Screenplay from /analyze as a project
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d @screenplay.json

# Run the pipeline and save the report against that project
curl -X POST "http://localhost:8000/recommend?project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d @screenplay.json

# List history / read one project with its latest report / delete one
curl http://localhost:8000/projects -H "Authorization: Bearer $ID_TOKEN"
curl http://localhost:8000/projects/$PROJECT_ID -H "Authorization: Bearer $ID_TOKEN"
curl -X DELETE http://localhost:8000/projects/$PROJECT_ID -H "Authorization: Bearer $ID_TOKEN"
```

`project_id` is optional -- without it `/recommend` behaves exactly as before and saves nothing.

One-time setup on a fresh GCP project:

```bash
gcloud services enable firestore.googleapis.com --project=cedar-calling-505608-s1
gcloud firestore databases create --location=nam5 --project=cedar-calling-505608-s1
gcloud projects add-iam-policy-binding cedar-calling-505608-s1 \
  --member=serviceAccount:raphael@cedar-calling-505608-s1.iam.gserviceaccount.com \
  --role=roles/datastore.user
firebase deploy --only firestore:rules
```

To run against the local emulator instead, start it with `firebase emulators:start --only firestore` and export `FIRESTORE_EMULATOR_HOST=127.0.0.1:8080` before starting the server.

## Why Raphael?

Named after the **Great Sage** — later known as *Raphael* — from ***That Time I Got Reincarnated as a Slime***, this project draws from what makes that character compelling: not omniscience, but tireless analysis, precise reasoning, and the ability to act autonomously on behalf of its master.
