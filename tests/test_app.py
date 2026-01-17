"""Tests for the main application."""

from cdash.app import ClaudeDashApp, StatusBar
from cdash.components.sessions import ActiveSessionsPanel


class TestAppStartup:
    """Test that the app starts correctly."""

    async def test_app_launches(self):
        """App launches without crash."""
        app = ClaudeDashApp()
        async with app.run_test():
            # App should have mounted
            assert app.is_running

    async def test_status_bar_present(self):
        """Status bar widget is mounted."""
        app = ClaudeDashApp()
        async with app.run_test():
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


class TestActiveSessionsPanel:
    """Test the active sessions panel."""

    async def test_sessions_panel_present(self):
        """Active sessions panel is mounted."""
        app = ClaudeDashApp()
        async with app.run_test():
            panel = app.query_one(ActiveSessionsPanel)
            assert panel is not None

    async def test_sessions_panel_has_title(self):
        """Active sessions panel shows title."""
        app = ClaudeDashApp()
        async with app.run_test():
            # Check for the section title
            title = app.query_one(".section-title")
            assert title is not None
