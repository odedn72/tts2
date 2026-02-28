"""
GET /api/health endpoint.

Returns application health status including version and dependency checks.
Used by Docker health checks and monitoring.
"""

import shutil

from fastapi import APIRouter

health_router = APIRouter()

# Read version from pyproject.toml at module level would require toml parsing.
# Instead, we use the version from the package metadata or a constant.
APP_VERSION = "0.1.0"


def _check_ffmpeg() -> dict:
    """Check if ffmpeg is available on the system PATH."""
    ffmpeg_path = shutil.which("ffmpeg")
    return {
        "available": ffmpeg_path is not None,
        "path": ffmpeg_path,
    }


@health_router.get("/health")
async def health_check() -> dict:
    """
    Application health check.

    Returns:
        - status: "healthy" or "degraded"
        - version: application version string
        - dependencies.ffmpeg: whether ffmpeg is installed and reachable
    """
    ffmpeg_status = _check_ffmpeg()

    # Overall status: degraded if ffmpeg is missing (audio processing will fail)
    overall_status = "healthy" if ffmpeg_status["available"] else "degraded"

    return {
        "status": overall_status,
        "version": APP_VERSION,
        "dependencies": {
            "ffmpeg": ffmpeg_status,
        },
    }
