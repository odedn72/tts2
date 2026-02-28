"""
GET /api/providers endpoint.

Lists all registered TTS providers with capabilities and configuration status.
"""

from fastapi import APIRouter, Request

from src.api.schemas import ProviderInfo

providers_router = APIRouter()


@providers_router.get("/providers")
async def list_providers(request: Request) -> dict:
    """
    List all registered TTS providers with their capabilities and
    configuration status.
    """
    registry = request.app.state.provider_registry
    providers: list[ProviderInfo] = registry.list_providers()
    return {"providers": [p.model_dump(mode="json") for p in providers]}
