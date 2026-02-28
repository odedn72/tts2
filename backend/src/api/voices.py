"""
POST /api/voices endpoint.

Fetches available voices for a specific provider.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from src.api.schemas import ProviderName, VoiceListResponse
from src.errors import ProviderNotConfiguredError, ProviderNotFoundError

voices_router = APIRouter()


class VoiceRequest(BaseModel):
    """Request body for the voices endpoint. Accepts a string provider name."""

    provider: str


@voices_router.post("/voices")
async def list_voices(request: Request, body: VoiceRequest) -> dict:
    """
    Fetch available voices for the specified provider.

    Raises:
        ProviderNotFoundError: If the provider is not registered.
        ProviderNotConfiguredError: If the provider has no API key.
        ProviderAPIError: If the provider API call fails.
    """
    registry = request.app.state.provider_registry

    # Validate provider name and look it up in registry
    try:
        provider_name = ProviderName(body.provider)
    except ValueError:
        raise ProviderNotFoundError(body.provider)

    provider = registry.get(provider_name)

    if not provider.is_configured():
        raise ProviderNotConfiguredError(body.provider)

    voices = await provider.list_voices()

    resp = VoiceListResponse(provider=provider_name, voices=voices)
    return resp.model_dump(mode="json")
