from datetime import datetime, date, timezone, timedelta
from typing import Optional, Tuple
import pytz


def utc_now() -> datetime:
    """Return current datetime in timezone-aware UTC."""
    return datetime.now(timezone.utc)


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 or common datetime string into timezone-aware UTC."""
    if not dt_str:
        return None
    try:
        # Replace Z with +00:00 for fromisoformat compatibility
        clean_str = dt_str.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        # Fallback formats
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M",
        ):
            try:
                dt = datetime.strptime(dt_str.strip(), fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    return None


def format_iso_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO 8601 UTC with Z suffix."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_day_range_utc(target_date: Optional[date] = None, tz_name: Optional[str] = None) -> Tuple[datetime, datetime]:
    """
    Get UTC start and end bounds for a given calendar date in the specified timezone.
    Defaults to today in UTC.
    """
    if tz_name:
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC
    else:
        tz = pytz.UTC

    now_tz = datetime.now(tz)
    if target_date is None:
        target_date = now_tz.date()

    start_local = tz.localize(datetime.combine(target_date, datetime.min.time()))
    end_local = tz.localize(datetime.combine(target_date, datetime.max.time()))

    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def is_time_proximate(dt1: Optional[datetime], dt2: Optional[datetime], max_delta_minutes: int = 120) -> bool:
    """Check if two datetimes are within max_delta_minutes of each other."""
    if not dt1 or not dt2:
        return False
    diff = abs((dt1 - dt2).total_seconds()) / 60.0
    return diff <= max_delta_minutes
