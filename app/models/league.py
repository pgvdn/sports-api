from typing import Optional
from pydantic import BaseModel, Field


class LeagueInfo(BaseModel):
    id: str = Field(..., description="Unique league slug or identifier")
    name: str = Field(..., description="League or tournament name")
    country: Optional[str] = Field(None, description="Country of the league or 'International'")
    logo: Optional[str] = Field(None, description="URL to league logo image")
    season: Optional[str] = Field(None, description="Season identifier e.g. 2026-2027")
    round: Optional[str] = Field(None, description="Match round or stage e.g. 'Matchday 5' or 'Semi-Final'")


class ParticipantInfo(BaseModel):
    id: Optional[str] = Field(None, description="Team or player identifier")
    name: str = Field(..., description="Team or player name")
    shortName: Optional[str] = Field(None, description="Abbreviated name or code e.g. ARS")
    logo: Optional[str] = Field(None, description="Logo or avatar URL")
    country: Optional[str] = Field(None, description="Country or nationality")


class TennisMatchPlayers(BaseModel):
    player1: ParticipantInfo
    player2: ParticipantInfo
    player1Seed: Optional[int] = None
    player2Seed: Optional[int] = None


class VenueInfo(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: Optional[int] = None
