# ─────────────────────────────────────────────
# Stage 1: Builder — install Python packages
# ─────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# System build deps: libpq for asyncpg, cairo/pango for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ─────────────────────────────────────────────
# Stage 2: Runtime image
# ─────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Runtime-only system libs (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN addgroup --system finora && adduser --system --ingroup finora finora

# Copy application source
COPY --chown=finora:finora . .

# Generated reports directory must be writable at runtime
RUN mkdir -p generated_reports && chown finora:finora generated_reports

USER finora

# Railway injects $PORT at runtime; default to 8000
ENV PORT=8000
EXPOSE 8000

# Mirrors the Procfile exactly:
# web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
