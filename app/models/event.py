from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.models.league import LeagueInfo, ParticipantInfo, TennisMatchPlayers, VenueInfo
from app.models.broadcaster import BroadcasterInfo


class SportType(str, Enum):
    SOCCER = "soccer"
    BASKETBALL = "basketball"
    CRICKET = "cricket"
    TENNIS = "tennis"
    NFL = "nfl"
    F1 = "f1"


class EventStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    STARTING_SOON = "STARTING_SOON"
    LIVE = "LIVE"
    HALFTIME = "HALFTIME"
    BREAK = "BREAK"
    FINISHED = "FINISHED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"


class EventScore(BaseModel):
    home: Optional[Any] = Field(None, description="Home score/runs/goals/games")
    away: Optional[Any] = Field(None, description="Away score/runs/goals/games")
    homeDetails: Optional[str] = Field(None, description="Detailed score e.g. '280/6 (50 ov)' or '6-4, 3-6, 7-6'")
    awayDetails: Optional[str] = Field(None, description="Detailed score e.g. '245/10 (47.2 ov)'")
    currentPeriod: Optional[str] = Field(None, description="e.g. '2nd Half 74'' or 'Q3 04:12' or 'Set 3'")
    displayScore: Optional[str] = Field(None, description="Preformatted human-friendly score string")


class Event(BaseModel):
    id: str = Field(..., description="Normalized unique internal event identifier e.g. soccer_epl_123456")
    externalIds: Dict[str, str] = Field(default_factory=dict, description="Source provider IDs e.g. {'thesportsdb': '123'}")
    sport: str = Field(..., description="Sport category: soccer, basketball, cricket, tennis")
    league: LeagueInfo = Field(..., description="League, competition, or tournament information")
    home: ParticipantInfo = Field(..., description="Home team or Player 1")
    away: ParticipantInfo = Field(..., description="Away team or Player 2")
    tennisPlayers: Optional[TennisMatchPlayers] = Field(None, description="Player 1 vs Player 2 details for Tennis")
    cricketFormat: Optional[str] = Field(None, description="Cricket format: Test, ODI, T20, The Hundred")
    startTime: str = Field(..., description="Match start time in UTC (ISO 8601 format with Z)")
    status: EventStatus = Field(..., description="Normalized event status")
    score: Optional[EventScore] = Field(None, description="Current match score or result")
    venue: Optional[VenueInfo] = Field(None, description="Stadium / arena / court details")
    broadcasters: Optional[List[BroadcasterInfo]] = Field(default_factory=list, description="Broadcaster TV channels")
    debug: Optional[Dict[str, Any]] = Field(None, description="Debug metadata returned when ?debug=true")


class EventsListResponse(BaseModel):
    total: int
    sport: Optional[str] = None
    status: Optional[str] = None
    date: Optional[str] = None
    events: List[Event] = Field(default_factory=list)
    debug: Optional[Dict[str, Any]] = None


class HomeSection(BaseModel):
    sport: str
    title: str
    events: List[Event] = Field(default_factory=list)


class HomeScreenResponse(BaseModel):
    generatedAt: str = Field(..., description="ISO 8601 generation timestamp")
    live: List[Event] = Field(default_factory=list, description="All currently live games across sports")
    startingSoon: List[Event] = Field(default_factory=list, description="Games starting in next 60 minutes")
    sections: List[HomeSection] = Field(default_factory=list, description="Sport-specific sections for Apple TV")
    debug: Optional[Dict[str, Any]] = None
