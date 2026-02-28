"""
GET /api/settings and PUT /api/settings endpoints.

Manages provider API key configuration status.
Never exposes actual key values in responses (NFR-004).
"""

from fastapi import APIRouter, Request

from src.api.schemas import (
    ProviderKeyStatus,
    ProviderName,
    SettingsResponse,
    UpdateSettingsRequest,
)

settings_router = APIRouter()


@settings_router.get("/settings")
async def get_settings(request: Request) -> dict:
    """
    Get current provider configuration status.

    Returns is_configured status for each provider. NEVER returns
    actual API key values.
    """
    config = request.app.state.runtime_config
    provider_names = [
        ProviderName.GOOGLE,
        ProviderName.AMAZON,
        ProviderName.ELEVENLABS,
        ProviderName.OPENAI,
    ]

    statuses = [
        ProviderKeyStatus(
            provider=name,
            is_configured=config.is_provider_configured(name),
        )
        for name in provider_names
    ]

    resp = SettingsResponse(providers=statuses)
    return resp.model_dump(mode="json")


@settings_router.put("/settings")
async def update_settings(request: Request, body: UpdateSettingsRequest) -> dict:
    """
    Update a provider's API key.

    The key is stored in runtime settings (in-memory for this session).
    Response confirms the update but NEVER echoes the key back.
    """
    config = request.app.state.runtime_config
    config.set_provider_key(body.provider, body.api_key)

    return ProviderKeyStatus(
        provider=body.provider,
        is_configured=True,
    ).model_dump(mode="json")
