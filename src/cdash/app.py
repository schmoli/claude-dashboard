"""Main Textual application for Claude Dashboard."""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Static

from cdash.components.sessions import ActiveSessionsPanel
from cdash.components.stats import StatsPanel
from cdash.components.tools import ToolBreakdownPanel
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
        padding: 1;
    }

    ActiveSessionsPanel {
        height: auto;
        max-height: 10;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    # Refresh interval in seconds
    REFRESH_INTERVAL = 5.0

    def compose(self) -> ComposeResult:
        yield StatusBar()
        yield Container(
            ActiveSessionsPanel(),
            StatsPanel(),
            ToolBreakdownPanel(),
            id="main-content",
        )
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

        # Refresh the sessions panel
        sessions_panel = self.query_one(ActiveSessionsPanel)
        sessions_panel.refresh_sessions()

        # Refresh the stats panel
        stats_panel = self.query_one(StatsPanel)
        stats_panel.refresh_stats()

        # Refresh the tool breakdown panel
        tools_panel = self.query_one(ToolBreakdownPanel)
        tools_panel.refresh_tools()

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)
