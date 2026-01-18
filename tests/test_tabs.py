"""Tests for tab infrastructure."""

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.tabs import DashboardTabs, OverviewTab, PlaceholderTab


class TestDashboardTabs:
    """Tests for DashboardTabs widget."""

    @pytest.mark.asyncio
    async def test_tabs_present(self):
        """Dashboard tabs are present in the app."""
        app = ClaudeDashApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            assert tabs is not None

    @pytest.mark.asyncio
    async def test_overview_tab_default(self):
        """Overview tab is the default active tab."""
        app = ClaudeDashApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-overview"

    @pytest.mark.asyncio
    async def test_four_tabs_exist(self):
        """All four tabs exist (Overview, GitHub, Plugins, MCP)."""
        app = ClaudeDashApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            # Check all tab panes exist
            assert tabs.query_one("#tab-overview") is not None
            assert tabs.query_one("#tab-github") is not None
            assert tabs.query_one("#tab-plugins") is not None
            assert tabs.query_one("#tab-mcp") is not None


class TestTabNavigation:
    """Tests for tab keyboard navigation."""

    @pytest.mark.asyncio
    async def test_switch_to_github_with_2(self):
        """Pressing 2 switches to GitHub tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-github"

    @pytest.mark.asyncio
    async def test_switch_to_plugins_with_3(self):
        """Pressing 3 switches to Plugins tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-plugins"

    @pytest.mark.asyncio
    async def test_switch_to_mcp_with_4(self):
        """Pressing 4 switches to MCP tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("4")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-mcp"

    @pytest.mark.asyncio
    async def test_switch_back_to_overview_with_1(self):
        """Pressing 1 switches back to Overview tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")  # Go to Plugins
            await pilot.press("1")  # Back to Overview
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-overview"


class TestOverviewTab:
    """Tests for Overview tab content."""

    @pytest.mark.asyncio
    async def test_overview_tab_has_sessions_panel(self):
        """Overview tab contains sessions panel."""
        from cdash.components.sessions import ActiveSessionsPanel

        app = ClaudeDashApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            panel = overview.query_one(ActiveSessionsPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_overview_tab_has_stats_panel(self):
        """Overview tab contains stats panel."""
        from cdash.components.stats import StatsPanel

        app = ClaudeDashApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            panel = overview.query_one(StatsPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_overview_tab_has_tools_panel(self):
        """Overview tab contains tools panel."""
        from cdash.components.tools import ToolBreakdownPanel

        app = ClaudeDashApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            panel = overview.query_one(ToolBreakdownPanel)
            assert panel is not None


class TestAllTabsImplemented:
    """Tests that all tabs are implemented."""

    @pytest.mark.asyncio
    async def test_no_placeholder_tabs_remain(self):
        """All tabs have real implementations."""
        app = ClaudeDashApp()
        async with app.run_test():
            placeholders = app.query(PlaceholderTab)
            # No more placeholder tabs!
            assert len(placeholders) == 0


class TestTabsRender:
    """Tests that tab pages actually render with content."""

    @pytest.mark.asyncio
    async def test_overview_tab_has_height(self):
        """Overview tab renders with non-zero height."""
        app = ClaudeDashApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            # Must have positive height - catches height: 100% -> 0 bug
            assert overview.size.height > 0

    @pytest.mark.asyncio
    async def test_github_tab_has_height(self):
        """GitHub tab renders with non-zero height."""
        from cdash.components.ci import CITab

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")  # Switch to GitHub
            github_tab = app.query_one(CITab)
            assert github_tab.size.height > 0

    @pytest.mark.asyncio
    async def test_plugins_tab_has_height(self):
        """Plugins tab renders with non-zero height."""
        from cdash.components.plugins import PluginsTab

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")  # Switch to Plugins
            plugins_tab = app.query_one(PluginsTab)
            assert plugins_tab.size.height > 0

    @pytest.mark.asyncio
    async def test_mcp_tab_has_height(self):
        """MCP tab renders with non-zero height."""
        from cdash.components.mcp import MCPServersTab

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("4")  # Switch to MCP
            mcp_tab = app.query_one(MCPServersTab)
            assert mcp_tab.size.height > 0

    @pytest.mark.asyncio
    async def test_overview_has_visible_content(self):
        """Overview tab has visible panels."""
        from textual.widgets import Collapsible

        from cdash.components.sessions import ActiveSessionsPanel
        from cdash.components.stats import StatsPanel
        from cdash.components.tools import ToolBreakdownPanel

        app = ClaudeDashApp()
        async with app.run_test():
            overview = app.query_one(OverviewTab)
            # Sessions panel should be visible
            sessions = overview.query_one(ActiveSessionsPanel)
            assert sessions.size.height > 0

            # Stats and tools are inside a collapsible (collapsed by default)
            collapsible = overview.query_one("#stats-collapsible", Collapsible)
            assert collapsible.collapsed is True

            # Panels exist inside collapsible
            stats = overview.query_one(StatsPanel)
            tools = overview.query_one(ToolBreakdownPanel)
            assert stats is not None
            assert tools is not None
