from typing import Optional, List
from pydantic import BaseModel, Field

_ONLINE_TYPES = {"ott", "streaming", "online"}
_ONLINE_NAME_PATTERNS = {
    "espn+",
    "peacock",
    "paramount+",
    "apple tv",
    "prime video",
    "amazon prime",
    "jiocinema",
    "sony liv",
    "fancode",
    "fanatiz",
    "triller tv",
    "shahid",
    "star+",
    "onefootball",
    "mls season pass",
    "dazn app",
}


class BroadcasterInfo(BaseModel):
    name: str = Field(..., description="Display name of the TV/broadcast channel")
    normalizedName: str = Field(..., description="Lowercased and cleaned channel name for matching")
    countryCode: Optional[str] = Field(None, description="ISO 3166-1 alpha-2 country code e.g. GB, US, IN")
    country: Optional[str] = Field(None, description="Full country name e.g. United Kingdom")
    channelType: str = Field("tv", description="Channel category: 'online' for OTT/streaming services, 'tv' for traditional broadcast channels")
    language: Optional[str] = Field("English", description="Primary broadcast commentary language")
    logo: Optional[str] = Field(None, description="Broadcaster logo URL if available")
    source: str = Field("thesportsdb", description="Source provider or catalog of this broadcast entry")
    channels: Optional[List[str]] = Field(default_factory=list, description="Specific sub-channel feeds or alternate names")

    def __init__(self, **data):
        # Accept legacy 'type' field and derive channelType from it or known streaming platforms
        broadcaster_type = (data.pop("type", None) or "").lower()
        if "channelType" not in data:
            if broadcaster_type in _ONLINE_TYPES:
                data["channelType"] = "online"
            else:
                norm_name = str(data.get("normalizedName") or data.get("name") or "").lower()
                if any(p in norm_name for p in _ONLINE_NAME_PATTERNS):
                    data["channelType"] = "online"
        super().__init__(**data)


class EventBroadcastersResponse(BaseModel):
    eventId: str
    eventName: Optional[str] = None
    sport: Optional[str] = None
    startTime: Optional[str] = None
    broadcasters: List[BroadcasterInfo] = Field(default_factory=list)
    totalCount: int = 0
