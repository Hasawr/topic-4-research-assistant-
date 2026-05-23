# =============================================================
# Async Research Assistant — Dockerfile
# =============================================================
# Two-stage build:
#   Stage 1 (builder) — install deps + run offline smoke tests
#   Stage 2 (runtime) — lean production image, non-root user
# =============================================================

# ── STAGE 1: builder ─────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build tools needed by asyncpg (C extension)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy full source
COPY . .

# Run the offline smoke tests to gate the build
# OFFLINE_MODE skips API key validation in config.py
# CACHE_BACKEND=memory avoids needing a real PostgreSQL at build time
RUN OFFLINE_MODE=true \
    CACHE_BACKEND=memory \
    DATABASE_URL=postgresql://dummy:dummy@localhost:5432/dummy \
    LLM_PROVIDER=gemini \
    WEB_SEARCH_PROVIDER=duckduckgo \
    PYTHONPATH=/app \
    /install/bin/pytest tests/ -v --tb=short


# ── STAGE 2: runtime ─────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Runtime system dependency for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
 && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder (includes binaries + libs)
COPY --from=builder /install /usr/local

# Copy only the source needed at runtime (no tests, no __pycache__)
COPY ai/        ./ai/
COPY src/        ./src/
COPY data/       ./data/
COPY demo_ai.py  ./demo_ai.py

# Keeps Python output unbuffered (visible in docker logs)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser /app
USER appuser

# Default: run the CLI (override with `docker run ... python demo_ai.py`)
# All secrets come in via --env-file or -e flags at runtime — never baked in
ENTRYPOINT ["python", "-m", "src.cli"]
CMD ["--help"]
