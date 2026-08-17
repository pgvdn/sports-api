from abc import ABC, abstractmethod
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.models.event import Event
from app.models.broadcaster import BroadcasterInfo


class ProviderStatus(BaseModel):
    name: str
    enabled: bool
    status: str = "healthy"  # healthy, degraded, rate_limited, disabled, error
    supportsSports: List[str] = []
    supportsBroadcasters: bool = False
    requestsToday: int = 0
    remainingRequests: Optional[int] = None
    lastError: Optional[str] = None
    lastRequestAt: Optional[str] = None


class BaseProvider(ABC):
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.requests_today = 0
        self.last_error: Optional[str] = None
        self.last_request_at: Optional[datetime] = None
        self.is_rate_limited = False
        self.rate_limit_resets_at: Optional[datetime] = None

    def record_request(self) -> None:
        self.requests_today += 1
        self.last_request_at = datetime.now(timezone.utc)

    def record_error(self, error_msg: str) -> None:
        self.last_error = error_msg

    def record_rate_limit(self, resets_at: Optional[datetime] = None) -> None:
        self.is_rate_limited = True
        self.rate_limit_resets_at = resets_at

    def reset_daily_stats(self) -> None:
        self.requests_today = 0
        self.last_error = None
        self.is_rate_limited = False

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        pass


class SportsProvider(BaseProvider):
    @abstractmethod
    async def get_live_events(self, sport: Optional[str] = None) -> List[Event]:
        """Fetch all currently live sporting events."""
        pass

    @abstractmethod
    async def get_events_by_date(self, target_date: date, sport: Optional[str] = None) -> List[Event]:
        """Fetch all events scheduled for a specific calendar date (UTC)."""
        pass

    @abstractmethod
    async def get_upcoming_events(self, sport: Optional[str] = None, hours: int = 24) -> List[Event]:
        """Fetch upcoming events for the next N hours."""
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[Event]:
        """Lookup full event details by ID."""
        pass


class BroadcastProvider(BaseProvider):
    @abstractmethod
    async def get_broadcasters(self, event: Event) -> List[BroadcasterInfo]:
        """Retrieve TV/channel broadcast information for an event."""
        pass
