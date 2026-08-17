from datetime import datetime, date, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.config import get_settings
from app.models.event import (
    Event,
    EventStatus,
    EventsListResponse,
    HomeScreenResponse,
    HomeSection,
)
from app.providers.registry import get_provider_registry
from app.services.cache_service import get_cache_service
from app.services.reconciliation import reconcile_events
from app.utils.time import utc_now, parse_iso_datetime, format_iso_datetime, get_day_range_utc
from app.utils.logging import logger

settings = get_settings()


class EventService:
    def __init__(self):
        self.registry = get_provider_registry()
        self.cache = get_cache_service()

    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        """
        Retrieves all live matches across active providers.
        Cached with short TTL (e.g. 60 seconds).
        """
        cache_key = f"events:live:{sport or 'all'}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [Event(**item) for item in cached]

        collected_events: List[Event] = []
        providers = self.registry.get_providers_for_sport(sport)

        for provider in providers:
            try:
                events = await provider.get_live_events(sport=sport)
                if events:
                    collected_events.extend(events)
            except Exception as exc:
                logger.error(f"[EventService] Error fetching live from {provider.name}: {exc}")

        # Deduplicate & reconcile
        reconciled = reconcile_events(collected_events)

        # Filter strictly for LIVE / HALFTIME / BREAK
        live_events = [
            e for e in reconciled
            if e.status in (EventStatus.LIVE, EventStatus.HALFTIME, EventStatus.BREAK)
        ]

        # Cache result
        await self.cache.set(
            cache_key,
            [e.model_dump() for e in live_events],
            ttl_seconds=settings.CACHE_TTL_LIVE,
        )

        return live_events

    async def get_today_events(self, sport: Optional[str] = None, tz_name: Optional[str] = None) -> List[Event]:
        """
        Retrieves all fixtures scheduled for today in the user's timezone.
        """
        start_utc, end_utc = get_day_range_utc(target_date=None, tz_name=tz_name)
        today_date = start_utc.date()

        cache_key = f"events:today:{today_date.isoformat()}:{sport or 'all'}:{tz_name or 'UTC'}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [Event(**item) for item in cached]

        collected_events: List[Event] = []
        providers = self.registry.get_providers_for_sport(sport)

        for provider in providers:
            try:
                events = await provider.get_events_by_date(today_date, sport=sport)
                if events:
                    collected_events.extend(events)
            except Exception as exc:
                logger.error(f"[EventService] Error fetching today events from {provider.name}: {exc}")

        reconciled = reconcile_events(collected_events)

        # Filter events falling within the requested calendar day window
        day_events: List[Event] = []
        for e in reconciled:
            dt = parse_iso_datetime(e.startTime)
            if dt and (start_utc <= dt <= end_utc):
                day_events.append(e)
            elif not dt:
                day_events.append(e)

        # Sort chronologically
        day_events.sort(key=lambda x: x.startTime)

        # Cache result
        await self.cache.set(
            cache_key,
            [e.model_dump() for e in day_events],
            ttl_seconds=settings.CACHE_TTL_TODAY,
        )

        return day_events

    async def get_upcoming_events(
        self,
        sport: Optional[str] = None,
        hours: int = 24,
        limit: int = 100,
    ) -> List[Event]:
        """
        Retrieves upcoming matches within the next N hours.
        """
        cache_key = f"events:upcoming:{sport or 'all'}:{hours}h"
        cached = await self.cache.get(cache_key)
        if cached:
            events = [Event(**item) for item in cached]
            return events[:limit]

        collected_events: List[Event] = []
        providers = self.registry.get_providers_for_sport(sport)

        for provider in providers:
            try:
                events = await provider.get_upcoming_events(sport=sport, hours=hours)
                if events:
                    collected_events.extend(events)
            except Exception as exc:
                logger.error(f"[EventService] Error fetching upcoming from {provider.name}: {exc}")

        reconciled = reconcile_events(collected_events)

        now = utc_now()
        cutoff = now + timedelta(hours=hours)

        upcoming: List[Event] = []
        for e in reconciled:
            dt = parse_iso_datetime(e.startTime)
            if dt and now <= dt <= cutoff:
                upcoming.append(e)
            elif not dt:
                upcoming.append(e)

        upcoming.sort(key=lambda x: x.startTime)

        await self.cache.set(
            cache_key,
            [e.model_dump() for e in upcoming],
            ttl_seconds=settings.CACHE_TTL_UPCOMING,
        )

        return upcoming[:limit]

    async def get_event_by_id(self, event_id: str) -> Optional[Event]:
        """
        Retrieves full event details for an event ID.
        """
        cache_key = f"event:detail:{event_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Event(**cached)

        # Query providers
        for provider in self.registry.all_providers:
            if provider.enabled:
                try:
                    event = await provider.get_event(event_id)
                    if event:
                        await self.cache.set(cache_key, event.model_dump(), ttl_seconds=settings.CACHE_TTL_TODAY)
                        return event
                except Exception as exc:
                    logger.error(f"[EventService] Error looking up event {event_id} on {provider.name}: {exc}")

        # Check in active upcoming & today lists
        all_active = await self.get_upcoming_events(hours=72, limit=200)
        for ev in all_active:
            if ev.id == event_id or event_id in ev.id or any(v == event_id for v in ev.externalIds.values()):
                await self.cache.set(cache_key, ev.model_dump(), ttl_seconds=settings.CACHE_TTL_TODAY)
                return ev

        return None

    async def get_home_screen(self) -> HomeScreenResponse:
        """
        Optimized feed for Apple TV sports home screen.
        Aggregates:
          - 🔴 LIVE (All sports currently in play)
          - ⏳ STARTING SOON (Next 60 minutes)
          - ⚽ Football / Soccer
          - 🏏 Cricket
          - 🏀 NBA / Basketball
          - 🎾 Tennis
        """
        cache_key = "home:screen:feed"
        cached = await self.cache.get(cache_key)
        if cached:
            return HomeScreenResponse(**cached)

        now = utc_now()
        soon_cutoff = now + timedelta(minutes=60)

        # 1. Fetch live events
        live_events = await self.get_live_events()

        # 2. Fetch today & upcoming fixtures across sports
        all_today = await self.get_today_events()
        all_upcoming = await self.get_upcoming_events(hours=48, limit=150)
        combined = reconcile_events(all_today + all_upcoming)

        # 3. Identify starting soon
        starting_soon: List[Event] = []
        for e in combined:
            if e.status in (EventStatus.SCHEDULED, EventStatus.STARTING_SOON):
                dt = parse_iso_datetime(e.startTime)
                if dt and now <= dt <= soon_cutoff:
                    e.status = EventStatus.STARTING_SOON
                    starting_soon.append(e)

        # 4. Group into sport-specific sections
        soccer_events = [e for e in combined if e.sport == "soccer"][:15]
        cricket_events = [e for e in combined if e.sport == "cricket"][:15]
        basketball_events = [e for e in combined if e.sport == "basketball"][:15]
        tennis_events = [e for e in combined if e.sport == "tennis"][:15]
        nfl_events = [e for e in combined if e.sport in ("nfl", "football_us")][:15]
        f1_events = [e for e in combined if e.sport in ("f1", "formula1")][:15]

        sections = [
            HomeSection(sport="soccer", title="Football / Soccer", events=soccer_events),
            HomeSection(sport="cricket", title="Cricket", events=cricket_events),
            HomeSection(sport="basketball", title="NBA / Basketball", events=basketball_events),
            HomeSection(sport="tennis", title="Tennis", events=tennis_events),
            HomeSection(sport="nfl", title="NFL / American Football", events=nfl_events),
            HomeSection(sport="f1", title="Formula 1", events=f1_events),
        ]

        response = HomeScreenResponse(
            generatedAt=format_iso_datetime(now) or "",
            live=live_events,
            startingSoon=starting_soon,
            sections=sections,
        )

        # Cache feed for 60 seconds
        await self.cache.set(cache_key, response.model_dump(), ttl_seconds=settings.CACHE_TTL_LIVE)

        return response


_event_service_instance: Optional[EventService] = None


def get_event_service() -> EventService:
    global _event_service_instance
    if _event_service_instance is None:
        _event_service_instance = EventService()
    return _event_service_instance
