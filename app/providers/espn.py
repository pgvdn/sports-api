import httpx
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.providers.base import SportsProvider, ProviderStatus
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo, TennisMatchPlayers, VenueInfo
from app.models.broadcaster import BroadcasterInfo
from app.utils.time import utc_now, parse_iso_datetime, format_iso_datetime
from app.utils.normalization import normalize_channel_name
from app.utils.logging import logger
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event

SOCCER_LEAGUE_SLUGS = [
    # Domestic Cups
    ("ita.coppa_italia", "Coppa Italia", "Italy"),
    ("eng.fa", "Emirates FA Cup", "England"),
    ("eng.league_cup", "Carabao Cup", "England"),
    ("esp.copa_del_rey", "Copa del Rey", "Spain"),
    ("ger.dfb_pokal", "DFB-Pokal", "Germany"),
    ("fra.coupe_de_france", "Coupe de France", "France"),
    ("usa.open", "U.S. Open Cup", "United States"),
    # Domestic Leagues
    ("eng.1", "English Premier League", "England"),
    ("esp.1", "Spanish La Liga", "Spain"),
    ("ita.1", "Italian Serie A", "Italy"),
    ("ger.1", "German Bundesliga", "Germany"),
    ("fra.1", "French Ligue 1", "France"),
    ("usa.1", "Major League Soccer", "United States"),
    ("sau.1", "Saudi Pro League", "Saudi Arabia"),
    ("por.1", "Portuguese Primeira Liga", "Portugal"),
    ("ned.1", "Dutch Eredivisie", "Netherlands"),
    ("sco.1", "Scottish Premiership", "Scotland"),
    # European & International Club
    ("uefa.champions", "UEFA Champions League", "Europe"),
    ("uefa.europa", "UEFA Europa League", "Europe"),
    ("uefa.europa.conf", "UEFA Conference League", "Europe"),
    ("uefa.super_cup", "UEFA Super Cup", "Europe"),
    ("fifa.cwc", "FIFA Club World Cup", "Worldwide"),
]

BASKETBALL_LEAGUE_SLUGS = [
    ("nba", "NBA", "United States"),
    ("mens-college-basketball", "NCAA Basketball", "United States"),
]

NFL_LEAGUE_SLUGS = [
    ("nfl", "NFL", "United States"),
]

F1_LEAGUE_SLUGS = [
    ("f1", "Formula 1", "International"),
]


class EspnPublicProvider(SportsProvider):
    """
    High-reliability, zero-key public sports data provider.
    Delivers live scores, real-time match statuses, domestic cups, and schedules.
    """
    def __init__(self, enabled: bool = True):
        super().__init__(name="ESPN-Public", enabled=enabled)
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports"
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
            supportsSports=["soccer", "basketball", "tennis", "nfl", "f1"],
            supportsBroadcasters=True,
            requestsToday=self.requests_today,
            lastError=self.last_error,
            lastRequestAt=format_iso_datetime(self.last_request_at),
        )

    def _map_espn_status(self, raw_status: Dict[str, Any], start_time: Optional[datetime] = None) -> EventStatus:
        type_info = raw_status.get("type", {})
        state = str(type_info.get("state", "")).lower()
        detail = str(type_info.get("shortDetail", "")).lower()

        if state == "in":
            if "halftime" in detail or "ht" in detail:
                return EventStatus.HALFTIME
            if "delay" in detail or "interrupted" in detail or "break" in detail:
                return EventStatus.BREAK
            return EventStatus.LIVE
        elif state == "post":
            if "postponed" in detail:
                return EventStatus.POSTPONED
            if "canceled" in detail or "cancelled" in detail:
                return EventStatus.CANCELLED
            return EventStatus.FINISHED
        elif state == "pre":
            if start_time:
                now = utc_now()
                if now < start_time <= (now + timedelta(minutes=60)):
                    return EventStatus.STARTING_SOON
            return EventStatus.SCHEDULED

        return EventStatus.SCHEDULED

    def _parse_espn_event(
        self,
        raw_event: Dict[str, Any],
        sport: str,
        league_id: str,
        league_name: str,
        country: str,
    ) -> Optional[Event]:
        try:
            event_id = str(raw_event.get("id", ""))
            if not event_id:
                return None

            date_str = raw_event.get("date")
            start_dt = parse_iso_datetime(date_str) or utc_now()
            start_time_iso = format_iso_datetime(start_dt) or ""

            status_obj = raw_event.get("status", {})
            status = self._map_espn_status(status_obj, start_dt)

            competitions = raw_event.get("competitions", [{}])
            comp = competitions[0] if competitions else {}
            competitors = comp.get("competitors", [])

            home_raw = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0] if competitors else {})
            away_raw = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1] if len(competitors) > 1 else {})

            home_team_info = home_raw.get("team", {})
            away_team_info = away_raw.get("team", {})

            home_name = home_team_info.get("displayName") or home_team_info.get("name") or "Home"
            away_name = away_team_info.get("displayName") or away_team_info.get("name") or "Away"

            home_score = home_raw.get("score")
            away_score = away_raw.get("score")

            score = None
            if home_score is not None or away_score is not None or status == EventStatus.LIVE:
                clock_detail = status_obj.get("type", {}).get("shortDetail")
                score = EventScore(
                    home=home_score,
                    away=away_score,
                    currentPeriod=clock_detail,
                    displayScore=f"{home_score or 0} - {away_score or 0}" if (home_score is not None and away_score is not None) else None,
                )

            # Venue
            venue = None
            venue_raw = comp.get("venue", {})
            if venue_raw.get("fullName"):
                venue = VenueInfo(
                    name=venue_raw["fullName"],
                    city=venue_raw.get("address", {}).get("city"),
                    country=venue_raw.get("address", {}).get("country"),
                )

            # Extract broadcast networks from API response if present
            broadcasters: List[BroadcasterInfo] = []
            seen_tv: set = set()
            for b in comp.get("broadcasts", []):
                for name in b.get("names", []):
                    norm = normalize_channel_name(name)
                    if norm and norm not in seen_tv:
                        seen_tv.add(norm)
                        broadcasters.append(
                            BroadcasterInfo(
                                name=name,
                                normalizedName=norm,
                                country=country,
                                source="espn_api",
                            )
                        )

            # Enrich with verified curated channels
            curated = get_curated_broadcasters_for_event(
                sport=sport,
                league_name=league_name,
                home_name=home_name,
                away_name=away_name,
            )
            for c in curated:
                if c.normalizedName not in seen_tv:
                    seen_tv.add(c.normalizedName)
                    broadcasters.append(c)

            clean_league_slug = league_name.lower().replace(" ", "_")[:12]
            canonical_id = f"{sport}_{clean_league_slug}_{event_id}"

            home_info = ParticipantInfo(
                id=str(home_team_info.get("id", "")),
                name=home_name,
                shortName=home_team_info.get("abbreviation"),
                logo=home_team_info.get("logo"),
            )
            away_info = ParticipantInfo(
                id=str(away_team_info.get("id", "")),
                name=away_name,
                shortName=away_team_info.get("abbreviation"),
                logo=away_team_info.get("logo"),
            )

            tennis_players = None
            if sport == "tennis":
                tennis_players = TennisMatchPlayers(player1=home_info, player2=away_info)

            return Event(
                id=canonical_id,
                externalIds={"espn": event_id},
                sport=sport,
                league=LeagueInfo(
                    id=league_id,
                    name=league_name,
                    country=country,
                ),
                home=home_info,
                away=away_info,
                tennisPlayers=tennis_players,
                startTime=start_time_iso,
                status=status,
                score=score,
                venue=venue,
                broadcasters=broadcasters,
            )
        except Exception as exc:
            logger.error(f"[{self.name}] Error parsing ESPN event: {exc}")
            return None

    async def _fetch_scoreboard(self, sport: str, league_slug: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        client = await self._get_client()
        url = f"{self.base_url}/{sport}/{league_slug}/scoreboard"
        try:
            self.record_request()
            r = await client.get(url, params=params)
            if r.status_code == 200:
                return r.json()
        except Exception as exc:
            self.record_error(str(exc))
            logger.debug(f"[{self.name}] Error on {url}: {exc}")
        return None

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        events: List[Event] = []
        target_sport = (sport or "").lower()

        # Check soccer
        if not target_sport or target_sport in ("soccer", "football"):
            for slug, league_name, country in SOCCER_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("soccer", slug)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "soccer", slug, league_name, country)
                        if ev and ev.status in (EventStatus.LIVE, EventStatus.HALFTIME, EventStatus.BREAK):
                            events.append(ev)

        # Check basketball
        if not target_sport or target_sport in ("basketball", "nba"):
            for slug, league_name, country in BASKETBALL_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("basketball", slug)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "basketball", slug, league_name, country)
                        if ev and ev.status in (EventStatus.LIVE, EventStatus.HALFTIME, EventStatus.BREAK):
                            events.append(ev)

        # Check NFL
        if not target_sport or target_sport in ("nfl", "football_us"):
            for slug, league_name, country in NFL_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("football", slug)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "nfl", slug, league_name, country)
                        if ev and ev.status in (EventStatus.LIVE, EventStatus.HALFTIME, EventStatus.BREAK):
                            events.append(ev)

        # Check F1
        if not target_sport or target_sport in ("f1", "formula1"):
            for slug, league_name, country in F1_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("racing", slug)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "f1", slug, league_name, country)
                        if ev and ev.status in (EventStatus.LIVE, EventStatus.HALFTIME, EventStatus.BREAK):
                            events.append(ev)

        return events

    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        events: List[Event] = []
        date_param = target_date.strftime("%Y%m%d")
        params = {"dates": date_param}
        target_sport = (sport or "").lower()

        if not target_sport or target_sport in ("soccer", "football"):
            for slug, league_name, country in SOCCER_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("soccer", slug, params=params)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "soccer", slug, league_name, country)
                        if ev:
                            events.append(ev)

        if not target_sport or target_sport in ("basketball", "nba"):
            for slug, league_name, country in BASKETBALL_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("basketball", slug, params=params)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "basketball", slug, league_name, country)
                        if ev:
                            events.append(ev)

        if not target_sport or target_sport in ("nfl", "football_us"):
            for slug, league_name, country in NFL_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("football", slug, params=params)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "nfl", slug, league_name, country)
                        if ev:
                            events.append(ev)

        if not target_sport or target_sport in ("f1", "formula1"):
            for slug, league_name, country in F1_LEAGUE_SLUGS:
                data = await self._fetch_scoreboard("racing", slug, params=params)
                if data and data.get("events"):
                    for raw in data["events"]:
                        ev = self._parse_espn_event(raw, "f1", slug, league_name, country)
                        if ev:
                            events.append(ev)

        return events

    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        today = utc_now().date()
        today_events = await self.get_events_by_date(today, sport=sport)
        tomorrow_events = await self.get_events_by_date(today + timedelta(days=1), sport=sport)
        return today_events + tomorrow_events

    async def get_event(self, event_id: str) -> Optional[Event]:
        # Check today and tomorrow cached events
        today_events = await self.get_upcoming_events(hours=48)
        for ev in today_events:
            if ev.id == event_id or ev.externalIds.get("espn") == event_id or event_id in ev.id:
                return ev
        return None
