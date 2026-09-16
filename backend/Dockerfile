# ─────────────────────────────────────────────
# Stage 1: Builder — install Python packages
# ─────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

# System build deps: cairo/pango for WeasyPrint PDF generation
# Note: asyncpg / libpq removed — Finora uses SQLite, not PostgreSQL.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
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

# Writable directories needed at runtime
RUN mkdir -p generated_reports .finora/cache .finora/state .finora/temp .finora/locks .finora/logs \
    && chown -R finora:finora generated_reports .finora

USER finora

# Default port — override with PORT env var
ENV PORT=8000
EXPOSE 8000

# Run migrations then start the server.
# SQLite database file will be created automatically.
# Set GOOGLE_DRIVE_ENABLED=true and mount credentials.json for Drive sync.
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
