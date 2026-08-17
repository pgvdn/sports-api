from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    Float,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DBEvent(Base):
    __tablename__ = "events"

    id = Column(String(128), primary_key=True, index=True)
    sport = Column(String(32), nullable=False, index=True)
    league_id = Column(String(64), index=True)
    league_name = Column(String(128))
    home_id = Column(String(64))
    home_name = Column(String(128), nullable=False)
    away_id = Column(String(64))
    away_name = Column(String(128), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    score_json = Column(Text, nullable=True)
    raw_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    broadcasters = relationship("DBEventBroadcaster", back_populates="event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_events_sport_status_time", "sport", "status", "start_time"),
    )


class DBBroadcaster(Base):
    __tablename__ = "broadcasters"

    id = Column(String(128), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    normalized_name = Column(String(128), nullable=False, index=True)
    country_code = Column(String(8), index=True)
    country = Column(String(64))
    type = Column(String(32), default="tv")
    language = Column(String(32), default="English")
    logo = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class DBEventBroadcaster(Base):
    __tablename__ = "event_broadcasters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(128), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    broadcaster_id = Column(String(128), ForeignKey("broadcasters.id"), nullable=True)
    broadcaster_name = Column(String(128), nullable=False)
    country_code = Column(String(8), nullable=True)
    source = Column(String(64), default="thesportsdb")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    event = relationship("DBEvent", back_populates="broadcasters")


class DBCacheEntry(Base):
    __tablename__ = "cache_entries"

    key = Column(String(256), primary_key=True, index=True)
    value_json = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class DBProviderUsage(Base):
    __tablename__ = "provider_usage"

    provider_name = Column(String(64), primary_key=True)
    requests_today = Column(Integer, default=0)
    total_requests = Column(Integer, default=0)
    last_request_at = Column(DateTime(timezone=True), nullable=True)
    is_rate_limited = Column(Boolean, default=False)
    rate_limit_resets_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
