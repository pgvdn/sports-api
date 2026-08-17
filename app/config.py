from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sports IPTV API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./sports.db"

    # Provider Keys & Toggles
    THESPORTSDB_API_KEY: str = "3"
    THESPORTSDB_ENABLED: bool = True

    API_FOOTBALL_KEY: Optional[str] = None
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    API_FOOTBALL_ENABLED: bool = True

    API_BASKETBALL_KEY: Optional[str] = None
    API_BASKETBALL_BASE_URL: str = "https://v1.basketball.api-sports.io"
    API_BASKETBALL_ENABLED: bool = True

    CRICKET_API_KEY: Optional[str] = None
    CRICKET_ENABLED: bool = True

    TENNIS_API_KEY: Optional[str] = None
    TENNIS_ENABLED: bool = True

    # Caching TTLs (seconds)
    CACHE_ENABLED: bool = True
    CACHE_TTL_LIVE: int = 60
    CACHE_TTL_STARTING_SOON: int = 180
    CACHE_TTL_TODAY: int = 600
    CACHE_TTL_UPCOMING: int = 1800
    CACHE_TTL_BROADCASTERS: int = 14400
    CACHE_TTL_FINISHED: int = 86400

    # Channel Matcher
    CHANNEL_MATCH_THRESHOLD: float = 0.80

    # Background Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_REFRESH_INTERVAL_MINUTES: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
