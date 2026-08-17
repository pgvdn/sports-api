import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.models.event import HomeScreenResponse, HomeSection, Event, EventStatus
from app.models.league import LeagueInfo, ParticipantInfo


@pytest.mark.asyncio
async def test_get_home_screen_feed(client: AsyncClient):
    mock_feed = HomeScreenResponse(
        generatedAt="2026-08-17T13:00:00Z",
        live=[
            Event(
                id="soccer_epl_1",
                sport="soccer",
                league=LeagueInfo(id="4328", name="Premier League"),
                home=ParticipantInfo(name="Arsenal"),
                away=ParticipantInfo(name="Liverpool"),
                startTime="2026-08-17T19:00:00Z",
                status=EventStatus.LIVE,
            )
        ],
        startingSoon=[],
        sections=[
            HomeSection(sport="soccer", title="Football / Soccer", events=[]),
            HomeSection(sport="cricket", title="Cricket", events=[]),
            HomeSection(sport="basketball", title="NBA / Basketball", events=[]),
            HomeSection(sport="tennis", title="Tennis", events=[]),
        ],
    )

    with patch("app.services.event_service.EventService.get_home_screen", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_feed

        response = await client.get("/api/v1/home")
        assert response.status_code == 200
        data = response.json()
        assert "generatedAt" in data
        assert len(data["live"]) == 1
        assert len(data["sections"]) == 4
        sports_in_sections = [s["sport"] for s in data["sections"]]
        assert "soccer" in sports_in_sections
        assert "cricket" in sports_in_sections
        assert "basketball" in sports_in_sections
        assert "tennis" in sports_in_sections
