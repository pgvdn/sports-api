from typing import List, Dict, Optional

from app.config import Settings, get_settings
from app.providers.base import SportsProvider, BroadcastProvider, ProviderStatus
from app.providers.espn import EspnPublicProvider
from app.providers.thesportsdb import TheSportsDBProvider
from app.providers.api_football import ApiFootballProvider
from app.providers.api_basketball import ApiBasketballProvider
from app.providers.cricket import CricketProvider
from app.providers.tennis import TennisProvider


class ProviderRegistry:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

        # Zero-key high-reliability public provider (Domestic cups, Live scores, Leagues)
        self.espn = EspnPublicProvider(enabled=True)

        # Free tier provider
        self.thesportsdb = TheSportsDBProvider(
            api_key=self.settings.THESPORTSDB_API_KEY,
            enabled=self.settings.THESPORTSDB_ENABLED,
        )

        # Optional API-Sports / RapidAPI providers
        self.api_football = ApiFootballProvider(
            api_key=self.settings.API_FOOTBALL_KEY,
            base_url=self.settings.API_FOOTBALL_BASE_URL,
            enabled=self.settings.API_FOOTBALL_ENABLED,
        )

        self.api_basketball = ApiBasketballProvider(
            api_key=self.settings.API_BASKETBALL_KEY,
            base_url=self.settings.API_BASKETBALL_BASE_URL,
            enabled=self.settings.API_BASKETBALL_ENABLED,
        )

        self.cricket = CricketProvider(
            api_key=self.settings.CRICKET_API_KEY,
            enabled=self.settings.CRICKET_ENABLED,
        )

        self.tennis = TennisProvider(
            api_key=self.settings.TENNIS_API_KEY,
            enabled=self.settings.TENNIS_ENABLED,
        )

        self.all_providers: List[SportsProvider] = [
            self.espn,
            self.thesportsdb,
            self.api_football,
            self.api_basketball,
            self.cricket,
            self.tennis,
        ]

    def get_providers_for_sport(self, sport: Optional[str] = None) -> List[SportsProvider]:
        """
        Returns active provider chain for a given sport in fallback priority order.
        """
        if not sport:
            return [p for p in self.all_providers if p.enabled]

        s = sport.lower()
        chain: List[SportsProvider] = []

        if s in ("soccer", "football"):
            if self.api_football.enabled and not self.api_football.is_rate_limited:
                chain.append(self.api_football)
            if self.espn.enabled:
                chain.append(self.espn)
            if self.thesportsdb.enabled:
                chain.append(self.thesportsdb)

        elif s in ("basketball", "nba"):
            if self.api_basketball.enabled and not self.api_basketball.is_rate_limited:
                chain.append(self.api_basketball)
            if self.espn.enabled:
                chain.append(self.espn)
            if self.thesportsdb.enabled:
                chain.append(self.thesportsdb)

        elif s == "cricket":
            if self.cricket.enabled:
                chain.append(self.cricket)
            if self.thesportsdb.enabled:
                chain.append(self.thesportsdb)

        elif s == "tennis":
            if self.tennis.enabled:
                chain.append(self.tennis)
            if self.espn.enabled:
                chain.append(self.espn)
            if self.thesportsdb.enabled:
                chain.append(self.thesportsdb)

        else:
            if self.espn.enabled:
                chain.append(self.espn)
            if self.thesportsdb.enabled:
                chain.append(self.thesportsdb)

        if not chain and self.thesportsdb.enabled:
            chain.append(self.thesportsdb)

        return chain

    def get_broadcast_providers(self) -> List[BroadcastProvider]:
        """Returns providers capable of looking up TV broadcasts."""
        return [self.thesportsdb]

    def get_all_statuses(self) -> List[ProviderStatus]:
        """Returns health and status summary for all providers."""
        return [p.get_status() for p in self.all_providers]

    async def close_all(self) -> None:
        """Gracefully close HTTP sessions."""
        for p in self.all_providers:
            if hasattr(p, "close"):
                await p.close()


_registry_instance: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ProviderRegistry()
    return _registry_instance
