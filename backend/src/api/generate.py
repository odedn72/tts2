"""
POST /api/generate and GET /api/generate/{job_id}/status endpoints.

Handles TTS generation job creation and status polling.
"""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Request

from src.api.schemas import (
    GenerateRequest,
    GenerateResponse,
    GenerationStatus,
    JobStatusResponse,
)

logger = logging.getLogger(__name__)

generate_router = APIRouter()


@generate_router.post("/generate", status_code=202)
async def start_generation(
    request: Request,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Start an asynchronous TTS generation job.

    Returns 202 immediately with the job_id. The actual generation
    runs as a background task.
    """
    manager = request.app.state.job_manager
    job = await manager.create_job(body)

    # Schedule background processing
    background_tasks.add_task(manager.process_job, job.id)

    resp = GenerateResponse(job_id=job.id, status=job.status)
    return resp.model_dump(mode="json")


@generate_router.get("/generate/{job_id}/status")
async def get_job_status(request: Request, job_id: str) -> dict:
    """
    Poll for generation job progress.

    Returns the current status, progress, and any error message.
    """
    manager = request.app.state.job_manager
    job = manager.get_job_status(job_id)

    resp = JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        total_chunks=job.total_chunks,
        completed_chunks=job.completed_chunks,
        error_message=job.error_message,
    )
    return resp.model_dump(mode="json")
