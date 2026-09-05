# Enrichment

Given a casting report, enriches each candidate actor with a full research dossier
(ClickHouse-cached where possible, live Parallel deep-research on a cache miss).

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
   biographical fields). On a **miss**, it calls `ParallelClient.aresearch_person()` live,
   stores the result via `insert_person()`, and returns that freshly-researched dossier
   directly.
3. **Reduce** (`build_report`) — every candidate's `EnrichmentAssessment` (dossier +
   `source`: `cache` / `research` / `failed`) is collected into an `EnrichmentReport`.

`EnrichmentAgent` opens **one** `ClickHouseHandler` MCP session per `ainvoke()` call,
shared by every concurrently-running fan-out branch, and tears it down when the run
finishes. It is not safe to call `ainvoke()` twice concurrently on the same agent instance
as a result (accepted MVP limitation — see the class docstring in `agent.py`).

Unlike `RiskManagementAgent`, this agent makes **no LLM call** — there's no judgment to
form, just a lookup-or-research-and-store. It's designed to run concurrently alongside
`RiskManagementAgent` over the same `CastingReport` (see
`Raphael.aenrich_and_assess_risk` in `src/raphael/agentry/orchestrator.py`), since the two
are independent.

The whole graph is **async-only** — every node runs concurrently via `ainvoke`/`astream`. Use
`await agent.ainvoke(casting_report)` directly; the sync `agent.invoke(casting_report)` is a
thin `asyncio.run(...)` wrapper and can't be called from inside a running event loop.

## Files

| File | Contents |
|---|---|
| `agent.py` | `EnrichmentAgent` — the graph and its nodes |
| `models.py` | `EnrichmentSource`, `EnrichmentAssessment`, `EnrichmentReport` (domain models) + `EnrichmentState`, `CandidateEnrichmentState` (internal graph state) |

## Requirements

This agent makes no LLM call, so Vertex AI credentials aren't needed for it specifically
(they're only needed by `Raphael.run()`, unrelated). It does always touch ClickHouse (on
both the hit and miss paths) and touches Parallel on a miss, so live runs need:

- `CLICKHOUSE_USERNAME`, `CLICKHOUSE_PASSWORD`, `CLICKHOUSE_HOST`, `CLICKHOUSE_PORT`,
  `CLICKHOUSE_ALLOW_WRITE_ACCESS` — ClickHouse (see `.env.example`)
- `PARALLEL_API_KEY` — Parallel deep research, for the cache-miss fallback

**A first run against a fresh/empty ClickHouse instance will do full Parallel research +
storage for every candidate** — slow, and costs Parallel API calls. **A second run against
the same instance should mostly hit cache** — fast, no Parallel calls, just the 3-table
join. Keep this in mind before re-running the smoke test repeatedly.

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

`Raphael.run_async` (`src/raphael/agentry/orchestrator.py`) runs this agent and
`RiskManagementAgent` concurrently via `asyncio.gather` over the same `CastingReport`, then
merges the enrichment dossiers back onto it (`EnrichmentReport.merge_into`, upgrading each
candidate's shallow, search-prefilled dossier to the fuller researched/cached one where
available), and finally runs `ChemistryEngine` over the enriched report — so chemistry
scoring sees full filmography/collaborators data instead of whatever
`CastingDirectorAgent`'s shallow search pass happened to surface:

```sh
uv run python -c "
import asyncio
from pathlib import Path
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.orchestrator import Raphael

async def main():
    casting_report = CastingReport.model_validate_json(Path('tests/risk_management/sample_casting_report.json').read_text())
    enriched_casting_report, chemistry_report, risk_report = await Raphael().run_async(casting_report)
    print('enriched dossiers:', [(c.name, len(c.dossier.filmography) if c.dossier else 0) for casting in enriched_casting_report.castings for c in casting.candidates])
    print('chemistry clusters:', len(chemistry_report.clusters))
    print('risk:', [a.name for a in risk_report.assessments])

asyncio.run(main())
"
```
