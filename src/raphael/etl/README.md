# ETL

Manual CLI tools for growing the ClickHouse `people`/`credits`/`collaborations` corpus:
look people up (researching them via Parallel on a cache miss), or discover a whole
network of actors from TMDB and research/store everyone new.

## What it does

`populate.py` is a `sys.argv`-dispatched script, not an importable library module --
run it via `uv run python -m src.raphael.etl.populate <subcommand> ...`. Every subcommand
opens its own `ClickHouseHandler`/`ParallelClient`/`TMDBClient` and touches ClickHouse
directly; none of this goes through the `agentry`/LangGraph framework.

| Subcommand | What it does |
|---|---|
| `discover <title> [flags]` | Seeds from one movie, BFS-traverses the TMDB actor graph outward (movie -> cast -> each actor's other movies -> those movies' cast -> repeat), then researches + stores every newly-discovered actor not already in ClickHouse. The real "populate the DB at scale" command. |
| `movie-cast <title> [--limit N]` | Pulls one movie's cast/crew from TMDB and researches/stores each cast member (crew is listed but not researched -- actors-only). No traversal -- just that one movie's direct cast. |
| `add-person <name> [current_pick ...]` | Looks up one person by name; researches + stores them if not already cached. Also runs a roster search favoring `current_pick`s afterward, to show the person joining the roster in the same run. |
| `roster [current_pick ...]` | Searches the already-stored `people` table, ranked by collaboration affinity with `current_pick`s. Read-only -- doesn't call Parallel or TMDB. |
| *(no subcommand)* | Bare-name demo: researches one person via Parallel and stores them, printing the full dossier. Not TMDB-driven. |

## `discover` in detail

```sh
uv run python -m src.raphael.etl.populate discover "Inception" --depth 3 --max-actors 150
```

Flags (any position, all optional -- default from `etl/config.py`, overridable via env or
per-invocation flag):

| Flag | Meaning | Default |
|---|---|---|
| `--depth N` | Actor-generations to traverse. Generation 1 is the seed movie's own cast; generations 2..N come from further actor -> other movies -> cast hops. | `ETL_TRAVERSAL_MAX_DEPTH` (3) |
| `--max-actors N` | Total actor budget across the whole traversal -- stops discovering once hit. | `ETL_TRAVERSAL_MAX_ACTORS` (150) |
| `--movies-per-actor N` | How many of each actor's other movies to expand through (ranked by TMDB popularity). | `ETL_TRAVERSAL_MOVIES_PER_ACTOR` (5) |
| `--cast-per-movie N` | How many top-billed cast members to pull from each movie. | `ETL_TRAVERSAL_CAST_PER_MOVIE` (10) |

After traversal, candidate names are batch-filtered against ClickHouse in one round trip
(`ClickHouseHandler.get_new_names`) rather than checking each name individually, then
researched concurrently (bounded by `ETL_PARALLEL_RESEARCH_CONCURRENCY`, default 3) and
stored. The final summary reports discovered / already-cached / newly-stored / failed
counts.

**Cost**: each newly-researched actor is one Parallel `pro-fast` deep-research call --
$0.10/actor at time of writing (`docs.parallel.ai/getting-started/pricing`; only
successfully-completed runs are billed). A full default-budget run (150 actors) costs up
to ~$15, less for however many are already cached. TMDB itself is free (rate-limited to
~40 req/sec/IP; traversal stays well under that via `ETL_TMDB_CONCURRENCY`, default 5).

Re-running the same seed is close to free -- almost everyone will already be cached.

### Running a full-budget `discover` (surviving a closed SSH session)

A full-budget run (150 actors, concurrency 3) can take hours, since Parallel's
`pro-fast` processor has a documented 30s-5min latency per call. If you're running this
on a remote server over SSH, a plain foreground command dies with the connection
(`SIGHUP`) the moment your session drops. Launch it detached instead:

```sh
nohup uv run python -u -m src.raphael.etl.populate discover "Inception" --depth 3 --max-actors 150 > discover.log 2>&1 &
disown
```

- `-u` (Python's unbuffered flag) matters here -- without it, stdout is fully
  block-buffered once redirected to a file, so `discover.log` can look nearly empty for
  a long time even though work is happening, and a killed/crashed process can lose
  everything sitting in that buffer.
- `disown` detaches the job from the current shell so it isn't sent `SIGHUP` when the
  shell exits.
- Reattach/monitor later with `tail -f discover.log`, and check it's still alive with
  `pgrep -fa "etl.populate discover"`.

Alternatively, run it inside `tmux`/`screen` (`tmux new -s discover`, run the command,
detach with `Ctrl-b d`, reattach with `tmux attach -t discover`) -- that also lets you
watch live output normally if you reconnect, rather than tailing a log file.

**If it needs to be stopped early**: `pkill -f "etl.populate discover"` (or a scoped
`kill <pid>` from `pgrep -fa "etl.populate discover"`) stops the local process, but note
this does **not** cancel any Parallel research calls already in flight -- the Parallel
SDK has no `cancel` endpoint, so up to `ETL_PARALLEL_RESEARCH_CONCURRENCY` in-progress
calls may keep running (and billing) server-side regardless. Whatever had already
finished and been stored before the kill stays in ClickHouse -- storage happens
per-actor as each research call completes, not in one batch at the end -- so re-running
the same command afterward picks up close to where it left off via `get_new_names`.

## Config

All knobs live in `src/raphael/etl/config.py`, same env-driven `Config` class pattern as
`tmdb/config.py`/`parallel/config.py`. Override via env vars matching the setting names
above (e.g. `ETL_TRAVERSAL_MAX_ACTORS=50`); nothing here needs to be in `.env` unless
you want a different default than what's baked in.

## Requirements

- `TMDB_API_KEY` -- TMDB's **v4 "API Read Access Token"** (a long JWT-looking string
  from themoviedb.org/settings/api's "API Read Access Token" field, *not* the shorter
  v3 "API Key" -- `TMDBClient` sends it as a Bearer token, so the v3 key gets a 401).
- `PARALLEL_API_KEY` -- for the research calls every subcommand except `roster` makes.
- `CLICKHOUSE_USERNAME`/`CLICKHOUSE_PASSWORD`/`CLICKHOUSE_HOST`/`CLICKHOUSE_PORT`/
  `CLICKHOUSE_ALLOW_WRITE_ACCESS` -- every subcommand touches ClickHouse.

See `.env.example` at the repo root.

## Known limitations

- **Cross-run name matching** relies on `ClickHouseHandler`'s canonicalization
  (`_resolve_canonical_name`), which only catches exact matches and simple token-subset
  variants -- e.g. it will NOT recognize two genuinely different people who happen to
  share a short name as different, and conversely can miss that two spellings are the
  same person if punctuation breaks the token match. Every code path here that researches
  a name stores the dossier under the *caller's own* name (TMDB's, for `discover`/
  `movie-cast`; whatever you typed, for `add-person`) rather than whatever free-text name
  the research agent returned, specifically to avoid drift between what you searched for
  and what's stored.
- `insert_person` does three sequential inserts (`people`, then `credits`, then
  `collaborations`) with no transaction -- a failure partway through can leave a `people`
  row with no matching credits/collaborations, and a later run will treat that name as
  "already cached" even though it's incomplete.
- `discover`'s traversal budget can't distinguish "ran out of budget" from "the graph
  naturally dead-ended" -- both just stop the loop early.
