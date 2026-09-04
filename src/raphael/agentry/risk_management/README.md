# Risk Management

Given a casting report, assesses each candidate actor for reputational/legal/publicity risk.

## What it does

`RiskManagementAgent` (`agent.py`) is a LangGraph sub-agent that takes a `CastingReport`
(as produced by `casting_director`) and returns a `RiskReport`: a risk assessment for every
unique candidate actor considered across the whole cast.

1. **Fan out** — one graph branch per unique candidate across the entire report
   (`CastingReport.unique_candidates()`, deduped by name), run concurrently
   (`START` → `fan_out` → `Send("assess_candidate", ...)` per candidate). An actor
   shortlisted for two different characters is only assessed once.
2. **Search** (`assess`) — a Parallel web-search sub-agent (`ParallelAgentType.SEARCH`)
   runs distinct searches for scandals/controversies, news articles/press coverage (legal
   issues, on-set/contractual disputes, other negative coverage), and questionable social
   media comments/posts about the candidate. The findings are structured into a
   `RiskAssessment`: an overall `risk_level` (low/medium/high), a rationale, and any specific
   `RiskFlag`s (category + description + source) the findings support.
3. **Reduce** (`build_report`) — every candidate's assessment is collected into a
   `RiskReport`.

`RiskManagementAgent` runs over `CastingReport`, not `ChemistryReport` — risk is intrinsic
to an actor, independent of which chemistry-optimized cast combo they might land in, so
assessing the full candidate pool once (rather than per chemistry cluster) avoids redundant
lookups for actors who'd otherwise repeat across multiple clusters.

The whole graph is **async-only** — every node runs concurrently via `ainvoke`/`astream`. Use
`await agent.ainvoke(casting_report)` directly; the sync `agent.invoke(casting_report)` is a
thin `asyncio.run(...)` wrapper and can't be called from inside a running event loop.

## Files

| File | Contents |
|---|---|
| `agent.py` | `RiskManagementAgent` — the graph and its nodes |
| `models.py` | `RiskLevel`, `RiskFlag`, `RiskAssessment`, `RiskReport` (domain models) + `RiskManagementState`, `CandidateRiskState` (internal graph state) |
| `SEARCH_PROMPT.md` | System prompt for the risk-research sub-agent |

## Requirements

Live runs need real credentials in `.env` (see `.env.example`):
- `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` — Vertex AI (ADC)
- `PARALLEL_API_KEY` — Parallel search

## Smoke test

`tests/risk_management/sample_casting_report.json` is a pre-built `CastingReport` fixture
you can feed straight into the agent. This calls live Parallel + Vertex AI APIs.

```python
import asyncio
from pathlib import Path

from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.risk_management import RiskManagementAgent

async def main():
    casting_report = CastingReport.model_validate_json(
        Path("tests/risk_management/sample_casting_report.json").read_text()
    )
    report = await RiskManagementAgent().ainvoke(casting_report)
    for assessment in report.assessments:
        print(assessment.name, "->", assessment.risk_level.value)

asyncio.run(main())
```

Or as a one-liner from the repo root:

```sh
uv run python -c "
import asyncio
from pathlib import Path
from src.raphael.agentry.casting_director.models import CastingReport
from src.raphael.agentry.risk_management import RiskManagementAgent

async def main():
    casting_report = CastingReport.model_validate_json(Path('tests/risk_management/sample_casting_report.json').read_text())
    report = await RiskManagementAgent().ainvoke(casting_report)
    for assessment in report.assessments:
        print(assessment.name, '->', assessment.risk_level.value)

asyncio.run(main())
"
```

A construction-only check (no network calls, no credentials needed) is also useful for verifying
the graph wiring after a refactor:

```sh
uv run python -c "
from src.raphael.agentry.risk_management import RiskManagementAgent
agent = RiskManagementAgent()
print(agent.graph)
"
```
