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
    async def test_five_tabs_exist(self):
        """All five tabs exist."""
        app = ClaudeDashApp()
        async with app.run_test():
            tabs = app.query_one(DashboardTabs)
            # Check all tab panes exist
            assert tabs.query_one("#tab-overview") is not None
            assert tabs.query_one("#tab-plugins") is not None
            assert tabs.query_one("#tab-mcp") is not None
            assert tabs.query_one("#tab-skills") is not None
            assert tabs.query_one("#tab-agents") is not None


class TestTabNavigation:
    """Tests for tab keyboard navigation."""

    @pytest.mark.asyncio
    async def test_switch_to_plugins_with_2(self):
        """Pressing 2 switches to Plugins tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-plugins"

    @pytest.mark.asyncio
    async def test_switch_to_mcp_with_3(self):
        """Pressing 3 switches to MCP Servers tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-mcp"

    @pytest.mark.asyncio
    async def test_switch_to_skills_with_4(self):
        """Pressing 4 switches to Skills tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("4")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-skills"

    @pytest.mark.asyncio
    async def test_switch_to_agents_with_5(self):
        """Pressing 5 switches to Agents tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("5")
            tabs = app.query_one(DashboardTabs)
            assert tabs.active == "tab-agents"

    @pytest.mark.asyncio
    async def test_switch_back_to_overview_with_1(self):
        """Pressing 1 switches back to Overview tab."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("3")  # Go to MCP
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


class TestPlaceholderTabs:
    """Tests for placeholder tabs."""

    @pytest.mark.asyncio
    async def test_plugins_tab_has_placeholder(self):
        """Plugins tab shows placeholder message."""
        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            await pilot.press("2")
            placeholders = app.query(PlaceholderTab)
            # At least one placeholder should be visible
            assert len(placeholders) >= 1
