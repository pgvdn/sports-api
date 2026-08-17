import httpx
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.providers.base import SportsProvider, ProviderStatus
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo, VenueInfo
from app.models.broadcaster import BroadcasterInfo
from app.utils.time import utc_now, parse_iso_datetime, format_iso_datetime
from app.utils.logging import logger
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event

# South American domestic leagues to exclude
EXCLUDED_LEAGUE_KEYWORDS = {
    "argentinian",          # Argentinian Primera Division (TheSportsDB naming)
    "primera division",     # Argentine Primera División
    "primera nacional",     # Argentine Segunda División
    "liga profesional",     # Argentine top flight (alternate name)
    "brasileirao",          # Brazilian Série A
    "serie a brasil",       # Brazilian Série A (alternate)
    "serie b brasil",       # Brazilian Série B
    "campeonato brasileiro",
    "copa libertadores",
    "copa sudamericana",
    "recopa sudamericana",
    "liga mx",              # Mexican league (optional: remove if you want Liga MX)
}



class ApiFootballProvider(SportsProvider):
    """
    API-Football / API-Sports provider.
    Works with either API-Sports direct (x-apisports-key) or RapidAPI (x-rapidapi-key).
    Automatically disables if API key is not configured.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://v3.football.api-sports.io",
        enabled: bool = True,
    ):
        is_enabled = enabled and bool(api_key and api_key.strip())
        super().__init__(name="API-Football", enabled=is_enabled)
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
            supportsSports=["soccer"],
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

            # Check remaining quota from API response headers
            remaining = response.headers.get("x-ratelimit-requests-remaining")
            if remaining and remaining.isdigit():
                self.remaining_requests = int(remaining)

            if response.status_code == 429 or (self.remaining_requests is not None and self.remaining_requests <= 0):
                self.record_rate_limit()
                self.record_error("Daily request limit reached (429)")
                logger.warning(f"[{self.name}] Quota exhausted on {endpoint}")
                return None

            if response.status_code != 200:
                self.record_error(f"HTTP {response.status_code}")
                return None

            data = response.json()
            # Check for API-level errors
            if data.get("errors"):
                err_msg = str(data["errors"])
                self.record_error(err_msg)
                logger.warning(f"[{self.name}] API returned error: {err_msg}")
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
        if s in ("1H", "2H", "ET", "P", "LIVE"):
            return EventStatus.LIVE
        if s in ("HT", "BT"):
            return EventStatus.HALFTIME
        if s in ("FT", "AET", "PEN"):
            return EventStatus.FINISHED
        if s in ("SUSP", "INT"):
            return EventStatus.BREAK
        if s in ("PST",):
            return EventStatus.POSTPONED
        if s in ("CANC", "ABD"):
            return EventStatus.CANCELLED
        return EventStatus.SCHEDULED

    def _parse_fixture(self, raw: Dict[str, Any]) -> Optional[Event]:
        try:
            fixture = raw.get("fixture", {})
            league = raw.get("league", {})
            teams = raw.get("teams", {})
            goals = raw.get("goals", {})

            fixture_id = str(fixture.get("id"))
            if not fixture_id:
                return None

            start_time_iso = fixture.get("date")
            start_dt = parse_iso_datetime(start_time_iso)
            if not start_dt:
                start_dt = utc_now()
            start_time_str = format_iso_datetime(start_dt)

            short_status = fixture.get("status", {}).get("short")
            status = self._map_status(short_status)

            home_team = teams.get("home", {})
            away_team = teams.get("away", {})

            home_name = home_team.get("name", "Home")
            away_name = away_team.get("name", "Away")

            score = None
            if goals.get("home") is not None or goals.get("away") is not None:
                score = EventScore(
                    home=goals.get("home"),
                    away=goals.get("away"),
                    currentPeriod=fixture.get("status", {}).get("elapsed") and f"{fixture['status']['elapsed']}'",
                    displayScore=f"{goals.get('home', 0)} - {goals.get('away', 0)}",
                )

            venue = None
            if fixture.get("venue", {}).get("name"):
                venue = VenueInfo(
                    name=fixture["venue"]["name"],
                    city=fixture["venue"].get("city"),
                )

            league_name = league.get("name", "Soccer League")
            if any(kw in league_name.lower() for kw in EXCLUDED_LEAGUE_KEYWORDS):
                return None

            clean_league_slug = league_name.lower().replace(" ", "_")[:12]
            canonical_id = f"soccer_{clean_league_slug}_{fixture_id}"

            broadcasters = get_curated_broadcasters_for_event(
                sport="soccer",
                league_name=league_name,
                home_name=home_name,
                away_name=away_name,
            )

            return Event(
                id=canonical_id,
                externalIds={"apiFootball": fixture_id},
                sport="soccer",
                league=LeagueInfo(
                    id=str(league.get("id", "generic")),
                    name=league_name,
                    country=league.get("country"),
                    logo=league.get("logo"),
                    season=str(league.get("season", "")),
                    round=league.get("round"),
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
                startTime=start_time_str,
                status=status,
                score=score,
                venue=venue,
                broadcasters=broadcasters,
            )
        except Exception as exc:
            logger.error(f"[{self.name}] Parse fixture error: {exc}")
            return None

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        if sport and sport.lower() != "soccer":
            return []
        data = await self._fetch_json("fixtures", params={"live": "all"})
        if not data or not data.get("response"):
            return []
        return [ev for raw in data["response"] if (ev := self._parse_fixture(raw)) is not None]

    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        if sport and sport.lower() != "soccer":
            return []
        d_str = target_date.strftime("%Y-%m-%d")
        data = await self._fetch_json("fixtures", params={"date": d_str})
        if not data or not data.get("response"):
            return []
        return [ev for raw in data["response"] if (ev := self._parse_fixture(raw)) is not None]

    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        if sport and sport.lower() != "soccer":
            return []
        today = utc_now().date()
        return await self.get_events_by_date(today, sport=sport)

    async def get_event(self, event_id: str) -> Optional[Event]:
        clean_id = event_id.split("_")[-1]
        data = await self._fetch_json("fixtures", params={"id": clean_id})
        if not data or not data.get("response") or len(data["response"]) == 0:
            return None
        return self._parse_fixture(data["response"][0])
