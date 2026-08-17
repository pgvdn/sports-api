# Sports IPTV Backend API

A high-performance Python FastAPI backend for personal IPTV and Apple TV sports applications. It provides live, today, and upcoming sports events with legitimate TV/broadcast channel metadata for matching against a user's own Xtream Codes or M3U playlist.

> **Important**: This application never proxies, stores, scrapes, or streams copyrighted media. It only returns public match schedules, scores, and official TV broadcaster network names.

---

## 🌟 Key Features

* **Multi-Sport Coverage**:
  * ⚽ **Soccer / Football**: Premier League, UEFA Champions League, Europa League, La Liga, Serie A, Bundesliga, Ligue 1, MLS, Saudi Pro League, Indian Super League, World Cup, Euro, Copa America.
  * 🏀 **NBA / Basketball**: Full NBA regular season & playoff coverage, EuroLeague.
  * 🏏 **Cricket**: Test matches, ODIs, T20s, ICC World Cups, IPL, BBL, PSL, The Hundred, CPL.
  * 🎾 **Tennis**: Player 1 vs Player 2 support, Grand Slams (Wimbledon, US Open, French Open, Australian Open), ATP Tour, WTA Tour, ATP Masters 1000.
* **Apple TV Optimized Home Feed**: Single `/api/v1/home` endpoint returning live games, games starting in the next 60 minutes, and dedicated horizontal sport rails.
* **Official Broadcaster Information**: Returns verified TV network channels carrying each game (e.g., Sky Sports Main Event, TNT Sports, USA Network, Star Sports, Willow Cricket, Sony Sports, SuperSport, etc.).
* **Channel Matching & Normalization Engine**:
  * Cleans IPTV channel names (`UK | SKY SPORTS MAIN EVENT FHD` ➔ `sky sports main event`).
  * Calculates similarity scores (0.0 to 1.0) and matches against official TV broadcasters.
* **Free Tier Prioritization & Pluggable Provider Architecture**:
  * Default free integration with **TheSportsDB** (Free key `3`).
  * Optional free tier integration with **API-Sports / API-Football** and **API-Basketball**.
  * Curated fallback database for verified global broadcasting rights.
  * Extensible architecture for future providers (Sportradar, Sportmonks, Ronin, etc.).
* **Two-Tier Caching System**: In-memory + persistent SQLite database cache with TTLs (Live: 60s, Today: 10m, Broadcasters: 4h).
* **Cross-Provider Event Reconciliation**: Deduplicates same events from different providers by team name similarity and start time proximity.

---

## 🏗️ Architecture

```text
sports-api/
├── app/
│   ├── main.py                  # FastAPI app entry point, CORS, lifespan & middleware
│   ├── config.py                # Pydantic Settings & environment loader
│   ├── database.py              # Async SQLAlchemy engine & SQLite/PostgreSQL setup
│   ├── api/
│   │   ├── sports.py            # /api/v1/sports
│   │   ├── events.py            # /api/v1/events (live, today, upcoming, id, channels, match)
│   │   ├── home.py              # /api/v1/home (Apple TV feed)
│   │   └── providers.py         # /api/v1/providers/status
│   ├── models/
│   │   ├── event.py             # Normalized Event, Score, and Feed models
│   │   ├── broadcaster.py       # BroadcasterInfo models
│   │   ├── league.py            # League, Participant, TennisPlayers models
│   │   ├── channel.py           # IPTV ChannelInput and ChannelMatch models
│   │   └── db_models.py         # SQLAlchemy DB models (events, cache, metrics)
│   ├── providers/
│   │   ├── base.py              # SportsProvider & BroadcastProvider abstract interfaces
│   │   ├── thesportsdb.py       # TheSportsDB free API integration
│   │   ├── api_football.py      # API-Football / API-Sports free tier
│   │   ├── api_basketball.py    # API-Basketball / NBA free tier
│   │   ├── cricket.py           # Cricket schedule provider
│   │   ├── tennis.py            # Tennis tournament provider
│   │   ├── curated_broadcasters.py # Verified global TV rights database
│   │   └── registry.py          # Provider registry, fallback chains & health metrics
│   ├── services/
│   │   ├── event_service.py     # Event aggregation, filtering, and caching
│   │   ├── broadcast_service.py # TV broadcast resolution & deduplication
│   │   ├── reconciliation.py    # Multi-provider event deduplication
│   │   ├── channel_matcher.py   # Fuzzy playlist channel matching
│   │   ├── cache_service.py     # Two-tier cache with TTL
│   │   └── scheduler_service.py # APScheduler background maintenance
│   └── utils/
│       ├── time.py              # UTC / Timezone helpers
│       ├── normalization.py     # Channel name cleaner & similarity algorithms
│       └── logging.py           # Structured logger
├── tests/                       # Complete Pytest test suite
├── .env.example
├── requirements.txt
├── pytest.ini
└── run.py
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* Python 3.12+ (or `uv`)

### 2. Setup Virtual Environment
```bash
# Using standard venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Or using uv (faster)
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` as needed:
```ini
THESPORTSDB_API_KEY="3"        # Default free public key
API_FOOTBALL_KEY=""           # Optional free tier key from api-football.com
API_BASKETBALL_KEY=""         # Optional free tier key from api-sports.io
DATABASE_URL="sqlite+aiosqlite:///./sports.db"
CACHE_ENABLED=true
CHANNEL_MATCH_THRESHOLD=0.80
```

### 4. Run the API Server
```bash
python run.py
```
Or directly with uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔑 How to Obtain Free API Keys

1. **TheSportsDB (Free)**:
   * Public test key is `3` (pre-configured).
   * For personal production access, create a free account at [TheSportsDB.com](https://www.thesportsdb.com/).
2. **API-Football / API-Sports (Free Tier - 100 requests/day)**:
   * Sign up at [dashboard.api-football.com](https://dashboard.api-football.com/).
   * Copy your API key and set `API_FOOTBALL_KEY` in `.env`.
3. **API-Basketball (Free Tier - 100 requests/day)**:
   * Available within the same API-Sports account.
   * Set `API_BASKETBALL_KEY` in `.env`.

> *Note: If any API key is left blank, the application automatically disables that provider and falls back to TheSportsDB and curated catalogs.*

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check and database status |
| `GET` | `/api/v1/sports` | List of supported sports |
| `GET` | `/api/v1/home` | Apple TV optimized sports home feed |
| `GET` | `/api/v1/events/live` | Currently live events (`?sport=soccer`) |
| `GET` | `/api/v1/events/today` | Today's events (`?sport=cricket&timezone=America/New_York`) |
| `GET` | `/api/v1/events/upcoming` | Upcoming fixtures (`?sport=basketball&hours=24`) |
| `GET` | `/api/v1/events/{id}` | Full event details with scores & venue |
| `GET` | `/api/v1/events/{id}/channels` | TV broadcasters for the event |
| `POST` | `/api/v1/events/{id}/match-channels` | Match user's playlist against broadcasters |
| `GET` | `/api/v1/providers/status` | Provider request metrics and health |

---

## 📺 Channel Matching Example

### 1. Request Broadcasters for a Match
```http
GET /api/v1/events/soccer_premier_leag_123456/channels
```

**Response**:
```json
{
  "eventId": "soccer_premier_leag_123456",
  "eventName": "Arsenal vs Liverpool",
  "sport": "soccer",
  "startTime": "2026-08-17T19:00:00Z",
  "broadcasters": [
    {
      "name": "Sky Sports Main Event",
      "normalizedName": "sky sports main event",
      "countryCode": "GB",
      "country": "United Kingdom",
      "type": "tv",
      "source": "thesportsdb"
    },
    {
      "name": "USA Network",
      "normalizedName": "usa network",
      "countryCode": "US",
      "country": "United States",
      "type": "tv",
      "source": "thesportsdb"
    }
  ],
  "totalCount": 2
}
```

### 2. Match Against User's IPTV Playlist
```http
POST /api/v1/events/soccer_premier_leag_123456/match-channels
Content-Type: application/json

{
  "channels": [
    { "id": "101", "name": "UK | SKY SPORTS MAIN EVENT FHD" },
    { "id": "102", "name": "USA NETWORK HD" },
    { "id": "103", "name": "UK | BBC ONE HD" }
  ],
  "threshold": 0.80
}
```

**Response**:
```json
{
  "eventId": "soccer_premier_leag_123456",
  "eventName": "Arsenal vs Liverpool",
  "threshold": 0.8,
  "totalBroadcasters": 2,
  "matches": [
    {
      "broadcaster": "USA Network",
      "country": "United States",
      "channel": { "id": "102", "name": "USA NETWORK HD" },
      "score": 1.0,
      "matchedName": "usa network"
    },
    {
      "broadcaster": "Sky Sports Main Event",
      "country": "United Kingdom",
      "channel": { "id": "101", "name": "UK | SKY SPORTS MAIN EVENT FHD" },
      "score": 0.96,
      "matchedName": "sky sports main event"
    }
  ]
}
```

---

## 🧪 Running Tests

```bash
./.venv/bin/pytest
```

---

## 🔌 Adding Another Sports Provider

To add a new provider (e.g., `SportmonksProvider`):

1. Inherit from `SportsProvider` in `app/providers/`:
```python
from app.providers.base import SportsProvider, ProviderStatus

class SportmonksProvider(SportsProvider):
    def __init__(self, api_key: str):
        super().__init__(name="Sportmonks", enabled=bool(api_key))
        ...
```
2. Implement `get_live_events`, `get_events_by_date`, `get_upcoming_events`, and `get_event`.
3. Register the new provider in `app/providers/registry.py`.

---

## 📄 License

MIT License. Designed for personal and home streaming setups.
