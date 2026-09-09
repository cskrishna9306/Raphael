# Raphael FastAPI backend -- deployed to Cloud Run.
#
# `uv` needs to be present at RUNTIME, not just build time: ClickHouseClient
# (src/raphael/clickhouse/client.py) spawns `uv run --with mcp-clickhouse
# mcp-clickhouse` as a stdio subprocess on every process start, not just during
# dependency install.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Dependency layer first so it's cached separately from source changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/
COPY README.md ./

RUN useradd --create-home --shell /bin/bash raphael \
    && chown -R raphael:raphael /app
USER raphael

# Cloud Run injects PORT at runtime; src/raphael/config.py already reads it
# via os.getenv("PORT", "8000") through main.py's uvicorn.run(...).
CMD ["uv", "run", "python", "-m", "src.raphael.main"]
