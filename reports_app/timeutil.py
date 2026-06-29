from datetime import datetime, timezone
from datetime import time as dt_time
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import DEFAULT_TIMEZONE


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


def parse_iso(value: str):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def get_zone(name: str):
    try:
        return ZoneInfo(name or DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        raise ValueError(f"invalid timezone: {name}")


def current_week_key(tz_name: str = DEFAULT_TIMEZONE, now=None) -> str:
    zone = get_zone(tz_name)
    local = (now or utc_now()).astimezone(zone)
    year, week, _weekday = local.isocalendar()
    return f"{year}-W{week:02d}"


def week_key_for(dt: datetime, tz_name: str = DEFAULT_TIMEZONE) -> str:
    zone = get_zone(tz_name)
    local = dt.astimezone(zone)
    year, week, _weekday = local.isocalendar()
    return f"{year}-W{week:02d}"


def week_bounds(tz_name: str = DEFAULT_TIMEZONE, now=None):
    zone = get_zone(tz_name)
    local = (now or utc_now()).astimezone(zone)
    start_date = local.date() - timedelta(days=local.isoweekday() - 1)
    start_local = datetime.combine(start_date, dt_time.min, tzinfo=zone)
    end_local = start_local + timedelta(days=7)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)
