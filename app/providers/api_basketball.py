import httpx
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.providers.base import SportsProvider, ProviderStatus
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo, VenueInfo
from app.utils.time import utc_now, parse_iso_datetime, format_iso_datetime
from app.utils.logging import logger
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event


class ApiBasketballProvider(SportsProvider):
    """
    API-Basketball provider (API-Sports).
    Prioritizes NBA coverage with team names, game status, scores, start times, and broadcasts.
    Automatically disables if API key is not configured.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://v1.basketball.api-sports.io",
        enabled: bool = True,
    ):
        is_enabled = enabled and bool(api_key and api_key.strip())
        super().__init__(name="API-Basketball", enabled=is_enabled)
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self._http_client: Optional[httpx.AsyncClient] = None
        self.remaining_requests: Optional[int] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            headers = {
                "x-apisports-key": self.api_key,
                "x-rapidapi-key": self.api_key,
            }
            self._http_client = httpx.AsyncClient(headers=headers, timeout=10.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    def get_status(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            enabled=self.enabled,
            status="healthy" if self.enabled and not self.is_rate_limited else ("disabled" if not self.enabled else "rate_limited"),
            supportsSports=["basketball"],
            supportsBroadcasters=False,
            requestsToday=self.requests_today,
            remainingRequests=self.remaining_requests,
            lastError=self.last_error,
            lastRequestAt=format_iso_datetime(self.last_request_at),
        )

    async def _fetch_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.enabled or self.is_rate_limited:
            return None

        url = f"{self.base_url}/{endpoint}"
        client = await self._get_client()

        try:
            self.record_request()
            response = await client.get(url, params=params)

            remaining = response.headers.get("x-ratelimit-requests-remaining")
            if remaining and remaining.isdigit():
                self.remaining_requests = int(remaining)

            if response.status_code == 429 or (self.remaining_requests is not None and self.remaining_requests <= 0):
                self.record_rate_limit()
                self.record_error("Daily request limit reached (429)")
                return None

            if response.status_code != 200:
                self.record_error(f"HTTP {response.status_code}")
                return None

            data = response.json()
            if data.get("errors"):
                self.record_error(str(data["errors"]))
                return None

            return data
        except Exception as exc:
            self.record_error(str(exc))
            logger.error(f"[{self.name}] Request error: {exc}")
            return None

    def _map_status(self, short_status: Optional[str]) -> EventStatus:
        if not short_status:
            return EventStatus.SCHEDULED
        s = short_status.strip().upper()
        if s in ("Q1", "Q2", "Q3", "Q4", "OT", "LIVE", "IN PLAY"):
            return EventStatus.LIVE
        if s in ("HT", "HALF"):
            return EventStatus.HALFTIME
        if s in ("FT", "AOT", "FINAL", "ENDED"):
            return EventStatus.FINISHED
        if s in ("POSTP.", "POSTPONED", "PST"):
            return EventStatus.POSTPONED
        if s in ("CANC.", "CANCELLED", "CANCELED"):
            return EventStatus.CANCELLED
        return EventStatus.SCHEDULED

    def _parse_game(self, raw: Dict[str, Any]) -> Optional[Event]:
        try:
            game_id = str(raw.get("id"))
            if not game_id:
                return None

            date_str = raw.get("date")
            start_dt = parse_iso_datetime(date_str) or utc_now()
            start_time_iso = format_iso_datetime(start_dt)

            status_obj = raw.get("status", {})
            status = self._map_status(status_obj.get("short"))

            league = raw.get("league", {})
            teams = raw.get("teams", {})
            scores = raw.get("scores", {})

            home_team = teams.get("home", {})
            away_team = teams.get("away", {})
            home_name = home_team.get("name", "Home")
            away_name = away_team.get("name", "Away")

            home_pts = scores.get("home", {}).get("total")
            away_pts = scores.get("away", {}).get("total")

            score = None
            if home_pts is not None or away_pts is not None:
                score = EventScore(
                    home=home_pts,
                    away=away_pts,
                    currentPeriod=status_obj.get("short"),
                    displayScore=f"{home_pts or 0} - {away_pts or 0}",
                )

            league_name = league.get("name", "NBA")
            clean_league_slug = league_name.lower().replace(" ", "_")[:12]
            canonical_id = f"basketball_{clean_league_slug}_{game_id}"

            broadcasters = get_curated_broadcasters_for_event(
                sport="basketball",
                league_name=league_name,
                home_name=home_name,
                away_name=away_name,
            )

            return Event(
                id=canonical_id,
                externalIds={"apiBasketball": game_id},
                sport="basketball",
                league=LeagueInfo(
                    id=str(league.get("id", "12")),  # 12 is standard NBA in api-basketball
                    name=league_name,
                    country=league.get("country", {}).get("name") if isinstance(league.get("country"), dict) else league.get("country"),
                    logo=league.get("logo"),
                    season=str(raw.get("season", "")),
                ),
                home=ParticipantInfo(
                    id=str(home_team.get("id", "")),
                    name=home_name,
                    logo=home_team.get("logo"),
                ),
                away=ParticipantInfo(
                    id=str(away_team.get("id", "")),
                    name=away_name,
                    logo=away_team.get("logo"),
                ),
                startTime=start_time_iso,
                status=status,
                score=score,
                broadcasters=broadcasters,
            )
        except Exception as exc:
            logger.error(f"[{self.name}] Parse game error: {exc}")
            return None

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        if sport and sport.lower() != "basketball":
            return []
        data = await self._fetch_json("games", params={"live": "all"})
        if not data or not data.get("response"):
            return []
        return [ev for raw in data["response"] if (ev := self._parse_game(raw)) is not None]

    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        if sport and sport.lower() != "basketball":
            return []
        d_str = target_date.strftime("%Y-%m-%d")
        data = await self._fetch_json("games", params={"date": d_str})
        if not data or not data.get("response"):
            return []
        return [ev for raw in data["response"] if (ev := self._parse_game(raw)) is not None]

    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        if sport and sport.lower() != "basketball":
            return []
        today = utc_now().date()
        return await self.get_events_by_date(today, sport=sport)

    async def get_event(self, event_id: str) -> Optional[Event]:
        clean_id = event_id.split("_")[-1]
        data = await self._fetch_json("games", params={"id": clean_id})
        if not data or not data.get("response") or len(data["response"]) == 0:
            return None
        return self._parse_game(data["response"][0])
