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

`.env` needs GCP credentials (Vertex AI), plus Parallel, ClickHouse, and TMDB credentials -- see `.env.example` for the full list. `HOST`/`PORT` are optional and default to `0.0.0.0:8000`.

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

# Run the full pipeline over a screenplay document (.txt or .pdf)
curl -X POST http://localhost:8000/recommend \
  -F "file=@/path/to/screenplay.pdf"
```

`/recommend` returns a `RecommendationReport` JSON body: the ranked cast clusters along with each cluster's top actor risk assessments.

## Why Raphael?

Named after the **Great Sage** — later known as *Raphael* — from ***That Time I Got Reincarnated as a Slime***, this project draws from what makes that character compelling: not omniscience, but tireless analysis, precise reasoning, and the ability to act autonomously on behalf of its master.
