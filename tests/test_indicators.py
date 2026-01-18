"""Tests for RefreshIndicator widget."""

import time

import pytest

from cdash.components.indicators import RefreshIndicator


class TestRefreshIndicator:
    """Tests for RefreshIndicator widget."""

    @pytest.mark.asyncio
    async def test_indicator_creates(self):
        """RefreshIndicator can be created."""
        indicator = RefreshIndicator()
        assert indicator is not None

    @pytest.mark.asyncio
    async def test_indicator_default_timestamp(self):
        """RefreshIndicator starts with zero timestamp."""
        indicator = RefreshIndicator()
        assert indicator.last_refresh == 0.0

    @pytest.mark.asyncio
    async def test_mark_refreshed_sets_timestamp(self):
        """mark_refreshed() sets current timestamp."""
        indicator = RefreshIndicator()
        before = time.time()
        indicator.mark_refreshed()
        after = time.time()

        assert indicator.last_refresh >= before
        assert indicator.last_refresh <= after

    @pytest.mark.asyncio
    async def test_format_never_refreshed(self):
        """Shows ... when never refreshed."""
        indicator = RefreshIndicator()
        assert indicator._format_refresh_ago() == "..."

    @pytest.mark.asyncio
    async def test_format_seconds_ago(self):
        """Shows seconds for recent refresh."""
        indicator = RefreshIndicator()
        indicator._last_refresh = time.time() - 5
        result = indicator._format_refresh_ago()
        assert "s" in result
        assert "5" in result

    @pytest.mark.asyncio
    async def test_format_minutes_ago(self):
        """Shows minutes for older refresh."""
        indicator = RefreshIndicator()
        indicator._last_refresh = time.time() - 120  # 2 minutes
        result = indicator._format_refresh_ago()
        assert "2m" in result

    @pytest.mark.asyncio
    async def test_format_hours_ago(self):
        """Shows hours for much older refresh."""
        indicator = RefreshIndicator()
        indicator._last_refresh = time.time() - 7200  # 2 hours
        result = indicator._format_refresh_ago()
        assert "2h" in result

    @pytest.mark.asyncio
    async def test_with_id(self):
        """RefreshIndicator can be created with id."""
        indicator = RefreshIndicator(id="my-indicator")
        assert indicator.id == "my-indicator"


class TestRefreshIndicatorIntegration:
    """Integration tests for RefreshIndicator in panels."""

    @pytest.mark.asyncio
    async def test_sessions_panel_has_refresh_indicator(self):
        """ActiveSessionsPanel contains refresh indicator."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            # Find the indicator
            indicator = app.query_one("#sessions-refresh", RefreshIndicator)
            assert indicator is not None

    @pytest.mark.asyncio
    async def test_tools_panel_has_refresh_indicator(self):
        """ToolBreakdownPanel contains refresh indicator."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            indicator = app.query_one("#tools-refresh", RefreshIndicator)
            assert indicator is not None

    @pytest.mark.asyncio
    async def test_ci_panel_has_refresh_indicator(self):
        """CIActivityPanel contains refresh indicator."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            indicator = app.query_one("#ci-refresh", RefreshIndicator)
            assert indicator is not None

    @pytest.mark.asyncio
    async def test_header_has_refresh_indicator(self):
        """TodayHeader contains refresh indicator."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            indicator = app.query_one("#refresh-info", RefreshIndicator)
            assert indicator is not None
