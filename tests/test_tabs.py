"""Tests for tab infrastructure (standalone components).

Note: The main app uses a simplified k9s-style layout without tabs.
These tests verify the tabs module components can still be used
in future iterations when tab navigation is re-added.
"""

import pytest

from cdash.components.tabs import (
    DashboardTabs,
    LoadingScreen,
    OverviewContent,
    OverviewTab,
    PlaceholderTab,
)


class TestDashboardTabs:
    """Tests for DashboardTabs widget (standalone)."""

    @pytest.mark.asyncio
    async def test_tabs_compose(self):
        """DashboardTabs composes without error."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield DashboardTabs()

        app = TestApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            assert tabs is not None

    @pytest.mark.asyncio
    async def test_overview_tab_default(self):
        """Overview tab is the default active tab."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield DashboardTabs()

        app = TestApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-overview"

    @pytest.mark.asyncio
    async def test_four_tabs_exist(self):
        """All four tabs exist (Overview, GitHub, Plugins, MCP)."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield DashboardTabs()

        app = TestApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            # Check all tab panes exist
            assert tabs.query_one("#tab-overview") is not None
            assert tabs.query_one("#tab-github") is not None
            assert tabs.query_one("#tab-plugins") is not None
            assert tabs.query_one("#tab-mcp") is not None


class TestTabNavigation:
    """Tests for tab programmatic navigation (standalone)."""

    @pytest.mark.asyncio
    async def test_set_active_tab(self):
        """Can set active tab programmatically."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield DashboardTabs()

        app = TestApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            tabs.active = "tab-github"
            assert tabs.active == "tab-github"

    @pytest.mark.asyncio
    async def test_switch_tabs_multiple(self):
        """Can switch between tabs programmatically."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield DashboardTabs()

        app = TestApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            tabs.active = "tab-plugins"
            assert tabs.active == "tab-plugins"
            tabs.active = "tab-overview"
            assert tabs.active == "tab-overview"


class TestOverviewTab:
    """Tests for Overview tab content (standalone)."""

    @pytest.mark.asyncio
    async def test_overview_tab_has_sessions_panel(self):
        """Overview tab contains sessions panel."""
        from textual.app import App

        from cdash.components.sessions import ActiveSessionsPanel

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            panel = overview.query_one(ActiveSessionsPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_overview_tab_has_stats_panel(self):
        """Overview tab contains stats panel."""
        from textual.app import App

        from cdash.components.stats import StatsPanel

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            panel = overview.query_one(StatsPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_overview_tab_has_tools_panel(self):
        """Overview tab contains tools panel."""
        from textual.app import App

        from cdash.components.tools import ToolBreakdownPanel

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            panel = overview.query_one(ToolBreakdownPanel)
            assert panel is not None


class TestAllTabsImplemented:
    """Tests that all tabs are implemented."""

    @pytest.mark.asyncio
    async def test_no_placeholder_tabs_remain(self):
        """All tabs have real implementations."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield DashboardTabs()

        app = TestApp()
        async with app.run_test():
            placeholders = app.query(PlaceholderTab)
            # No more placeholder tabs!
            assert len(placeholders) == 0


class TestTabsRender:
    """Tests that tab pages actually render with content."""

    @pytest.mark.asyncio
    async def test_overview_tab_has_height(self):
        """Overview tab renders with non-zero height."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            # Must have positive height - catches height: 100% -> 0 bug
            assert overview.size.height > 0

    @pytest.mark.asyncio
    async def test_github_tab_has_height(self):
        """GitHub tab renders with non-zero height."""
        from textual.app import App

        from cdash.components.ci import CITab

        class TestApp(App):
            def compose(self):
                yield CITab()

        app = TestApp()
        async with app.run_test():
            github_tab = app.query_one(CITab)
            assert github_tab.size.height > 0

    @pytest.mark.asyncio
    async def test_plugins_tab_has_height(self):
        """Plugins tab renders with non-zero height."""
        from textual.app import App

        from cdash.components.plugins import PluginsTab

        class TestApp(App):
            def compose(self):
                yield PluginsTab()

        app = TestApp()
        async with app.run_test():
            plugins_tab = app.query_one(PluginsTab)
            assert plugins_tab.size.height > 0

    @pytest.mark.asyncio
    async def test_mcp_tab_has_height(self):
        """MCP tab renders with non-zero height."""
        from textual.app import App

        from cdash.components.mcp import MCPServersTab

        class TestApp(App):
            def compose(self):
                yield MCPServersTab()

        app = TestApp()
        async with app.run_test():
            mcp_tab = app.query_one(MCPServersTab)
            assert mcp_tab.size.height > 0

    @pytest.mark.asyncio
    async def test_overview_has_visible_content(self):
        """Overview tab has visible panels."""
        import asyncio

        from textual.app import App
        from textual.widgets import Collapsible

        from cdash.components.sessions import ActiveSessionsPanel
        from cdash.components.stats import StatsPanel
        from cdash.components.tools import ToolBreakdownPanel

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            # Wait for loading timer to complete
            await asyncio.sleep(0.15)
            overview = app.query_one(OverviewTab)
            # Sessions panel exists
            sessions = overview.query_one(ActiveSessionsPanel)
            assert sessions is not None

            # Stats and tools are inside a collapsible (collapsed by default)
            collapsible = overview.query_one("#stats-collapsible", Collapsible)
            assert collapsible.collapsed is True

            # Panels exist inside collapsible
            stats = overview.query_one(StatsPanel)
            tools = overview.query_one(ToolBreakdownPanel)
            assert stats is not None
            assert tools is not None


class TestLoadingIndicator:
    """Tests for the loading indicator during app startup."""

    @pytest.mark.asyncio
    async def test_loading_screen_widget_exists(self):
        """LoadingScreen widget is present in OverviewTab."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            loading_screen = overview.query_one(LoadingScreen)
            assert loading_screen is not None

    @pytest.mark.asyncio
    async def test_overview_content_widget_exists(self):
        """OverviewContent widget is present in OverviewTab."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            content = overview.query_one(OverviewContent)
            assert content is not None

    @pytest.mark.asyncio
    async def test_loading_screen_has_title(self):
        """LoadingScreen shows app title."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            loading_screen = overview.query_one(LoadingScreen)
            title = loading_screen.query_one("#loading-title")
            assert title is not None

    @pytest.mark.asyncio
    async def test_loading_screen_has_indicator(self):
        """LoadingScreen contains a LoadingIndicator widget."""
        from textual.app import App
        from textual.widgets import LoadingIndicator

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            loading_screen = overview.query_one(LoadingScreen)
            indicator = loading_screen.query_one(LoadingIndicator)
            assert indicator is not None

    @pytest.mark.asyncio
    async def test_loading_screen_has_status_text(self):
        """LoadingScreen shows status text."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            loading_screen = overview.query_one(LoadingScreen)
            status = loading_screen.query_one("#loading-status")
            assert status is not None

    @pytest.mark.asyncio
    async def test_content_shown_after_refresh(self):
        """Content is shown after show_content is called."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            content = overview.query_one(OverviewContent)
            # Initially content is hidden (loading screen visible)
            assert content.display is False
            # Call show_content to transition
            overview.show_content()
            # Content should now be displayed
            assert content.display is True

    @pytest.mark.asyncio
    async def test_loading_hidden_after_refresh(self):
        """Loading screen is hidden after show_content is called."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            loading_screen = overview.query_one(LoadingScreen)
            # Initially loading screen is visible
            assert loading_screen.display is True
            # Call show_content to transition
            overview.show_content()
            # Loading should be hidden
            assert loading_screen.display is False

    @pytest.mark.asyncio
    async def test_show_content_idempotent(self):
        """Calling show_content multiple times is safe."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield OverviewTab()

        app = TestApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            # Call show_content multiple times
            overview.show_content()
            overview.show_content()
            overview.show_content()
            # Should still work correctly
            content = overview.query_one(OverviewContent)
            loading_screen = overview.query_one(LoadingScreen)
            assert content.display is True
            assert loading_screen.display is False
