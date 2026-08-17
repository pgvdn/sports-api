from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import Optional

from app.config import get_settings
from app.services.cache_service import get_cache_service
from app.providers.registry import get_provider_registry
from app.utils.logging import logger

settings = get_settings()


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.cache = get_cache_service()
        self.registry = get_provider_registry()

    def start(self) -> None:
        if not settings.SCHEDULER_ENABLED:
            logger.info("[Scheduler] Background scheduler is disabled in settings.")
            return

        # 1. Periodic expired cache cleanup every 15 minutes
        self.scheduler.add_job(
            self.clean_expired_cache,
            trigger=IntervalTrigger(minutes=15),
            id="cleanup_cache",
            replace_existing=True,
        )

        # 2. Reset daily provider stats at 00:00 UTC
        self.scheduler.add_job(
            self.reset_daily_provider_stats,
            trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
            id="reset_stats",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("[Scheduler] Background tasks scheduler started successfully.")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("[Scheduler] Background scheduler stopped.")

    async def clean_expired_cache(self) -> None:
        try:
            count = await self.cache.clear_expired()
            if count > 0:
                logger.info(f"[Scheduler] Purged {count} expired cache entries.")
        except Exception as exc:
            logger.error(f"[Scheduler] Error during cache cleanup: {exc}")

    def reset_daily_provider_stats(self) -> None:
        try:
            for p in self.registry.all_providers:
                p.reset_daily_stats()
            logger.info("[Scheduler] Provider daily stats reset to 0.")
        except Exception as exc:
            logger.error(f"[Scheduler] Error resetting provider stats: {exc}")


_scheduler_instance: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SchedulerService()
    return _scheduler_instance
