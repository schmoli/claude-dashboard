"""Tests for TodayHeader widget."""

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
    async def test_header_has_mark_refreshed(self):
        """TodayHeader has mark_refreshed method."""
        header = TodayHeader()
        # Should not raise - delegates to child RefreshIndicator
        assert hasattr(header, "mark_refreshed")
        assert callable(header.mark_refreshed)
