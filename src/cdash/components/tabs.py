"""Tab infrastructure for the dashboard."""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import Collapsible, LoadingIndicator, Static, TabbedContent, TabPane

from cdash.components.ci import CIActivityPanel, CITab
from cdash.components.header import TodayHeader
from cdash.components.mcp import MCPServersTab
from cdash.components.plugins import PluginsTab
from cdash.components.sessions import ActiveSessionsPanel
from cdash.components.stats import StatsPanel
from cdash.components.tools import ToolBreakdownPanel
from cdash.theme import CORAL, TAB_ICONS_ASCII


class PlaceholderTab(Vertical):
    """Placeholder content for tabs not yet implemented."""

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        yield Static(self._message)


class LoadingScreen(Vertical):
    """Loading screen shown during app startup."""

    DEFAULT_CSS = """
    LoadingScreen {
        height: 100%;
        width: 100%;
        align: center middle;
    }
    LoadingScreen > #loading-content {
        width: auto;
        height: auto;
        align: center middle;
        padding: 2;
    }
    LoadingScreen > #loading-content > #loading-title {
        text-style: bold;
        margin-bottom: 1;
    }
    LoadingScreen > #loading-content > #loading-status {
        color: $text-muted;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Center(id="loading-content"):
            yield Static(f"[{CORAL}]claude-dash[/]", id="loading-title")
            yield LoadingIndicator()
            yield Static("Loading sessions...", id="loading-status")

    def set_status(self, status: str) -> None:
        """Update the loading status text."""
        try:
            self.query_one("#loading-status", Static).update(status)
        except Exception:
            pass


class OverviewContent(Vertical):
    """Main content of the Overview tab (shown after loading)."""

    def compose(self) -> ComposeResult:
        yield TodayHeader()
        yield ActiveSessionsPanel()
        with Collapsible(title="Stats & Trends", collapsed=True, id="stats-collapsible"):
            yield StatsPanel()
            yield ToolBreakdownPanel()
            yield CIActivityPanel()


class OverviewTab(Vertical):
    """Overview tab with sessions, stats, and tool breakdown."""

    def __init__(self) -> None:
        super().__init__()
        self._is_loaded = False

    def compose(self) -> ComposeResult:
        # Start with loading screen
        yield LoadingScreen(id="loading-screen")
        # Content is hidden initially (display: none in CSS)
        yield OverviewContent(id="overview-content")

    def on_mount(self) -> None:
        """Hide content initially."""
        try:
            self.query_one("#overview-content").display = False
        except Exception:
            pass

    def show_content(self) -> None:
        """Switch from loading screen to content."""
        if self._is_loaded:
            return
        self._is_loaded = True
        try:
            self.query_one("#loading-screen").display = False
            self.query_one("#overview-content").display = True
        except Exception:
            pass

    def refresh_data(
        self,
        msgs_today: int = 0,
        tools_today: int = 0,
        active_count: int = 0,
    ) -> None:
        """Refresh all panels in the overview tab.

        Args:
            msgs_today: Today's message count
            tools_today: Today's tool count
            active_count: Number of active sessions
        """
        # Show content on first refresh (transition from loading)
        self.show_content()

        try:
            content = self.query_one(OverviewContent)
            header = content.query_one(TodayHeader)
            header.update_stats(msgs=msgs_today, tools=tools_today, active=active_count)
            header.mark_refreshed()
        except Exception:
            pass
        try:
            content = self.query_one(OverviewContent)
            content.query_one(ActiveSessionsPanel).refresh_sessions()
        except Exception:
            pass
        try:
            content = self.query_one(OverviewContent)
            content.query_one(StatsPanel).refresh_stats()
        except Exception:
            pass
        try:
            content = self.query_one(OverviewContent)
            content.query_one(ToolBreakdownPanel).refresh_tools()
        except Exception:
            pass

    def update_ci(
        self,
        ci_runs: int = 0,
        ci_passed: int = 0,
        ci_failed: int = 0,
        ci_repos: list | None = None,
    ) -> None:
        """Update CI panel with async-fetched data."""
        try:
            content = self.query_one(OverviewContent)
            ci_panel = content.query_one(CIActivityPanel)
            ci_panel.update_stats(ci_runs, ci_passed, ci_failed)
            if ci_repos:
                ci_panel.update_repos(ci_repos)
        except Exception:
            pass


class DashboardTabs(Vertical):
    """Main tabbed content area for the dashboard."""

    def compose(self) -> ComposeResult:
        # Tab labels with icons
        # Order: Overview, GitHub, Plugins, MCP (4 tabs)
        ic = TAB_ICONS_ASCII
        with TabbedContent(initial="tab-overview"):
            with TabPane(f"{ic['overview']} Overview", id="tab-overview"):
                yield OverviewTab()
            with TabPane(f"{ic['ci']} GitHub", id="tab-github"):
                yield CITab()
            with TabPane(f"{ic['plugins']} Plugins", id="tab-plugins"):
                yield PluginsTab()
            with TabPane(f"{ic['mcp']} MCP", id="tab-mcp"):
                yield MCPServersTab()

    @property
    def active(self) -> str:
        """Get the active tab ID."""
        return self.query_one(TabbedContent).active

    @active.setter
    def active(self, tab_id: str) -> None:
        """Set the active tab."""
        self.query_one(TabbedContent).active = tab_id
