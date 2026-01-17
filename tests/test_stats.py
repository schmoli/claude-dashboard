"""Tests for stats data loading and display."""

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cdash.data.stats import DailyStats, StatsCache, load_stats_cache, sparkline


class TestSparkline:
    """Tests for sparkline generation."""

    def test_empty_values(self):
        """Empty list returns spaces."""
        result = sparkline([])
        assert result == "       "

    def test_single_value(self):
        """Single value generates single bar."""
        result = sparkline([100])
        assert len(result) == 1
        assert result == "█"

    def test_all_zeros(self):
        """All zeros shows minimal bars."""
        result = sparkline([0, 0, 0, 0])
        assert result == "▁▁▁▁"

    def test_ascending_values(self):
        """Ascending values show increasing bars."""
        result = sparkline([0, 25, 50, 75, 100])
        # Should show increasing trend
        assert result[0] == " " or result[0] == "▁"  # lowest
        assert result[-1] == "█"  # highest

    def test_mixed_values(self):
        """Mixed values show appropriate variation."""
        result = sparkline([10, 50, 20, 80, 30])
        assert len(result) == 5
        # Just check it produces valid sparkline chars
        valid_chars = " ▁▂▃▄▅▆▇█"
        for char in result:
            assert char in valid_chars


class TestDailyStats:
    """Tests for DailyStats dataclass."""

    def test_creation(self):
        """Can create DailyStats."""
        today = date.today()
        stats = DailyStats(date=today, message_count=100, session_count=5, tool_call_count=50)
        assert stats.date == today
        assert stats.message_count == 100
        assert stats.session_count == 5
        assert stats.tool_call_count == 50


class TestStatsCache:
    """Tests for StatsCache methods."""

    def test_get_today_found(self):
        """get_today returns today's stats when present."""
        today = date.today()
        stats = [
            DailyStats(date=today - timedelta(days=1), message_count=50, session_count=2, tool_call_count=20),
            DailyStats(date=today, message_count=100, session_count=5, tool_call_count=50),
        ]
        cache = StatsCache(daily_activity=stats, total_sessions=10, total_messages=500)

        result = cache.get_today()
        assert result is not None
        assert result.message_count == 100

    def test_get_today_not_found(self):
        """get_today returns None when today not present."""
        yesterday = date.today() - timedelta(days=1)
        stats = [DailyStats(date=yesterday, message_count=50, session_count=2, tool_call_count=20)]
        cache = StatsCache(daily_activity=stats, total_sessions=10, total_messages=500)

        result = cache.get_today()
        assert result is None

    def test_get_last_n_days(self):
        """get_last_n_days returns correct number of days with gaps filled."""
        today = date.today()
        # Only have data for today and 2 days ago
        stats = [
            DailyStats(date=today - timedelta(days=2), message_count=50, session_count=2, tool_call_count=20),
            DailyStats(date=today, message_count=100, session_count=5, tool_call_count=50),
        ]
        cache = StatsCache(daily_activity=stats, total_sessions=10, total_messages=500)

        result = cache.get_last_n_days(3)
        assert len(result) == 3
        # Should be in chronological order
        assert result[0].date == today - timedelta(days=2)
        assert result[0].message_count == 50
        assert result[1].date == today - timedelta(days=1)
        assert result[1].message_count == 0  # Filled with zero
        assert result[2].date == today
        assert result[2].message_count == 100


class TestLoadStatsCache:
    """Tests for load_stats_cache function."""

    def test_file_not_exists(self):
        """Returns None when file doesn't exist."""
        with patch("cdash.data.stats.get_stats_cache_path") as mock_path:
            mock_path.return_value = Path("/nonexistent/path/stats-cache.json")
            result = load_stats_cache()
            assert result is None

    def test_valid_file(self):
        """Parses valid stats-cache.json correctly."""
        data = {
            "version": 1,
            "lastComputedDate": "2026-01-16",
            "dailyActivity": [
                {"date": "2026-01-15", "messageCount": 100, "sessionCount": 5, "toolCallCount": 50},
                {"date": "2026-01-16", "messageCount": 200, "sessionCount": 10, "toolCallCount": 100},
            ],
            "totalSessions": 15,
            "totalMessages": 300,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with patch("cdash.data.stats.get_stats_cache_path") as mock_path:
                mock_path.return_value = temp_path
                result = load_stats_cache()

                assert result is not None
                assert len(result.daily_activity) == 2
                assert result.total_sessions == 15
                assert result.total_messages == 300
                assert result.daily_activity[0].message_count == 100
        finally:
            temp_path.unlink()

    def test_invalid_json(self):
        """Returns None for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            temp_path = Path(f.name)

        try:
            with patch("cdash.data.stats.get_stats_cache_path") as mock_path:
                mock_path.return_value = temp_path
                result = load_stats_cache()
                assert result is None
        finally:
            temp_path.unlink()


class TestStatsPanel:
    """Tests for StatsPanel widget."""

    @pytest.mark.asyncio
    async def test_stats_panel_present(self):
        """Stats panel is present in the app."""
        from cdash.app import ClaudeDashApp
        from cdash.components.stats import StatsPanel

        app = ClaudeDashApp()
        async with app.run_test():
            panel = app.query_one(StatsPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_trend_widget_present(self):
        """Trend widget is present in stats panel."""
        from cdash.app import ClaudeDashApp
        from cdash.components.stats import TrendWidget

        app = ClaudeDashApp()
        async with app.run_test():
            widget = app.query_one(TrendWidget)
            assert widget is not None
