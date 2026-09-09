# Raphael

**A FIFA-style chemistry rating, but for movie casts.** Raphael assembles a film's cast the way a
scout builds a fantasy sports team — not just by who's talented or available, but by who works well
*together* — and grounds every score in documented, citable collaborative history.

Submission to the Agentic Cinema Hackathon '26.

## Inspiration

Casting is one of the highest-stakes and least data-driven decisions in film.

The directors are unambiguous about how much it matters. Robert Altman: *"When casting's done, 90
percent of my creative work is done."* Martin Scorsese: *"I always say that casting is 85 to 90
percent of the picture for me."*

The people who actually do it are equally unambiguous that there's no method to it. Laura Rosenthal,
casting director on Todd Haynes' films: *"Sometimes it's just not a science, it's very instinctual."*
Jennifer Venditti (*Euphoria*), a nominee for the first-ever casting Oscar: *"It's really hard to put
words to it. It's like saying, 'Define beauty.'"* And Rufus Sewell on chemistry: *"Chemistry is
nothing if it's there, but it's everything if it's not."*

When instinct misses, it costs millions. *Back to the Future* shot five weeks of footage with Eric
Stoltz before Zemeckis recast Marty McFly — the reshoot added $3–4M to a $15M budget, a ~25% overrun
from a single casting call.

In 2026 the Academy awarded the first-ever Best Casting Oscar, its first new category since 2001.
Hollywood has formally recognized casting as an art at the center of filmmaking — and it's still
done entirely on gut.

> **If directing is 90% casting, why is casting still 0% data?**

We aren't trying to replace instinct. We're trying to **give instinct receipts**: the documented
collaborative history no human could synthesize per-decision, surfaced at the moment the decision is
being made.

## What it does

Upload a screenplay. Raphael reads it, decides who it needs, researches real people, and hands back
a ranked set of complete casts you can edit live.

- **Screenplay breakdown** — drop a `.txt` or `.pdf` screenplay and Gemini parses it into a
  structured cast breakdown: characters, role presence (lead / supporting / ensemble), and the
  attributes each role demands. You review and edit the detected characters before anything else runs.
- **Candidate search** — a casting-director agent fans out one concurrent candidate search per
  character and returns a shortlist per role, each candidate carrying a role `fit_score`.
- **Evidence enrichment** — every unique candidate (deduped across roles) gets a dossier:
  filmography, documented collaborators and the specific projects they shared, real quotes about
  working together, awards, controversies, availability, union affiliation, languages and physical
  skills. Cached candidates come straight from ClickHouse; misses fall back to a live Parallel search.
- **Risk assessment** — a parallel risk agent scores each candidate Low / Medium / High against
  documented, sourced signals rather than vibes.
- **Chemistry scoring** — a deterministic engine builds a collaboration graph over every candidate
  and scores it. Pairwise edges combine **NPMI** and **Adamic–Adar** over shared production credits;
  pairs who've never worked together get a small, hard-capped 2-hop "shared collaborators"
  affinity so they rank against each other instead of flattening to zero. Per-actor terms fold in
  role fit and an asymmetric risk penalty. A density penalty deliberately discourages an all-star
  cast where every pair already has history.
- **Cluster search** — a 1-swap local search with random restarts, anchored on lead-role candidate
  combinations, returns the top complete casts rather than a single "best" answer.
- **Live swaps** — swap any actor and the score updates instantly. `/swap/preview` scores *every*
  alternative in that character's shortlist first, so you see each candidate's chemistry delta and a
  per-co-star breakdown before committing. No agents, no API calls — a deterministic recompute over
  data the pipeline already produced.
- **Receipts on click** — every score opens into the cited evidence behind it: the shared films, the
  real quote, the source.
- **Per-user history** — sign in with Google and every screenplay and report is saved to your own
  project history, resumable later.

## How we built it

An agentic pipeline on **Google Cloud (Gemini via Vertex AI)**, a factual backbone from
**Parallel**, and an OLAP layer in **ClickHouse** — each doing exactly the one thing it's best at.

```
screenplay ──► ScreenplayBreakdownAgent ──► CastingDirectorAgent ──┬─► EnrichmentAgent (ClickHouse ─► Parallel)
                     (Gemini)                  (fan-out search)    └─► RiskManagementAgent
                                                                            │
                                                        ChemistryEngine ◄────┘
                                                          (graph + local search)
                                                                │
                                                        RecommendationEngine ──► RecommendationReport
```

- **Gemini (Vertex AI)** is the agentic brain: parsing screenplays into structured objects with
  constrained output, and reasoning over Parallel's facts into chemistry inputs and risk assessments.
- **Parallel** is the factual backbone. We ask it only for what it's best at — discrete,
  citation-backed facts (filmography, documented collaborations, real quotes, availability) through
  its Basis sourcing framework. We deliberately never ask it for subjective judgments. Raphael
  computes chemistry itself, on top of Parallel's verified evidence. Deep research is reserved for
  the offline ETL; the online path uses shallow search only.
- **ClickHouse** is the core loop, not a side dashboard. Dossiers are stored as a wide,
  array-typed table and the roster search-and-rank across every researched candidate runs as an OLAP
  query at request time. Reached over MCP (`mcp-clickhouse`) through a single long-lived session
  opened at app startup, so requests don't each pay for a subprocess and schema setup. Live on-screen
  swaps stay local, respecting ClickHouse's own anti-pattern guidance on point lookups.
- **Agents** are LangGraph `StateGraph`s. Every fan-out (per character, per candidate) uses `Send`
  into an async branch node and a reduce node that builds the report — so a five-character screenplay
  researches five shortlists concurrently, not serially.
- **Backend**: FastAPI + Pydantic, `uv`-managed, deployed to Cloud Run from GitHub Actions.
  `/recommend/stream` streams stage-by-stage progress so the UI isn't a spinner.
- **Frontend**: React + TypeScript + Vite. Ingest, Roster (formation tree, ensemble chemistry graph,
  cluster tabs, risk register) and About screens. Firebase Auth for Google sign-in, deployed to
  Firebase Hosting.
- **History**: Cloud Firestore under `users/{uid}/projects`, written only from the backend via the
  Admin SDK — `firestore.rules` denies all direct client access.
- **Offline ETL**: a TMDB-seeded discovery CLI walks real films' top-billed casts, runs Parallel deep
  research per person, and populates ClickHouse ahead of time, so the demo path is fast and the
  candidate universe is real.

## Setup

Requires Python >= 3.12 with [uv](https://docs.astral.sh/uv/), Node.js >= 20, and
[Task](https://taskfile.dev).

```bash
# Install backend (uv) and frontend (npm) dependencies
task install

# Copy the example env file and fill in your credentials
cp .env.example .env
```

`.env` needs GCP credentials (Vertex AI), plus Parallel, ClickHouse, and TMDB credentials -- see
`.env.example` for the full list. `HOST`/`PORT` are optional and default to `0.0.0.0:8000`.
`ALLOWED_ORIGINS` is also optional and defaults to `http://localhost:5173` (the frontend's dev
server). The frontend reads `VITE_API_BASE_URL` from `frontend/.env` -- only needed if the backend
isn't on `http://localhost:8000`; see `frontend/README.md`.

Run it:

```bash
task run             # frontend + backend together
```

Or start each side on its own:

```bash
task launch-server   # FastAPI on http://localhost:8000
task launch-ui       # Vite dev server on http://localhost:5173
```

Checks:

```bash
task lint            # oxlint
task typecheck       # tsc --noEmit
task check           # both
```

`task --list` shows everything available.

### Populating the candidate pool

The online pipeline reads from ClickHouse first, so seed it before a demo. The ETL CLI is a plain
module (no task wrapper -- its arguments vary per invocation):

```bash
# Deep-research one person and store the dossier
uv run python -m src.raphael.etl.populate "Christopher Nolan"

# Walk a film's top-billed cast into ClickHouse
uv run python -m src.raphael.etl.populate movie-cast "Inception" --limit 3

# BFS outward from one film through its actors' other films, researching everyone new
uv run python -m src.raphael.etl.populate discover "Inception" --depth 2 --max-actors 40
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

`/recommend` returns a `RecommendationReport` JSON body: the ranked cast clusters along with each
cluster's top actor risk assessments. `/recommend/stream` runs the same pipeline while streaming
per-stage progress. `/swap` rescores one cluster with a single character's candidate substituted in,
and `/swap/preview` scores every alternative in a character's shortlist at once -- both are pure
deterministic recomputes over the `Roster` an earlier `/recommend` returned, with no agent,
ClickHouse or Parallel calls.

Signing in is optional on `/analyze`, `/recommend`, `/recommend/stream` and the swap endpoints
-- a Firebase ID token is only required for the `/projects` history endpoints below.

### Per-user history

Saved screenplays and reports live in Cloud Firestore under `users/{uid}/projects`, scoped to the
signed-in Google account. Firestore is reached only from the backend via the Admin SDK --
`firestore.rules` denies all direct client access.

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

To run against the local emulator instead, start it with `firebase emulators:start --only firestore`
and export `FIRESTORE_EMULATOR_HOST=127.0.0.1:8080` before starting the server.

## Challenges we ran into

- **Defining "chemistry" without hand-waving.** The naive version — count shared credits — rewards
  prolific actors and says nothing about pairs who've never met, which is the overwhelmingly common
  case. We landed on NPMI plus Adamic–Adar over the collaboration graph, with a small, capped 2-hop
  shared-collaborator backoff so unproven pairs still differentiate. Every weight is tunable via env
  var because we retuned constantly against real screenplays.
- **Stopping the model from grading its own homework.** Early versions asked an LLM to just *rate*
  chemistry, and it produced confident, unfalsifiable numbers. Splitting the responsibilities —
  Parallel gathers only citable facts, Raphael computes the score deterministically — is what makes
  "click for receipts" possible at all.
- **The all-star trap.** The first working scorer converged on casts where everyone had already
  worked with everyone, which is both boring and unrealistic. We added an explicit density penalty
  toward a target of ~0.35 to push the search back toward mixed casts.
- **Latency.** A naive pass was one deep-research call per candidate per role — minutes per
  screenplay. Fixing it took four things: deduping candidates across roles, LangGraph `Send` fan-out
  so branches run concurrently, ClickHouse-first lookups with deep research pushed offline into the
  ETL, and streaming progress to the UI.
- **Keeping one MCP session alive.** ClickHouse is reached through an `mcp-clickhouse` stdio
  subprocess, which can't be opened in a synchronous constructor and can't be reopened per request
  without paying subprocess and schema-setup cost every time. It's opened once in FastAPI's lifespan
  handler and shared by every request — which also drove a `uv`-at-runtime requirement into the
  Cloud Run image.
- **Real screenplays are messy.** PDFs of actual scripts are inconsistently formatted; getting a
  reliable character breakdown out of them needed structured output plus a human review step in the
  UI rather than blind trust.

## Accomplishments that we're proud of

- **Swaps are instant.** The expensive pipeline runs once; every subsequent swap and preview is a
  deterministic local recompute over the roster already in hand. Editing a cast feels like a game,
  not like waiting on an API.
- **Every number opens into its evidence.** No score in the product is unexplainable — you can click
  through to the films, the quote, and the source.
- **We ship complete casts, not a leaderboard.** The cluster search returns several coherent
  ensembles, which is how the decision is actually made.
- **A real, end-to-end product.** Auth, per-user history, streaming progress, formation tree,
  ensemble chemistry graph, risk register, report export, CI/CD to Cloud Run and Firebase Hosting —
  not a notebook demo.
- **Honest division of labor across three services.** Parallel gathers verifiable evidence,
  ClickHouse ranks at scale, Gemini reasons over it. Nothing is a name-drop.

## What we learned

- **Ask each service for what it's uniquely good at, and nothing else.** The quality jump came from
  narrowing what we asked of the LLM, not from asking it for more.
- **Deterministic scoring is a feature, not a compromise.** Because chemistry is computed rather than
  generated, it's reproducible, tunable, explainable, and fast enough to recompute on every keystroke.
- **Graph metrics from information retrieval transfer surprisingly well.** NPMI and Adamic–Adar,
  borrowed from co-occurrence and link prediction, capture "these two have real history" far better
  than raw counts.
- **Caching is architecture.** Deciding what is offline (deep research) versus online (search and
  rank) determined the entire shape of the system.
- **Users need a checkpoint.** Letting people correct the screenplay breakdown before the expensive
  pipeline runs cost one screen and bought all of the trust.

## What's next for Raphael

- **Beyond actors** — extend chemistry to directors, writers, cinematographers, and the rest of the
  crew. The graph and scoring are role-agnostic already; it's a data-coverage problem.
- **Richer chemistry signals** — genre fit, skills, and critical reception of past collaborations,
  not just whether two people have shared a set.
- **Real-world constraints** — budget, scheduling, and availability, so a great cast on paper is one
  that can actually be assembled. Projected hours per cast member against a production timeline, and
  calendar conflict detection across the roster.
- **Opening the door for newcomers.** This is the direction we care about most. A tool that scores
  people by documented history structurally favors people who already have one — which is exactly the
  loop that keeps first-timers out of the room. The density penalty is a first step: it already
  pushes the search away from casts where everyone has worked with everyone. Next is going further —
  an explicit discovery mode that surfaces high-fit, low-credit candidates alongside the safe picks,
  and a chemistry model that predicts affinity from shared collaborators, training, and background
  rather than requiring a shared credit to exist at all. The goal is to make taking a chance on
  someone new a *defensible* decision with evidence behind it, instead of a leap of faith that
  nobody wants to be responsible for.
- **Casting directors keep the final call.** Raphael arms them; it doesn't overrule them. The
  industry just put casting on its biggest stage — we want to be the first tool that treats it with
  the rigor that recognition demands.

## Why Raphael?

Named after the **Great Sage** — later known as *Raphael* — from ***That Time I Got Reincarnated as
a Slime***, this project draws from what makes that character compelling: not omniscience, but
tireless analysis, precise reasoning, and the ability to act autonomously on behalf of its master.
