"""
GET /api/audio/{job_id} and GET /api/audio/{job_id}/file endpoints.

Serves audio metadata (with timing) and the raw MP3 file.
"""

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

audio_router = APIRouter()


@audio_router.get("/audio/{job_id}")
async def get_audio_metadata(request: Request, job_id: str) -> dict:
    """
    Get audio metadata and timing data for a completed job.

    Returns duration, format, size, and timing information.
    """
    manager = request.app.state.job_manager
    metadata = manager.get_audio_metadata(job_id)
    return metadata.model_dump(mode="json")


@audio_router.get("/audio/{job_id}/file")
async def get_audio_file(request: Request, job_id: str) -> FileResponse:
    """
    Stream the actual MP3 audio file bytes.

    Returns the file with appropriate Content-Type and Content-Disposition headers.
    """
    manager = request.app.state.job_manager
    file_path = manager.get_audio_file_path(job_id)

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=f"tts-{job_id}.mp3",
        headers={
            "Content-Disposition": f'attachment; filename="tts-{job_id}.mp3"',
        },
    )
