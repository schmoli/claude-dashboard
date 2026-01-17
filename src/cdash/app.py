"""Main Textual application for Claude Dashboard."""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Static

from cdash.components.tabs import DashboardTabs, OverviewTab
from cdash.data.sessions import get_active_sessions
from cdash.data.stats import load_stats_cache


class StatusBar(Static):
    """Top status bar showing app name and summary stats."""

    def __init__(self) -> None:
        super().__init__()
        self._active_count = 0

    def compose(self) -> ComposeResult:
        yield Static("claude-dash", id="app-name")
        yield Static("", id="active-count")
        yield Static("", id="today-stats")

    def update_stats(self, active_count: int, msgs_today: int = 0, tools_today: int = 0) -> None:
        """Update the stats display."""
        self._active_count = active_count
        count_widget = self.query_one("#active-count", Static)
        stats_widget = self.query_one("#today-stats", Static)

        if active_count > 0:
            count_widget.update(f"│ {active_count} active")
        else:
            count_widget.update("")

        if msgs_today > 0 or tools_today > 0:
            stats_widget.update(f"│ {msgs_today} msgs │ {tools_today} tools")
        else:
            stats_widget.update("")


class ClaudeDashApp(App):
    """Claude Code monitoring dashboard."""

    TITLE = "claude-dash"
    CSS = """
    StatusBar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
        layout: horizontal;
    }

    #app-name {
        text-style: bold;
        width: auto;
    }

    #active-count {
        width: auto;
        margin-left: 1;
    }

    #today-stats {
        width: auto;
        margin-left: 1;
    }

    #main-content {
        height: 100%;
    }

    ActiveSessionsPanel {
        height: auto;
        max-height: 10;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "switch_tab('tab-overview')", "Overview"),
        ("2", "switch_tab('tab-plugins')", "Plugins"),
        ("3", "switch_tab('tab-mcp')", "MCP"),
        ("4", "switch_tab('tab-skills')", "Skills"),
        ("5", "switch_tab('tab-agents')", "Agents"),
    ]

    # Refresh interval in seconds
    REFRESH_INTERVAL = 10.0  # Increased from 5s to reduce load

    def compose(self) -> ComposeResult:
        yield StatusBar()
        yield DashboardTabs(id="main-content")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the refresh timer when the app mounts."""
        self._refresh_data()
        self.set_interval(self.REFRESH_INTERVAL, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh all data displays."""
        # Update active session count and today's stats in status bar
        active_sessions = get_active_sessions()
        status_bar = self.query_one(StatusBar)

        # Get today's stats
        msgs_today = 0
        tools_today = 0
        stats_cache = load_stats_cache()
        if stats_cache:
            today = stats_cache.get_today()
            if today:
                msgs_today = today.message_count
                tools_today = today.tool_call_count

        status_bar.update_stats(len(active_sessions), msgs_today, tools_today)

        # Refresh the overview tab data
        try:
            overview_tab = self.query_one(OverviewTab)
            overview_tab.refresh_data()
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        tabs = self.query_one(DashboardTabs)
        tabs.active = tab_id

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)
