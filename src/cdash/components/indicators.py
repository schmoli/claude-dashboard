"""Refresh indicator widgets for auto-updating panels."""

import time

from textual.widgets import Static


class RefreshIndicator(Static):
    """Auto-updating timestamp indicator.

    Shows "↻ Xs ago" and updates every second via CSS animation trick.
    Parent widget should call mark_refreshed() when data is fetched.
    """

    def __init__(self, id: str | None = None) -> None:
        super().__init__("", id=id)
        self._last_refresh: float = 0.0
        self._update_timer = None

    def on_mount(self) -> None:
        """Start the update timer when mounted."""
        # Update every second to keep the time display fresh
        self._update_timer = self.set_interval(1.0, self._tick)

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed."""
        self._last_refresh = time.time()
        self._update_display()

    def _tick(self) -> None:
        """Called every second to update display."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed time."""
        self.update(f"↻ {self._format_refresh_ago()}")

    def _format_refresh_ago(self) -> str:
        """Format time since last refresh as human-readable."""
        if self._last_refresh == 0:
            return "..."

        elapsed = int(time.time() - self._last_refresh)
        if elapsed < 60:
            return f"{elapsed}s"
        mins = elapsed // 60
        if mins < 60:
            return f"{mins}m"
        hours = mins // 60
        return f"{hours}h"

    @property
    def last_refresh(self) -> float:
        """Get the timestamp of last refresh."""
        return self._last_refresh
