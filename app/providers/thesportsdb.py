import asyncio
import httpx
from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.providers.base import SportsProvider, BroadcastProvider, ProviderStatus
from app.models.event import Event, EventStatus, EventScore, SportType
from app.models.league import LeagueInfo, ParticipantInfo, TennisMatchPlayers, VenueInfo
from app.models.broadcaster import BroadcasterInfo
from app.utils.time import utc_now, parse_iso_datetime, format_iso_datetime
from app.utils.normalization import normalize_channel_name
from app.utils.logging import logger
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event

# Major League IDs in TheSportsDB for reliable upcoming schedule lookups
POPULAR_LEAGUE_IDS = {
    # Soccer (Domestic Leagues & Domestic Cups)
    "soccer": [
        "4328",  # English Premier League
        "4482",  # FA Cup (England)
        "4483",  # EFL Cup / Carabao Cup (England)
        "4480",  # UEFA Champions League
        "4481",  # UEFA Europa League
        "5097",  # UEFA Conference League
        "4335",  # Spanish La Liga
        "4484",  # Copa del Rey (Spain)
        "4332",  # Italian Serie A
        "4486",  # Coppa Italia (Italy)
        "4331",  # German Bundesliga
        "4485",  # DFB-Pokal (Germany)
        "4334",  # French Ligue 1
        "4487",  # Coupe de France (France)
        "4338",  # Scottish Premiership
        "4488",  # Scottish Cup (Scotland)
        "4346",  # American Major League Soccer (MLS)
        "4489",  # US Open Cup (USA)
        "4422",  # Saudi Professional League
        "4490",  # Indian Super League
        "4507",  # FIFA Club World Cup
        "4424",  # Copa Libertadores
    ],
    # Basketball
    "basketball": [
        "4387",  # NBA
        "4408",  # EuroLeague
    ],
    # Cricket
    "cricket": [
        "4460",  # Indian Premier League
        "4461",  # Big Bash League
        "4462",  # Pakistan Super League
        "4464",  # The Hundred
        "4570",  # ICC Men's T20 World Cup
        "4895",  # ICC World Test Championship
    ],
    # Tennis
    "tennis": [
        "4464",  # ATP Tour
        "4465",  # WTA Tour
        "4466",  # Australian Open
        "4467",  # French Open
        "4468",  # Wimbledon
        "4469",  # US Open
    ],
}


class TheSportsDBProvider(SportsProvider, BroadcastProvider):
    def __init__(self, api_key: str = "3", enabled: bool = True):
        super().__init__(name="TheSportsDB", enabled=enabled)
        self.api_key = api_key or "3"
        self.base_url = f"https://www.thesportsdb.com/api/v1/json/{self.api_key}"
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
            status="rate_limited" if self.is_rate_limited else ("healthy" if self.enabled else "disabled"),
            supportsSports=["soccer", "basketball", "cricket", "tennis"],
            supportsBroadcasters=True,
            requestsToday=self.requests_today,
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

            if response.status_code == 429:
                self.record_rate_limit()
                self.record_error("Rate limit reached (HTTP 429)")
                logger.warning(f"[{self.name}] Rate limited on {endpoint}")
                return None

            if response.status_code != 200:
                self.record_error(f"HTTP {response.status_code}")
                return None

            return response.json()
        except httpx.RequestError as exc:
            self.record_error(f"Network error: {str(exc)}")
            logger.error(f"[{self.name}] Request error to {url}: {exc}")
            return None
        except Exception as exc:
            self.record_error(f"Unexpected error: {str(exc)}")
            logger.error(f"[{self.name}] Parse error on {url}: {exc}")
            return None

    def _normalize_sport(self, raw_sport: Optional[str]) -> str:
        if not raw_sport:
            return "soccer"
        s = raw_sport.lower()
        if "soccer" in s or "football" in s:
            return "soccer"
        if "basket" in s or "nba" in s:
            return "basketball"
        if "cricket" in s:
            return "cricket"
        if "tennis" in s:
            return "tennis"
        return s

    def _normalize_status(self, raw_status: Optional[str], start_time: Optional[datetime] = None) -> EventStatus:
        if not raw_status:
            if start_time:
                now = utc_now()
                if start_time <= now <= (start_time + timedelta(hours=3)):
                    return EventStatus.LIVE
                elif now < start_time <= (now + timedelta(minutes=60)):
                    return EventStatus.STARTING_SOON
                elif now < start_time:
                    return EventStatus.SCHEDULED
                else:
                    return EventStatus.FINISHED
            return EventStatus.SCHEDULED

        s = str(raw_status).strip().upper()

        if s in ("1H", "2H", "LIVE", "IN PLAY", "Q1", "Q2", "Q3", "Q4", "OT", "SET 1", "SET 2", "SET 3", "SET 4", "SET 5", "INN 1", "INN 2", "PLAYING"):
            return EventStatus.LIVE
        if s in ("HT", "HALFTIME", "HALF TIME"):
            return EventStatus.HALFTIME
        if s in ("BREAK", "LUNCH", "TEA", "STUMPS", "RAIN DELAY", "INTERRUPTED"):
            return EventStatus.BREAK
        if s in ("FT", "AET", "AP", "FINISHED", "ENDED", "FINAL", "FINAL/OT", "RESULT"):
            return EventStatus.FINISHED
        if s in ("POSTP.", "POSTPONED", "PST"):
            return EventStatus.POSTPONED
        if s in ("CANC.", "CANCELLED", "CANCELED", "ABD", "ABANDONED"):
            return EventStatus.CANCELLED
        if s in ("NS", "NOT STARTED", "PRE-MATCH", "SCHEDULED", "UPCOMING", "TBD"):
            if start_time:
                now = utc_now()
                if now < start_time <= (now + timedelta(minutes=60)):
                    return EventStatus.STARTING_SOON
            return EventStatus.SCHEDULED

        return EventStatus.SCHEDULED

    def _parse_event(self, raw: Dict[str, Any]) -> Optional[Event]:
        try:
            event_id = str(raw.get("idEvent", "")).strip()
            if not event_id:
                return None

            sport = self._normalize_sport(raw.get("strSport"))
            league_id = str(raw.get("idLeague") or raw.get("idLeague_api") or "generic")
            league_name = raw.get("strLeague") or "General League"
            alt_event = raw.get("strEventAlternate") or ""
            home_name = (raw.get("strHomeTeam") or (alt_event.split(" vs ")[0] if " vs " in alt_event else "Home")).strip()
            away_name = (raw.get("strAwayTeam") or (alt_event.split(" vs ")[1] if " vs " in alt_event else "Away")).strip()

            # Parse Start Time
            timestamp_str = raw.get("strTimestamp")
            start_time_dt = parse_iso_datetime(timestamp_str)

            if not start_time_dt:
                date_str = raw.get("dateEvent")
                time_str = raw.get("strTime", "00:00:00")
                if date_str:
                    combined = f"{date_str}T{time_str}"
                    start_time_dt = parse_iso_datetime(combined)

            if not start_time_dt:
                start_time_dt = utc_now()

            start_time_iso = format_iso_datetime(start_time_dt)
            status = self._normalize_status(raw.get("strStatus"), start_time_dt)

            # Score
            home_score = raw.get("intHomeScore")
            away_score = raw.get("intAwayScore")
            score_obj = None
            if home_score is not None or away_score is not None or raw.get("strProgress"):
                score_obj = EventScore(
                    home=home_score,
                    away=away_score,
                    currentPeriod=raw.get("strProgress") or raw.get("strStatus"),
                    displayScore=f"{home_score or 0} - {away_score or 0}" if (home_score is not None and away_score is not None) else None,
                )

            # Participants
            home_info = ParticipantInfo(
                id=str(raw.get("idHomeTeam") or ""),
                name=home_name,
                logo=raw.get("strHomeTeamBadge") or raw.get("strThumb"),
            )
            away_info = ParticipantInfo(
                id=str(raw.get("idAwayTeam") or ""),
                name=away_name,
                logo=raw.get("strAwayTeamBadge"),
            )

            # Tennis specific players model
            tennis_players = None
            if sport == "tennis":
                tennis_players = TennisMatchPlayers(
                    player1=home_info,
                    player2=away_info,
                )

            # Venue
            venue = None
            if raw.get("strVenue"):
                venue = VenueInfo(
                    name=raw.get("strVenue"),
                    city=raw.get("strCity"),
                    country=raw.get("strCountry"),
                )

            # Internal canonical ID format: e.g. soccer_4328_123456
            clean_league_slug = league_name.lower().replace(" ", "_")[:12]
            canonical_id = f"{sport}_{clean_league_slug}_{event_id}"

            # Prepopulate curated broadcasters for instant availability
            broadcasters = get_curated_broadcasters_for_event(
                sport=sport,
                league_name=league_name,
                home_name=home_name,
                away_name=away_name,
            )

            return Event(
                id=canonical_id,
                externalIds={"thesportsdb": event_id},
                sport=sport,
                league=LeagueInfo(
                    id=league_id,
                    name=league_name,
                    country=raw.get("strCountry"),
                    logo=raw.get("strLeagueBadge") or raw.get("strBadge"),
                    season=raw.get("strSeason"),
                    round=raw.get("intRound") or raw.get("strRound"),
                ),
                home=home_info,
                away=away_info,
                tennisPlayers=tennis_players,
                cricketFormat=raw.get("strFormat") if sport == "cricket" else None,
                startTime=start_time_iso,
                status=status,
                score=score_obj,
                venue=venue,
                broadcasters=broadcasters,
            )
        except Exception as exc:
            logger.error(f"[{self.name}] Failed to parse event {raw.get('idEvent')}: {exc}")
            return None

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        """Fetch all live events from TheSportsDB."""
        data = await self._fetch_json("eventslive.php")
        if not data or not data.get("events"):
            return []

        events: List[Event] = []
        for raw in data["events"]:
            parsed = self._parse_event(raw)
            if parsed:
                if sport is None or parsed.sport == sport.lower():
                    events.append(parsed)

        return events

    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        """Fetch events for given date from TheSportsDB."""
        d_str = target_date.strftime("%Y-%m-%d")
        params: Dict[str, Any] = {"d": d_str}
        
        # TheSportsDB eventsday.php supports optional sport parameter (e.g. s=Soccer)
        if sport:
            sport_map = {
                "soccer": "Soccer",
                "basketball": "Basketball",
                "cricket": "Cricket",
                "tennis": "Tennis",
            }
            if sport.lower() in sport_map:
                params["s"] = sport_map[sport.lower()]

        data = await self._fetch_json("eventsday.php", params=params)
        if not data or not data.get("events"):
            return []

        events: List[Event] = []
        for raw in data["events"]:
            parsed = self._parse_event(raw)
            if parsed:
                if sport is None or parsed.sport == sport.lower():
                    events.append(parsed)

        return events

    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        """Fetch upcoming league events concurrently across major competitions."""
        target_sports = [sport.lower()] if sport else ["soccer", "basketball", "cricket", "tennis"]
        all_events: List[Event] = []
        seen_ids: set = set()

        tasks = []
        for s in target_sports:
            league_ids = POPULAR_LEAGUE_IDS.get(s, [])
            for lid in league_ids[:4]:
                tasks.append(self._fetch_json("eventsnextleague.php", params={"id": lid}))

        today = utc_now().date()
        for offset in range(max(1, (hours // 24) + 1)):
            d = today + timedelta(days=offset)
            tasks.append(self.get_events_by_date(d, sport=sport))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, dict) and res.get("events"):
                for raw in res["events"]:
                    parsed = self._parse_event(raw)
                    if parsed and parsed.id not in seen_ids:
                        seen_ids.add(parsed.id)
                        all_events.append(parsed)
            elif isinstance(res, list):
                for ev in res:
                    if isinstance(ev, Event) and ev.id not in seen_ids:
                        seen_ids.add(ev.id)
                        all_events.append(ev)

        return all_events

    async def get_event(self, event_id: str) -> Optional[Event]:
        """Lookup event by ID."""
        # Extract raw external ID if prefixed
        clean_id = event_id.split("_")[-1]
        data = await self._fetch_json("lookupevent.php", params={"id": clean_id})
        if not data or not data.get("events") or len(data["events"]) == 0:
            return None

        return self._parse_event(data["events"][0])

    async def get_broadcasters(self, event: Event) -> List[BroadcasterInfo]:
        """Fetch TV broadcasters for an event via TheSportsDB eventstv.php or curated fallback."""
        raw_id = event.externalIds.get("thesportsdb")
        if not raw_id:
            raw_id = event.id.split("_")[-1]

        broadcasters: List[BroadcasterInfo] = []
        seen_keys: set = set()

        # Call TheSportsDB TV endpoint if available
        if raw_id and raw_id.isdigit():
            data = await self._fetch_json("eventstv.php", params={"id": raw_id})
            if data and data.get("tv"):
                for tv in data["tv"]:
                    name = tv.get("strChannel")
                    if not name:
                        continue
                    norm = normalize_channel_name(name)
                    country = tv.get("strCountry", "International")
                    key = (norm, country)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    broadcasters.append(
                        BroadcasterInfo(
                            name=name,
                            normalizedName=norm,
                            countryCode=tv.get("strCountryCode"),
                            country=country,
                            logo=tv.get("strLogo"),
                            source="thesportsdb",
                        )
                    )

        # Enrich with curated broadcasters if upstream returns empty or few channels
        if len(broadcasters) < 3:
            curated = get_curated_broadcasters_for_event(
                sport=event.sport,
                league_name=event.league.name,
                home_name=event.home.name,
                away_name=event.away.name,
            )
            for c in curated:
                key = (c.normalizedName, c.country or "")
                if key not in seen_keys:
                    seen_keys.add(key)
                    broadcasters.append(c)

        return broadcasters
