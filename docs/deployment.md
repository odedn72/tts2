# TTS Reader - Deployment Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- API keys for at least one TTS provider (Google Cloud TTS, Amazon Polly, ElevenLabs, or OpenAI)
- For local development without Docker: Python 3.11+, Node.js 20+, ffmpeg

## Quick Start (Docker)

### 1. Configure Environment

Copy the example environment file and fill in your API keys:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your provider credentials:

```env
# At least one provider must be configured
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
ELEVENLABS_API_KEY=your_elevenlabs_key
OPENAI_API_KEY=your_openai_key
```

### 2. Build and Run

```bash
# Build the image
docker compose build

# Start the application
docker compose up -d

# Check it is running
docker compose ps
docker compose logs -f
```

The application will be available at **http://localhost:8000**.

### 3. Verify Health

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "dependencies": {
    "ffmpeg": {
      "available": true,
      "path": "/usr/bin/ffmpeg"
    }
  }
}
```

### 4. Stop

```bash
docker compose down
```

To also remove the audio volume:
```bash
docker compose down -v
```

## Development Mode (Docker)

Development mode mounts source code into the containers and enables hot reload for both backend and frontend.

```bash
# Start development services
docker compose --profile dev up

# Backend: http://localhost:8000 (uvicorn with --reload)
# Frontend: http://localhost:5173 (Vite dev server with HMR)
```

Changes to `backend/src/` will automatically reload the backend. Changes to `frontend/src/` will trigger Vite HMR.

## Development Mode (Local, No Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Ensure ffmpeg is installed
brew install ffmpeg  # macOS
# or: sudo apt-get install ffmpeg  # Ubuntu/Debian

# Create .env from template
cp .env.example .env
# Edit .env with your API keys

# Run dev server
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server starts at http://localhost:5173 and proxies `/api` requests to the backend at http://localhost:8000.

## Docker Image Details

### Multi-Stage Build

The Dockerfile uses three stages to minimize the final image size:

1. **frontend-build** (Node 20 Alpine) - Builds the React/Vite frontend into static assets
2. **backend-build** (Python 3.11 slim) - Installs Python dependencies into a virtual environment
3. **runtime** (Python 3.11 slim) - Combines built assets with ffmpeg and runs the application

### Image Properties

- Base: `python:3.11-slim`
- Non-root user: `appuser` (UID 1000)
- System dependencies: ffmpeg, curl (for health checks)
- Exposed port: 8000
- Health check: `GET /api/health` every 30 seconds

### Build the Image Manually

```bash
docker build -t tts-reader .
docker run -p 127.0.0.1:8000:8000 --env-file backend/.env tts-reader
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` (local) / `0.0.0.0` (Docker) | Server bind address |
| `PORT` | `8000` | Server port |
| `AUDIO_STORAGE_DIR` | `/tmp/tts-app-audio` | Directory for generated audio files |
| `LOG_FORMAT` | `text` (local) / `json` (Docker) | Log output format: `text` or `json` |
| `LOG_LEVEL` | `INFO` | Python log level: DEBUG, INFO, WARNING, ERROR |
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Path to Google Cloud service account JSON |
| `AWS_ACCESS_KEY_ID` | - | AWS access key for Amazon Polly |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key for Amazon Polly |
| `AWS_REGION` | `us-east-1` | AWS region for Amazon Polly |
| `ELEVENLABS_API_KEY` | - | ElevenLabs API key |
| `OPENAI_API_KEY` | - | OpenAI API key |

## Health Check

The `GET /api/health` endpoint returns:
- `status`: `"healthy"` (all dependencies OK) or `"degraded"` (ffmpeg missing)
- `version`: Application version
- `dependencies.ffmpeg`: Whether ffmpeg is available

Docker uses this endpoint for container health monitoring. The container is marked unhealthy after 3 consecutive failures.

## Observability

### Structured Logging

In production (`LOG_FORMAT=json`), all log output is JSON-structured:

```json
{
  "timestamp": "2026-02-28T12:00:00+00:00",
  "level": "INFO",
  "logger": "src.middleware",
  "message": "GET /api/providers -> 200 [abc-123-def] 15.2ms",
  "request_id": "abc-123-def"
}
```

### Request ID

Every request is assigned a unique `X-Request-ID` header (UUID). If the incoming request already has this header (e.g., from a reverse proxy), it is preserved. The ID appears in:
- Response headers (`X-Request-ID`)
- Log entries (`request_id` field)

### Graceful Shutdown

The application handles `SIGTERM` gracefully:
1. Uvicorn receives SIGTERM and starts shutdown
2. In-flight requests are given 15 seconds to complete
3. The application logs the shutdown event
4. The process exits cleanly

This ensures no audio generation jobs are abruptly terminated during container stops or rolling deployments.

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

| Job | Steps |
|-----|-------|
| **Backend** | Lint (Ruff) -> Test (pytest with coverage) |
| **Frontend** | Type check (tsc) -> Test (vitest) |
| **Docker Build** | Build image -> Verify health check (main branch only) |

## Troubleshooting

### Container shows "unhealthy"

```bash
# Check logs
docker compose logs app

# Test health endpoint manually
docker compose exec app curl http://localhost:8000/api/health
```

### "degraded" status

The ffmpeg binary is missing. This should not happen with the provided Dockerfile, but verify:

```bash
docker compose exec app ffmpeg -version
```

### API keys not working

Keys are loaded from `backend/.env` via the `env_file` directive in docker-compose.yml. Verify:

```bash
# Check the env file is readable
cat backend/.env

# Check environment inside the container (be careful not to log keys)
docker compose exec app env | grep -c "API_KEY"
```

### Permission denied on audio storage

The audio directory must be writable by the `appuser` (UID 1000):

```bash
docker compose exec app ls -la /tmp/tts-app-audio
```
