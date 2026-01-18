"""TodayHeader widget showing big numbers and refresh info."""

import time

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.theme import CORAL


class TodayHeader(Horizontal):
    """Big numbers showing today's totals and refresh info."""

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
        yield RefreshIndicator(id="refresh-info")

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
        try:
            indicator = self.query_one("#refresh-info", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass

    def _update_display(self) -> None:
        """Update all display widgets."""
        try:
            msgs_widget = self.query_one("#msgs-stat", Static)
            tools_widget = self.query_one("#tools-stat", Static)
            active_widget = self.query_one("#active-stat", Static)

            msgs_widget.update(f"[{CORAL} bold]{self._msgs}[/] messages")
            tools_widget.update(f"[{CORAL} bold]{self._tools}[/] tools")
            active_widget.update(f"[{CORAL} bold]{self._active}[/] active")
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
