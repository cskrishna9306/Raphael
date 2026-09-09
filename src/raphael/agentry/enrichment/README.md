# Enrichment

Given a casting report, enriches each candidate actor with a full research dossier
(ClickHouse-cached where possible, a shallow live Parallel search on a cache miss --
never deep research; see `search_agent.py`).

## What it does

`EnrichmentAgent` (`agent.py`) is a LangGraph sub-agent that takes a `CastingReport`
(as produced by `casting_director`) and returns an `EnrichmentReport`: a full research
dossier for every unique candidate actor considered across the whole cast.

1. **Fan out** — one graph branch per unique candidate across the entire report
   (`CastingReport.unique_candidates()`, deduped by name), run concurrently
   (`START` → `fan_out` → `Send("enrich_candidate", ...)` per candidate). An actor
   shortlisted for two different characters is only enriched once.
2. **Enrich** (`enrich`) — `ClickHouseHandler.find_or_research_dossier()`: canonicalizes
   the actor's name and checks the `people` table for an existing row. On a **hit**, it
   reconstructs a full `PersonDossier` by also joining the `credits` and `collaborations`
   tables (so filmography and collaborators come back populated, not just the flat
   biographical fields). On a **miss**, it calls `PersonSearchAgent.research()`
   (`search_agent.py` — one live Parallel *search* call + one Gemini call to structure the
   findings, mirroring `CastingDirectorAgent`/`RiskManagementAgent`'s own shallow-search
   pattern; deliberately never deep research), stores the result via `insert_person()`, and
   returns that freshly-found dossier directly.
3. **Reduce** (`build_report`) — every candidate's `EnrichmentAssessment` (dossier +
   `source`: `cache` / `search` / `failed`) is collected into an `EnrichmentReport`.

`EnrichmentAgent` opens **one** `ClickHouseHandler` MCP session per `ainvoke()` call,
shared by every concurrently-running fan-out branch, and tears it down when the run
finishes. It is not safe to call `ainvoke()` twice concurrently on the same agent instance
as a result (accepted MVP limitation — see the class docstring in `agent.py`).

It's designed to run concurrently alongside `RiskManagementAgent` over the same
`CastingReport` (see `Raphael.recommend` in `src/raphael/agentry/orchestrator.py`, which
runs both via `asyncio.gather`), since the two are independent.

Deep research (`ParallelClient.aresearch_person`) is intentionally never called from this
agent or anywhere in the live `/recommend` path — it stays reserved for the offline
`etl/populate.py` CLI tools (`ClickHouseHandler.find_or_research_person`), which do their
own bulk, deliberately-controlled corpus-building.

The whole graph is **async-only** — every node runs concurrently via `ainvoke`/`astream`. Use
`await agent.ainvoke(casting_report)` directly; the sync `agent.invoke(casting_report)` is a
thin `asyncio.run(...)` wrapper and can't be called from inside a running event loop.

## Files

| File | Contents |
|---|---|
| `agent.py` | `EnrichmentAgent` — the graph and its nodes |
| `models.py` | `EnrichmentSource`, `EnrichmentAssessment`, `EnrichmentReport` (domain models) + `EnrichmentState`, `CandidateEnrichmentState` (internal graph state) |
| `search_agent.py` | `PersonSearchAgent` — the shallow-search-and-structure cache-miss fallback |
| `SEARCH_PROMPT.md` | System prompt for `PersonSearchAgent`'s search step |

## Requirements

This agent's cache-miss path now makes one Gemini call (via `PersonSearchAgent`'s
`structuring_model`), so it needs Vertex AI credentials too, in addition to ClickHouse and
Parallel:

- `CLICKHOUSE_USERNAME`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`,
  `CLICKHOUSE_ALLOW_WRITE_ACCESS` — ClickHouse (see `.env.example`)
- `PARALLEL_API_KEY` — Parallel shallow search, for the cache-miss fallback
- `GOOGLE_APPLICATION_CREDENTIALS`/`GOOGLE_CLOUD_PROJECT`/`GOOGLE_CLOUD_LOCATION` — Vertex AI,
  for structuring the search findings into a `PersonDossier`

**A first run against a fresh/empty ClickHouse instance will shallow-search + store every
candidate** — one Parallel search + one Gemini call each. **A second run against the same
instance should mostly hit cache** — fast, no Parallel/Gemini calls, just the 3-table join.
Keep this in mind before re-running the smoke test repeatedly.

## Smoke test

`tests/risk_management/sample_casting_report.json` is a pre-built `CastingReport` fixture
(reused from the `risk_management` module — it already has a candidate shortlisted for two
characters, useful for confirming dedup here too) you can feed straight into the agent.

```python
import asyncio
from pathlib import Path

from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.enrichment import EnrichmentAgent

async def main():
    casting_report = CastingReport.model_validate_json(
        Path("tests/risk_management/sample_casting_report.json").read_text()
    )
    report = await EnrichmentAgent().ainvoke(casting_report)
    for assessment in report.assessments:
        credits = len(assessment.dossier.filmography) if assessment.dossier else 0
        print(assessment.name, "->", assessment.source.value, f"({credits} credits)")

asyncio.run(main())
```

Or as a one-liner from the repo root:

```sh
uv run python -c "
import asyncio
from pathlib import Path
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.enrichment import EnrichmentAgent

async def main():
    casting_report = CastingReport.model_validate_json(Path('tests/risk_management/sample_casting_report.json').read_text())
    report = await EnrichmentAgent().ainvoke(casting_report)
    for assessment in report.assessments:
        credits = len(assessment.dossier.filmography) if assessment.dossier else 0
        print(assessment.name, '->', assessment.source.value, f'({credits} credits)')

asyncio.run(main())
"
```

A construction-only check (no network calls, no credentials needed) is also useful for verifying
the graph wiring after a refactor:

```sh
uv run python -c "
from src.raphael.agentry.enrichment import EnrichmentAgent
agent = EnrichmentAgent()
print(agent.graph)
"
```

## Running as part of the full post-casting pipeline

`Raphael.recommend` (`src/raphael/agentry/orchestrator.py`) runs `CastingDirectorAgent`,
then this agent and `RiskManagementAgent` concurrently via `asyncio.gather` over the
resulting `CastingReport`, then merges the enrichment dossiers back onto it
(`EnrichmentReport.merge_dossiers`, upgrading each candidate's shallow, search-prefilled
dossier to the fuller cached/searched one where available), and finally runs
`ChemistryEngine` + `RecommendationEngine` over the enriched report — so chemistry scoring
sees full filmography/collaborators data instead of whatever `CastingDirectorAgent`'s own
shallow search pass happened to surface:

```sh
uv run python -c "
import asyncio
from pathlib import Path
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.agentry.orchestrator import Raphael

async def main():
    screenplay = Screenplay.model_validate_json(Path('tests/casting_director/sample_screenplay_object.json').read_text())
    raphael = Raphael()
    async with raphael.clickhouse_handler:
        recommendations = await raphael.recommend(screenplay)
    for rec in recommendations.recommendations:
        print([s.candidate.name for s in rec.cluster.selections], rec.cluster.chemistry_score)

asyncio.run(main())
"
```
