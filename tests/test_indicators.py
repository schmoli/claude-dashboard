"""Tests for RefreshIndicator (liveness indicator) widget."""

import time

import pytest

from cdash.components.indicators import (
    ERROR_THRESHOLD,
    WARN_THRESHOLD,
    LivenessState,
    RefreshIndicator,
)


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
    async def test_init_state_when_never_refreshed(self):
        """Shows init state when never refreshed."""
        indicator = RefreshIndicator()
        assert indicator.state == LivenessState.INIT

    @pytest.mark.asyncio
    async def test_refreshing_state_after_mark(self):
        """Shows refreshing state immediately after mark_refreshed."""
        indicator = RefreshIndicator()
        indicator.mark_refreshed()
        assert indicator.state == LivenessState.REFRESHING

    @pytest.mark.asyncio
    async def test_live_state_for_recent_refresh(self):
        """Shows live state for recent refresh."""
        indicator = RefreshIndicator()
        indicator._last_refresh = time.time() - 5
        indicator._refreshing_until = 0  # Past refreshing animation
        indicator._tick()
        assert indicator.state == LivenessState.LIVE

    @pytest.mark.asyncio
    async def test_warn_state_for_stale_refresh(self):
        """Shows warn state after missing refresh cycles."""
        indicator = RefreshIndicator()
        indicator._last_refresh = time.time() - (WARN_THRESHOLD + 1)
        indicator._refreshing_until = 0
        indicator._tick()
        assert indicator.state == LivenessState.WARN

    @pytest.mark.asyncio
    async def test_error_state_for_very_stale_refresh(self):
        """Shows error state after missing many refresh cycles."""
        indicator = RefreshIndicator()
        indicator._last_refresh = time.time() - (ERROR_THRESHOLD + 1)
        indicator._refreshing_until = 0
        indicator._tick()
        assert indicator.state == LivenessState.ERROR

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
    async def test_status_bar_has_refresh_indicator(self):
        """StatusBar contains refresh indicator."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            indicator = app.query_one("#status-refresh", RefreshIndicator)
            assert indicator is not None
