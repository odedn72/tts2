"""
Main API router that aggregates all endpoint sub-routers.

All endpoints are prefixed with /api.
"""

from fastapi import APIRouter

from src.api.audio import audio_router
from src.api.generate import generate_router
from src.api.health import health_router
from src.api.providers import providers_router
from src.api.settings import settings_router
from src.api.voices import voices_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(providers_router)
api_router.include_router(voices_router)
api_router.include_router(generate_router)
api_router.include_router(audio_router)
api_router.include_router(settings_router)
