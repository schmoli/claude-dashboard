"""TodayHeader widget showing big numbers and refresh info."""

import time

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class TodayHeader(Horizontal):
    """Big numbers showing today's totals and refresh info."""

    DEFAULT_CSS = """
    TodayHeader {
        height: 3;
        padding: 0 1;
        margin-bottom: 1;
    }

    TodayHeader > .header-title {
        text-style: bold;
        color: $text;
        width: auto;
    }

    TodayHeader > .stat-block {
        width: auto;
        margin-left: 2;
    }

    TodayHeader > .stat-block .stat-value {
        color: $accent;
        text-style: bold;
    }

    TodayHeader > .stat-block .stat-label {
        color: $text-muted;
    }

    TodayHeader > .spacer {
        width: 1fr;
    }

    TodayHeader > .refresh-info {
        color: $text-muted;
        width: auto;
        text-align: right;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._msgs = 0
        self._tools = 0
        self._active = 0
        self._last_refresh = 0.0

    def compose(self) -> ComposeResult:
        yield Static("TODAY", classes="header-title")
        yield Static("", id="msgs-stat", classes="stat-block")
        yield Static("", id="tools-stat", classes="stat-block")
        yield Static("", id="active-stat", classes="stat-block")
        yield Static("", classes="spacer")
        yield Static("", id="refresh-info", classes="refresh-info")

    def update_stats(self, msgs: int = 0, tools: int = 0, active: int = 0) -> None:
        """Update the displayed stats.

        Args:
            msgs: Today's message count
            tools: Today's tool count
            active: Number of active sessions
        """
        self._msgs = msgs
        self._tools = tools
        self._active = active
        self._update_display()

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed."""
        self._last_refresh = time.time()
        self._update_display()

    def _update_display(self) -> None:
        """Update all display widgets."""
        try:
            msgs_widget = self.query_one("#msgs-stat", Static)
            tools_widget = self.query_one("#tools-stat", Static)
            active_widget = self.query_one("#active-stat", Static)
            refresh_widget = self.query_one("#refresh-info", Static)

            msgs_widget.update(f"[cyan bold]{self._msgs}[/] messages")
            tools_widget.update(f"[cyan bold]{self._tools}[/] tools")
            active_widget.update(f"[cyan bold]{self._active}[/] active")
            refresh_widget.update(f"↻ {self._format_refresh_ago()}")
        except Exception:
            # Widget may not be mounted yet
            pass

    def _format_refresh_ago(self) -> str:
        """Format time since last refresh as human-readable."""
        if self._last_refresh == 0:
            return "never"

        elapsed = int(time.time() - self._last_refresh)
        if elapsed < 60:
            return f"refreshed {elapsed}s ago"
        mins = elapsed // 60
        return f"refreshed {mins}m ago"
