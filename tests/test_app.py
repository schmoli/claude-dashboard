"""Tests for the main application."""

import pytest

from cdash.app import ClaudeDashApp, StatusBar


class TestAppStartup:
    """Test that the app starts correctly."""

    async def test_app_launches(self):
        """App launches without crash."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            # App should have mounted
            assert app.is_running

    async def test_status_bar_present(self):
        """Status bar widget is mounted."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            status_bar = app.query_one(StatusBar)
            assert status_bar is not None

    async def test_app_title(self):
        """App has correct title."""
        app = ClaudeDashApp()
        assert app.TITLE == "claude-dash"


class TestAppQuit:
    """Test quit functionality."""

    async def test_q_quits(self):
        """Pressing q quits the application."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("q")
            # App should have exited with code 0
            assert app.return_code == 0
