"""Tests for StatusBar widget."""

import pytest

from cdash.app import StatusBar


class TestStatusBar:
    """Tests for StatusBar widget."""

    @pytest.mark.asyncio
    async def test_statusbar_renders(self):
        """StatusBar can be created and rendered."""
        statusbar = StatusBar()
        assert statusbar is not None

    @pytest.mark.asyncio
    async def test_statusbar_update_stats(self):
        """StatusBar updates internal stats correctly."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            statusbar = app.query_one(StatusBar)
            statusbar.update_stats(active_count=3, msgs_today=847, tools_today=142)

            assert statusbar._active_count == 3
            assert statusbar._msgs == 847
            assert statusbar._tools == 142

    @pytest.mark.asyncio
    async def test_statusbar_has_mark_refreshed(self):
        """StatusBar has mark_refreshed method."""
        statusbar = StatusBar()
        assert hasattr(statusbar, "mark_refreshed")
        assert callable(statusbar.mark_refreshed)
