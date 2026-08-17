import httpx
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any

from app.providers.base import SportsProvider, ProviderStatus
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo, TennisMatchPlayers
from app.utils.time import utc_now, format_iso_datetime


class TennisProvider(SportsProvider):
    """
    Tennis Provider covering Grand Slams (Wimbledon, US Open, Roland Garros, Australian Open),
    ATP Tour, WTA Tour, ATP Masters 1000, and Davis Cup.
    """
    def __init__(self, api_key: Optional[str] = None, enabled: bool = True):
        super().__init__(name="TennisProvider", enabled=enabled)
        self.api_key = api_key or ""
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            enabled=self.enabled,
            status="healthy" if self.enabled else "disabled",
            supportsSports=["tennis"],
            supportsBroadcasters=True,
            requestsToday=self.requests_today,
            lastError=self.last_error,
            lastRequestAt=format_iso_datetime(self.last_request_at),
        )

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        return []

    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        return []

    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        return []

    async def get_event(self, event_id: str) -> Optional[Event]:
        return None
