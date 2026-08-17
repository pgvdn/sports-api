from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/sports", tags=["Sports"])


class SportDetail(BaseModel):
    id: str
    name: str
    icon: str
    description: str
    popularLeagues: List[str]


@router.get("", response_model=List[SportDetail])
async def get_supported_sports():
    """
    Returns list of all supported sports categories and their key leagues.
    """
    return [
        SportDetail(
            id="soccer",
            name="Soccer / Football",
            icon="⚽",
            description="Global football coverage including Premier League, Champions League, La Liga, Serie A, and domestic cups.",
            popularLeagues=[
                "Premier League",
                "UEFA Champions League",
                "UEFA Europa League",
                "La Liga",
                "Serie A",
                "Bundesliga",
                "Ligue 1",
                "MLS",
                "Saudi Pro League",
                "Indian Super League",
            ],
        ),
        SportDetail(
            id="basketball",
            name="NBA / Basketball",
            icon="🏀",
            description="Basketball coverage prioritizing NBA regular season, playoffs, and finals.",
            popularLeagues=[
                "NBA",
                "EuroLeague",
                "NCAA Men's Basketball",
            ],
        ),
        SportDetail(
            id="cricket",
            name="Cricket",
            icon="🏏",
            description="Test, ODI, T20, ICC World Cups, and domestic franchise leagues.",
            popularLeagues=[
                "Indian Premier League (IPL)",
                "Big Bash League (BBL)",
                "Pakistan Super League (PSL)",
                "The Hundred",
                "ICC Men's Cricket World Cup",
                "ICC T20 World Cup",
            ],
        ),
        SportDetail(
            id="tennis",
            name="Tennis",
            icon="🎾",
            description="Grand Slams, ATP Tour, WTA Tour, ATP Masters 1000, and Davis Cup.",
            popularLeagues=[
                "Wimbledon",
                "US Open",
                "Australian Open",
                "French Open (Roland Garros)",
                "ATP Tour",
                "WTA Tour",
                "ATP Masters 1000",
            ],
        ),
        SportDetail(
            id="nfl",
            name="NFL / American Football",
            icon="🏈",
            description="NFL Regular Season, Playoffs, Super Bowl, and NCAA College Football.",
            popularLeagues=[
                "NFL",
                "NFL RedZone",
                "NCAA Football",
            ],
        ),
        SportDetail(
            id="f1",
            name="Formula 1 / Motorsport",
            icon="🏎️",
            description="Formula 1 Grand Prix races, Qualifying, Sprint races, and Practice sessions.",
            popularLeagues=[
                "Formula 1 World Championship",
            ],
        ),
    ]
