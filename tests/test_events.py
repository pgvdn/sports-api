import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo
from app.models.broadcaster import BroadcasterInfo


@pytest.mark.asyncio
async def test_get_supported_sports(client: AsyncClient):
    response = await client.get("/api/v1/sports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    sport_ids = [s["id"] for s in data]
    assert "soccer" in sport_ids
    assert "basketball" in sport_ids
    assert "cricket" in sport_ids
    assert "tennis" in sport_ids


@pytest.mark.asyncio
async def test_get_live_events(client: AsyncClient, sample_soccer_event: Event):
    with patch("app.services.event_service.EventService.get_live_events", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [sample_soccer_event]

        response = await client.get("/api/v1/events/live")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["home"]["name"] == "Arsenal"
        assert data["events"][0]["status"] == "LIVE"


@pytest.mark.asyncio
async def test_get_today_events(client: AsyncClient, sample_soccer_event: Event):
    with patch("app.services.event_service.EventService.get_today_events", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [sample_soccer_event]

        response = await client.get("/api/v1/events/today?timezone=America/New_York")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["events"][0]["id"] == "soccer_epl_123456"


@pytest.mark.asyncio
async def test_get_upcoming_events(client: AsyncClient, sample_soccer_event: Event):
    with patch("app.services.event_service.EventService.get_upcoming_events", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [sample_soccer_event]

        response = await client.get("/api/v1/events/upcoming?sport=soccer&hours=48")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.asyncio
async def test_get_event_by_id(client: AsyncClient, sample_soccer_event: Event):
    with patch("app.services.event_service.EventService.get_event_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_soccer_event

        response = await client.get("/api/v1/events/soccer_epl_123456")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "soccer_epl_123456"
        assert data["home"]["name"] == "Arsenal"


@pytest.mark.asyncio
async def test_get_event_channels(client: AsyncClient, sample_soccer_event: Event):
    with patch("app.services.event_service.EventService.get_event_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_soccer_event

        response = await client.get("/api/v1/events/soccer_epl_123456/channels")
        assert response.status_code == 200
        data = response.json()
        assert data["eventId"] == "soccer_epl_123456"
        assert len(data["broadcasters"]) >= 2
        names = [b["name"] for b in data["broadcasters"]]
        assert "Sky Sports Main Event" in names
        assert "USA Network" in names


@pytest.mark.asyncio
async def test_match_playlist_channels_endpoint(client: AsyncClient, sample_soccer_event: Event):
    with patch("app.services.event_service.EventService.get_event_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_soccer_event

        payload = {
            "channels": [
                {"id": "1001", "name": "UK | SKY SPORTS MAIN EVENT FHD"},
                {"id": "1002", "name": "USA NETWORK HD"},
                {"id": "1003", "name": "SKY MOVIES ACTION HD"},
            ],
            "threshold": 0.80,
        }

        response = await client.post("/api/v1/events/soccer_epl_123456/match-channels", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["eventId"] == "soccer_epl_123456"
        assert len(data["matches"]) == 2
        matched_ids = [m["channel"]["id"] for m in data["matches"]]
        assert "1001" in matched_ids
        assert "1002" in matched_ids
        assert "1003" not in matched_ids
