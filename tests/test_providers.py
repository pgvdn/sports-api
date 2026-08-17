import pytest
from httpx import AsyncClient
from app.providers.thesportsdb import TheSportsDBProvider
from app.providers.api_football import ApiFootballProvider
from app.providers.registry import get_provider_registry


@pytest.mark.asyncio
async def test_get_providers_status(client: AsyncClient):
    response = await client.get("/api/v1/providers/status")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 4
    names = [p["name"] for p in data["providers"]]
    assert "TheSportsDB" in names
    assert "API-Football" in names
    assert "API-Basketball" in names


def test_thesportsdb_status():
    provider = TheSportsDBProvider(api_key="3", enabled=True)
    status = provider.get_status()
    assert status.name == "TheSportsDB"
    assert status.enabled is True
    assert status.status == "healthy"
    assert "soccer" in status.supportsSports


def test_api_football_auto_disable_without_key():
    provider = ApiFootballProvider(api_key="", enabled=True)
    status = provider.get_status()
    assert status.name == "API-Football"
    assert status.enabled is False
    assert status.status == "disabled"


def test_provider_registry_fallback():
    registry = get_provider_registry()
    soccer_providers = registry.get_providers_for_sport("soccer")
    assert len(soccer_providers) >= 1
    # When API-Football key is missing, it falls back to TheSportsDB
    assert any(p.name == "TheSportsDB" for p in soccer_providers)
