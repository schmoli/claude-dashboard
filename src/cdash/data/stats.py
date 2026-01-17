"""Stats data loading from stats-cache.json."""

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


@dataclass
class DailyStats:
    """Stats for a single day."""

    date: date
    message_count: int
    session_count: int
    tool_call_count: int


@dataclass
class StatsCache:
    """Parsed stats cache data."""

    daily_activity: list[DailyStats]
    total_sessions: int
    total_messages: int

    def get_today(self) -> DailyStats | None:
        """Get today's stats."""
        today = date.today()
        for day in self.daily_activity:
            if day.date == today:
                return day
        return None

    def get_last_n_days(self, n: int) -> list[DailyStats]:
        """Get stats for last n days (including today), filling missing days with zeros."""
        today = date.today()
        result = []

        # Create a lookup by date
        by_date = {d.date: d for d in self.daily_activity}

        for i in range(n - 1, -1, -1):
            day = today - timedelta(days=i)
            if day in by_date:
                result.append(by_date[day])
            else:
                result.append(DailyStats(date=day, message_count=0, session_count=0, tool_call_count=0))

        return result


def get_stats_cache_path() -> Path:
    """Get path to stats-cache.json."""
    return Path.home() / ".claude" / "stats-cache.json"


def load_stats_cache() -> StatsCache | None:
    """Load and parse stats-cache.json.

    Returns:
        StatsCache object or None if file doesn't exist or is invalid
    """
    cache_path = get_stats_cache_path()
    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        daily_activity = []
        for entry in data.get("dailyActivity", []):
            try:
                d = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                daily_activity.append(
                    DailyStats(
                        date=d,
                        message_count=entry.get("messageCount", 0),
                        session_count=entry.get("sessionCount", 0),
                        tool_call_count=entry.get("toolCallCount", 0),
                    )
                )
            except (KeyError, ValueError):
                continue

        return StatsCache(
            daily_activity=daily_activity,
            total_sessions=data.get("totalSessions", 0),
            total_messages=data.get("totalMessages", 0),
        )
    except (json.JSONDecodeError, OSError, PermissionError):
        return None


def sparkline(values: list[int], width: int = 7) -> str:
    """Generate a sparkline string from values.

    Args:
        values: List of integer values
        width: Number of characters in sparkline

    Returns:
        String of sparkline characters
    """
    if not values:
        return " " * width

    # Unicode block characters for sparkline (empty to full)
    blocks = " ▁▂▃▄▅▆▇█"

    max_val = max(values) if values else 1
    if max_val == 0:
        return "▁" * len(values)

    result = []
    for val in values:
        # Scale to 0-8 range
        idx = int((val / max_val) * (len(blocks) - 1))
        result.append(blocks[idx])

    return "".join(result)
