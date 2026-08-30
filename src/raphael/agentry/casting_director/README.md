# Casting Director

Given a screenplay's cast breakdown, finds real actors who could plausibly play each character.

## What it does

`CastingDirectorAgent` (`agent.py`) is a LangGraph sub-agent that takes a `Screenplay`
(title + `Cast` of `CharacterProfile`s, as produced by `screenplay_breakdown`) and returns a
`CastingReport`: every character paired with a shortlist of candidate actors.

1. **Fan out** — one graph branch per character in `screenplay.cast.characters`, run concurrently
   (`START` → `fan_out` → `Send("search_candidates", ...)` per character).
2. **Search** (`find_candidates`) — a Parallel web-search sub-agent (`ParallelAgentType.SEARCH`)
   looks for actors who fit the character's role size, gender, age range, description, and traits.
   The findings are structured into a list of `CastingCandidate`s: name, a fit rationale, and a
   best-effort `PersonDossier` prefilled with whatever casting-relevant facts (bio, notable roles,
   age/nationality, awards, etc.) happened to surface in that same search pass.
3. **Reduce** (`build_report`) — every character's candidates are collected into a `CastingReport`.

The whole graph is **async-only** — every node runs concurrently via `ainvoke`/`astream`. Use
`await agent.ainvoke(screenplay)` directly; the sync `agent.invoke(screenplay)` is a thin
`asyncio.run(...)` wrapper and can't be called from inside a running event loop.

### Deep research is currently disabled

A separate deep-research pass (`enrich_candidate`, using `ParallelAgentType.RESEARCH` to compile a
fully-verified `PersonDossier` per candidate) exists but is commented out in `agent.py`, along with
the `research_agent` it depends on — see the comments there for why and how to re-enable it. Right
now every dossier is only ever as complete as what the search pass happened to surface.

## Files

| File | Contents |
|---|---|
| `agent.py` | `CastingDirectorAgent` — the graph and its nodes |
| `models.py` | `CastingCandidate`, `CastingCharacter`, `CastingReport` (domain models) + `CastingDirectorState`, `CharacterSearchState`, `CandidateSearchResult` (internal graph state) |
| `SEARCH_PROMPT.md` | System prompt for the candidate-search sub-agent |
| `RESEARCH_PROMPT.md` | System prompt for the (currently disabled) dossier-research sub-agent |

## Requirements

Live runs need real credentials in `.env` (see `.env.example`):
- `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` — Vertex AI (ADC)
- `PARALLEL_API_KEY` — Parallel search

## Smoke test

`tests/casting_director/sample_screenplay_object.json` is a pre-built `Screenplay` fixture (7
characters from *Night of the Living Dead*) you can feed straight into the agent without needing
`ScreenplayBreakdownAgent` first. This calls live Parallel + Vertex AI APIs — expect roughly
10-15 seconds for all 7 characters to search concurrently.

```python
import asyncio
from pathlib import Path

from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.agentry.casting_director import CastingDirectorAgent

async def main():
    screenplay = Screenplay.model_validate_json(
        Path("tests/casting_director/sample_screenplay_object.json").read_text()
    )
    report = await CastingDirectorAgent().ainvoke(screenplay)
    for casting in report.castings:
        print(casting.character.name, "->", [c.name for c in casting.candidates])

asyncio.run(main())
```

Or as a one-liner from the repo root:

```sh
uv run python -c "
import asyncio
from pathlib import Path
from src.raphael.agentry.screenplay_breakdown.models import Screenplay
from src.raphael.agentry.casting_director import CastingDirectorAgent

async def main():
    screenplay = Screenplay.model_validate_json(Path('tests/casting_director/sample_screenplay_object.json').read_text())
    report = await CastingDirectorAgent().ainvoke(screenplay)
    for casting in report.castings:
        print(casting.character.name, '->', [c.name for c in casting.candidates])

asyncio.run(main())
"
```

A construction-only check (no network calls, no credentials needed) is also useful for verifying
the graph wiring after a refactor:

```sh
uv run python -c "
from src.raphael.agentry.casting_director import CastingDirectorAgent
agent = CastingDirectorAgent()
print(agent.graph)
"
```
