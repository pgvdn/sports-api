from typing import Optional, List
from pydantic import BaseModel, Field


class ChannelInput(BaseModel):
    id: str = Field(..., description="ID from user's IPTV playlist / stream entry")
    name: str = Field(..., description="Channel name from user's IPTV playlist")
    group: Optional[str] = Field(None, description="Category / group title e.g. UK Sports, USA Live")
    tvgId: Optional[str] = Field(None, description="EPG channel ID if present in M3U")
    logo: Optional[str] = Field(None, description="Channel logo URL")


class ChannelMatch(BaseModel):
    broadcaster: str = Field(..., description="Canonical broadcaster name from sports database")
    country: Optional[str] = Field(None, description="Broadcaster country")
    channel: ChannelInput = Field(..., description="Matched playlist channel item")
    score: float = Field(..., description="Matching confidence score between 0.0 and 1.0")
    matchedName: str = Field(..., description="Normalized string used in match")


class ChannelMatchRequest(BaseModel):
    channels: List[ChannelInput] = Field(..., description="List of playlist channels to test against event broadcasters")
    threshold: Optional[float] = Field(0.80, description="Minimum confidence threshold (0.0 to 1.0)")


class ChannelMatchResponse(BaseModel):
    eventId: str
    eventName: Optional[str] = None
    threshold: float
    totalBroadcasters: int
    matches: List[ChannelMatch] = Field(default_factory=list)
