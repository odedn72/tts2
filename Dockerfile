# =============================================================================
# TTS Reader - Multi-stage Dockerfile
# Stage 1: Build frontend assets (Node)
# Stage 2: Build backend dependencies (Python)
# Stage 3: Slim runtime image with ffmpeg
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Frontend build
# ---------------------------------------------------------------------------
FROM node:20.11-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first (layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copy source and build
COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Backend dependency installation
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS backend-build

WORKDIR /app/backend

# Install build dependencies (needed for some Python packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency definition first (layer caching)
COPY backend/pyproject.toml ./

# Install Python dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -e "."

# Copy backend source
COPY backend/src/ ./src/

# ---------------------------------------------------------------------------
# Stage 3: Runtime image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install runtime dependencies: ffmpeg for audio processing
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy Python virtual environment from build stage
COPY --from=backend-build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy backend source code
COPY --from=backend-build /app/backend/ ./backend/

# Copy built frontend assets
COPY --from=frontend-build /app/frontend/dist/ ./frontend/dist/

# Create audio storage directory with proper permissions
RUN mkdir -p /tmp/tts-app-audio && chown appuser:appuser /tmp/tts-app-audio

# Switch to non-root user
USER appuser

# Environment configuration defaults
ENV HOST=0.0.0.0 \
    PORT=8000 \
    AUDIO_STORAGE_DIR=/tmp/tts-app-audio \
    LOG_FORMAT=json \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Health check: verify the backend is responding
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with uvicorn, serving the FastAPI app
# The --proxy-headers flag is included for potential reverse proxy use.
# Graceful shutdown: uvicorn handles SIGTERM natively (default 10s grace period).
WORKDIR /app/backend
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--proxy-headers", \
     "--timeout-graceful-shutdown", "15"]
