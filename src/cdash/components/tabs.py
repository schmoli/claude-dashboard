"""Tab infrastructure for the dashboard."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, TabbedContent, TabPane

from cdash.components.plugins import PluginsTab
from cdash.components.sessions import ActiveSessionsPanel
from cdash.components.stats import StatsPanel
from cdash.components.tools import ToolBreakdownPanel


class PlaceholderTab(Vertical):
    """Placeholder content for tabs not yet implemented."""

    DEFAULT_CSS = """
    PlaceholderTab {
        height: auto;
        padding: 2;
        align: center middle;
    }

    PlaceholderTab > Static {
        text-align: center;
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        yield Static(self._message)


class OverviewTab(Vertical):
    """Overview tab with sessions, stats, and tool breakdown."""

    DEFAULT_CSS = """
    OverviewTab {
        height: 100%;
        padding: 0;
    }
    """

    def compose(self) -> ComposeResult:
        yield ActiveSessionsPanel()
        yield StatsPanel()
        yield ToolBreakdownPanel()

    def refresh_data(self) -> None:
        """Refresh all panels in the overview tab."""
        try:
            self.query_one(ActiveSessionsPanel).refresh_sessions()
        except Exception:
            pass
        try:
            self.query_one(StatsPanel).refresh_stats()
        except Exception:
            pass
        try:
            self.query_one(ToolBreakdownPanel).refresh_tools()
        except Exception:
            pass


class DashboardTabs(Vertical):
    """Main tabbed content area for the dashboard."""

    DEFAULT_CSS = """
    DashboardTabs {
        height: 100%;
    }

    DashboardTabs > TabbedContent {
        height: 100%;
    }

    DashboardTabs TabPane {
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent(initial="tab-overview"):
            with TabPane("Overview", id="tab-overview"):
                yield OverviewTab()
            with TabPane("Plugins", id="tab-plugins"):
                yield PluginsTab()
            with TabPane("MCP Servers", id="tab-mcp"):
                yield PlaceholderTab("MCP Servers tab - Coming in iteration 6")
            with TabPane("Skills", id="tab-skills"):
                yield PlaceholderTab("Skills tab - Coming in iteration 7")
            with TabPane("Agents", id="tab-agents"):
                yield PlaceholderTab("Agents tab - Coming in iteration 8")

    @property
    def active(self) -> str:
        """Get the active tab ID."""
        return self.query_one(TabbedContent).active

    @active.setter
    def active(self, tab_id: str) -> None:
        """Set the active tab."""
        self.query_one(TabbedContent).active = tab_id
