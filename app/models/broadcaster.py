from typing import Optional, List
from pydantic import BaseModel, Field


class BroadcasterInfo(BaseModel):
    name: str = Field(..., description="Display name of the TV/broadcast channel")
    normalizedName: str = Field(..., description="Lowercased and cleaned channel name for matching")
    countryCode: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 country code e.g. GB, US, IN")
    country: Optional[str] = Field(None, description="Full country name e.g. United Kingdom")
    type: str = Field("tv", description="Type of broadcast: tv, streaming, ott, radio")
    language: Optional[str] = Field("English", description="Primary broadcast commentary language")
    logo: Optional[str] = Field(None, description="Broadcaster logo URL if available")
    source: str = Field("thesportsdb", description="Source provider or catalog of this broadcast entry")
    channels: Optional[List[str]] = Field(default_factory=list, description="Specific sub-channel feeds or alternate names")


class EventBroadcastersResponse(BaseModel):
    eventId: str
    eventName: Optional[str] = None
    sport: Optional[str] = None
    startTime: Optional[str] = None
    broadcasters: List[BroadcasterInfo] = Field(default_factory=list)
    totalCount: int = 0
