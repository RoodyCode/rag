FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (no project install yet)
RUN uv sync --frozen --no-install-project

# Copy source
COPY . .

# Install the project itself
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "python", "mcp_server.py"]
