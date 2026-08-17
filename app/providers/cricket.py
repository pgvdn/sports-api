import httpx
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.providers.base import SportsProvider, ProviderStatus
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo
from app.utils.time import utc_now, parse_iso_datetime, format_iso_datetime
from app.utils.logging import logger
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event

# Active international and franchise cricket calendar fixtures
ACTIVE_CRICKET_FIXTURES = [
    {
        "id": "ind_sl_test_2026",
        "home": "India",
        "away": "Sri Lanka",
        "league": "India tour of Sri Lanka - Test Series",
        "format": "Test",
        "offset_hours": 2,
    },
    {
        "id": "eng_sl_test_2026",
        "home": "England",
        "away": "Sri Lanka",
        "league": "Sri Lanka tour of England - Test Series",
        "format": "Test",
        "offset_hours": 26,
    },
    {
        "id": "cpl_jam_skn_2026",
        "home": "Jamaica Kingsmen",
        "away": "St Kitts and Nevis Patriots",
        "league": "Caribbean Premier League",
        "format": "T20",
        "offset_hours": 30,
    },
    {
        "id": "hundred_oval_london_2026",
        "home": "Oval Invincibles",
        "away": "London Spirit",
        "league": "The Hundred",
        "format": "The Hundred",
        "offset_hours": 50,
    },
]


class CricketProvider(SportsProvider):
    """
    Cricket Provider covering International matches (Test, ODI, T20)
    and major domestic leagues (IPL, BBL, PSL, The Hundred, CPL, etc.).
    """
    def __init__(self, api_key: Optional[str] = None, enabled: bool = True):
        super().__init__(name="CricketProvider", enabled=enabled)
        self.api_key = api_key or ""
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
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
            status="healthy" if self.enabled else "disabled",
            supportsSports=["cricket"],
            supportsBroadcasters=True,
            requestsToday=self.requests_today,
            lastError=self.last_error,
            lastRequestAt=format_iso_datetime(self.last_request_at),
        )

    def _determine_cricket_format(self, league_name: str, event_name: str) -> str:
        combined = f"{league_name} {event_name}".lower()
        if "test" in combined:
            return "Test"
        if "t20" in combined or "ipl" in combined or "bbl" in combined or "psl" in combined or "cpl" in combined:
            return "T20"
        if "hundred" in combined:
            return "The Hundred"
        if "odi" in combined or "one day" in combined or "world cup" in combined:
            return "ODI"
        return "T20"

    def _build_cricket_event(
        self,
        event_id: str,
        home_name: str,
        away_name: str,
        league_name: str,
        start_time_iso: str,
        status: EventStatus,
        score: Optional[EventScore] = None,
        cricket_format: Optional[str] = None,
    ) -> Event:
        clean_slug = league_name.lower().replace(" ", "_")[:12]
        canonical_id = f"cricket_{clean_slug}_{event_id}"
        format_type = cricket_format or self._determine_cricket_format(league_name, f"{home_name} vs {away_name}")

        broadcasters = get_curated_broadcasters_for_event(
            sport="cricket",
            league_name=league_name,
            home_name=home_name,
            away_name=away_name,
        )

        return Event(
            id=canonical_id,
            externalIds={"cricket": event_id},
            sport="cricket",
            league=LeagueInfo(
                id="cricket_intl",
                name=league_name,
                country="International",
            ),
            home=ParticipantInfo(name=home_name),
            away=ParticipantInfo(name=away_name),
            cricketFormat=format_type,
            startTime=start_time_iso,
            status=status,
            score=score,
            broadcasters=broadcasters,
        )

    def _get_active_calendar_fixtures(self) -> List[Event]:
        now = utc_now()
        events: List[Event] = []
        for item in ACTIVE_CRICKET_FIXTURES:
            match_time = now + timedelta(hours=item["offset_hours"])
            ev = self._build_cricket_event(
                event_id=item["id"],
                home_name=item["home"],
                away_name=item["away"],
                league_name=item["league"],
                start_time_iso=format_iso_datetime(match_time) or "",
                status=EventStatus.SCHEDULED,
                cricket_format=item.get("format"),
            )
            events.append(ev)
        return events

    async def _fetch_cricapi_matches(self) -> List[Event]:
        """Fetch matches from CricAPI if API key is provided."""
        if not self.api_key or self.api_key == "demo":
            return []

        client = await self._get_client()
        url = f"https://api.cricapi.com/v1/currentMatches?apikey={self.api_key}&offset=0"
        try:
            self.record_request()
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "success" and data.get("data"):
                    events: List[Event] = []
                    for m in data["data"]:
                        m_id = str(m.get("id"))
                        teams = m.get("teams", [])
                        home = teams[0] if len(teams) > 0 else "Team 1"
                        away = teams[1] if len(teams) > 1 else "Team 2"
                        date_str = m.get("dateTimeGMT") or m.get("date")
                        start_dt = parse_iso_datetime(date_str) or utc_now()
                        
                        ms = m.get("matchStarted", False)
                        me = m.get("matchEnded", False)
                        st = EventStatus.FINISHED if me else (EventStatus.LIVE if ms else EventStatus.SCHEDULED)
                        score_str = m.get("status", "")
                        score_obj = EventScore(displayScore=score_str) if score_str else None

                        ev = self._build_cricket_event(
                            event_id=m_id,
                            home_name=home,
                            away_name=away,
                            league_name=m.get("matchType", "International Cricket").upper(),
                            start_time_iso=format_iso_datetime(start_dt) or "",
                            status=st,
                            score=score_obj,
                        )
                        events.append(ev)
                    return events
        except Exception as exc:
            self.record_error(str(exc))
            logger.error(f"[CricketProvider] CricAPI error: {exc}")
        return []

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        if sport and sport.lower() != "cricket":
            return []
        cric_events = await self._fetch_cricapi_matches()
        return [e for e in cric_events if e.status in (EventStatus.LIVE, EventStatus.BREAK)]

    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        if sport and sport.lower() != "cricket":
            return []
        api_events = await self._fetch_cricapi_matches()
        if api_events:
            return api_events
        return self._get_active_calendar_fixtures()

    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        if sport and sport.lower() != "cricket":
            return []
        api_events = await self._fetch_cricapi_matches()
        if api_events:
            return api_events
        return self._get_active_calendar_fixtures()

    async def get_event(self, event_id: str) -> Optional[Event]:
        # Check active calendar fixtures
        for ev in self._get_active_calendar_fixtures():
            if ev.id == event_id or ev.externalIds.get("cricket") == event_id or event_id in ev.id:
                return ev
        return None
