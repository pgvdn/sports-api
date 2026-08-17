from typing import List, Optional
from app.config import get_settings
from app.models.event import Event
from app.models.broadcaster import BroadcasterInfo, EventBroadcastersResponse
from app.providers.registry import get_provider_registry
from app.services.cache_service import get_cache_service
from app.providers.curated_broadcasters import get_curated_broadcasters_for_event
from app.utils.logging import logger

settings = get_settings()


class BroadcastService:
    def __init__(self):
        self.registry = get_provider_registry()
        self.cache = get_cache_service()

    async def get_broadcasters_for_event(self, event: Event) -> List[BroadcasterInfo]:
        """
        Retrieves, deduplicates, and caches TV broadcasters for an event.
        """
        cache_key = f"broadcasters:{event.id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return [BroadcasterInfo(**b) for b in cached]

        all_broadcasters: List[BroadcasterInfo] = []
        seen_keys: set = set()

        # 1. Query broadcast providers (TheSportsDB TV endpoint)
        for provider in self.registry.get_broadcast_providers():
            if provider.enabled and not provider.is_rate_limited:
                try:
                    results = await provider.get_broadcasters(event)
                    for b in results:
                        key = (b.normalizedName, b.countryCode or "")
                        if key not in seen_keys:
                            seen_keys.add(key)
                            all_broadcasters.append(b)
                except Exception as exc:
                    logger.error(f"[BroadcastService] Error fetching from {provider.name}: {exc}")

        # 2. Add curated catalog if provider results are empty
        if not all_broadcasters:
            curated = get_curated_broadcasters_for_event(
                sport=event.sport,
                league_name=event.league.name,
                home_name=event.home.name,
                away_name=event.away.name,
            )
            for c in curated:
                key = (c.normalizedName, c.countryCode or "")
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_broadcasters.append(c)

        # Cache broadcasters for 4 hours
        if all_broadcasters:
            await self.cache.set(
                cache_key,
                [b.model_dump() for b in all_broadcasters],
                ttl_seconds=settings.CACHE_TTL_BROADCASTERS,
            )

        return all_broadcasters


_broadcast_service_instance: Optional[BroadcastService] = None


def get_broadcast_service() -> BroadcastService:
    global _broadcast_service_instance
    if _broadcast_service_instance is None:
        _broadcast_service_instance = BroadcastService()
    return _broadcast_service_instance
