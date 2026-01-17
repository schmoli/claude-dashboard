"""Tests for TodayHeader widget."""

import time

import pytest

from cdash.components.header import TodayHeader


class TestTodayHeader:
    """Tests for TodayHeader widget."""

    @pytest.mark.asyncio
    async def test_header_renders(self):
        """TodayHeader can be created and rendered."""
        header = TodayHeader()
        # Widget should exist with default values
        assert header is not None

    @pytest.mark.asyncio
    async def test_header_update_stats(self):
        """TodayHeader updates stats correctly."""
        header = TodayHeader()
        header.update_stats(msgs=847, tools=142, active=3)

        assert header._msgs == 847
        assert header._tools == 142
        assert header._active == 3

    @pytest.mark.asyncio
    async def test_header_refresh_info(self):
        """TodayHeader shows refresh timestamp."""
        header = TodayHeader()
        header.mark_refreshed()

        # Should have recent timestamp
        assert header._last_refresh > 0
        assert time.time() - header._last_refresh < 5

    @pytest.mark.asyncio
    async def test_format_refresh_ago(self):
        """format_refresh_ago shows human-readable time."""
        header = TodayHeader()

        # Just refreshed
        header._last_refresh = time.time()
        assert "0s" in header._format_refresh_ago()

        # 30 seconds ago
        header._last_refresh = time.time() - 30
        assert "30s" in header._format_refresh_ago()

        # 2 minutes ago
        header._last_refresh = time.time() - 120
        assert "2m" in header._format_refresh_ago()
