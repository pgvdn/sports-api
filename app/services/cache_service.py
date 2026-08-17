import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict
from sqlalchemy import select, delete

from app.config import get_settings
from app.database import async_session_factory
from app.models.db_models import DBCacheEntry
from app.utils.logging import logger

settings = get_settings()


class CacheService:
    def __init__(self):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _is_expired(self, expires_at: datetime) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expires_at

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if cache is enabled and entry is not expired."""
        if not settings.CACHE_ENABLED:
            return None

        # 1. Fast in-memory check
        mem_item = self._memory_cache.get(key)
        if mem_item:
            if not self._is_expired(mem_item["expires_at"]):
                return mem_item["data"]
            else:
                del self._memory_cache[key]

        # 2. Database cache check
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(DBCacheEntry).where(DBCacheEntry.key == key)
                )
                entry = result.scalar_one_or_none()
                if entry:
                    if not self._is_expired(entry.expires_at):
                        data = json.loads(entry.value_json)
                        # Warm memory cache
                        self._memory_cache[key] = {
                            "data": data,
                            "expires_at": entry.expires_at,
                        }
                        return data
                    else:
                        # Clean up expired entry
                        await session.delete(entry)
                        await session.commit()
        except Exception as exc:
            logger.debug(f"[Cache] DB get error for {key}: {exc}")

        return None

    async def set(self, key: str, data: Any, ttl_seconds: int) -> None:
        """Save value into memory and persistent database cache."""
        if not settings.CACHE_ENABLED or ttl_seconds <= 0:
            return

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

        # 1. Save to memory cache
        self._memory_cache[key] = {
            "data": data,
            "expires_at": expires_at,
        }

        # 2. Save to database cache
        try:
            json_str = json.dumps(data)
            async with async_session_factory() as session:
                # Upsert into SQLite
                existing = await session.get(DBCacheEntry, key)
                if existing:
                    existing.value_json = json_str
                    existing.expires_at = expires_at
                else:
                    new_entry = DBCacheEntry(
                        key=key,
                        value_json=json_str,
                        expires_at=expires_at,
                    )
                    session.add(new_entry)
                await session.commit()
        except Exception as exc:
            logger.debug(f"[Cache] DB set error for {key}: {exc}")

    async def delete(self, key: str) -> None:
        """Remove entry from both cache layers."""
        self._memory_cache.pop(key, None)
        try:
            async with async_session_factory() as session:
                await session.execute(delete(DBCacheEntry).where(DBCacheEntry.key == key))
                await session.commit()
        except Exception as exc:
            logger.debug(f"[Cache] DB delete error for {key}: {exc}")

    async def clear_expired(self) -> int:
        """Clean up expired entries from the database."""
        now = datetime.now(timezone.utc)
        count = 0
        try:
            async with async_session_factory() as session:
                stmt = delete(DBCacheEntry).where(DBCacheEntry.expires_at <= now)
                result = await session.execute(stmt)
                await session.commit()
                count = result.rowcount
        except Exception as exc:
            logger.error(f"[Cache] Error clearing expired entries: {exc}")
        return count


_cache_instance: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
