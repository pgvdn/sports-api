import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Force test database URL
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["CACHE_ENABLED"] = "true"
os.environ["SCHEDULER_ENABLED"] = "false"

from app.main import app
from app.database import init_db
from app.models.event import Event, EventStatus, EventScore
from app.models.league import LeagueInfo, ParticipantInfo
from app.models.broadcaster import BroadcasterInfo


@pytest_asyncio.fixture(scope="function")
async def client():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_soccer_event():
    return Event(
        id="soccer_epl_123456",
        externalIds={"thesportsdb": "123456"},
        sport="soccer",
        league=LeagueInfo(id="4328", name="Premier League", country="England"),
        home=ParticipantInfo(id="1", name="Arsenal"),
        away=ParticipantInfo(id="2", name="Liverpool"),
        startTime="2026-08-17T19:00:00Z",
        status=EventStatus.LIVE,
        score=EventScore(home=1, away=0, displayScore="1 - 0"),
        broadcasters=[
            BroadcasterInfo(
                name="Sky Sports Main Event",
                normalizedName="sky sports main event",
                countryCode="GB",
                country="United Kingdom",
                type="tv",
            ),
            BroadcasterInfo(
                name="USA Network",
                normalizedName="usa network",
                countryCode="US",
                country="United States",
                type="tv",
            ),
        ],
    )
