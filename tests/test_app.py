"""Tests for the main application."""

from cdash.app import ClaudeDashApp
from cdash.components.header import HeaderPanel
from cdash.components.sessions import SessionsPanel


class TestAppStartup:
    """Test that the app starts correctly."""

    async def test_app_launches(self):
        """App launches without crash."""
        app = ClaudeDashApp()
        async with app.run_test():
            # App should have mounted
            assert app.is_running

    async def test_header_panel_present(self):
        """Header panel widget is mounted."""
        app = ClaudeDashApp()
        async with app.run_test():
            header = app.query_one(HeaderPanel)
            assert header is not None

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


class TestSessionsPanel:
    """Test the sessions panel."""

    async def test_sessions_panel_present(self):
        """Sessions panel is mounted."""
        app = ClaudeDashApp()
        async with app.run_test():
            panel = app.query_one(SessionsPanel)
            assert panel is not None

    async def test_sessions_panel_has_container(self):
        """Sessions panel has scrollable card container."""
        from textual.containers import VerticalScroll

        app = ClaudeDashApp()
        async with app.run_test():
            panel = app.query_one(SessionsPanel)
            container = panel.query_one("#cards-container", VerticalScroll)
            assert container is not None
