"""Liveness indicator widgets for auto-updating panels."""

import time
from enum import Enum

from textual.widgets import Static


class LivenessState(Enum):
    """States for the liveness indicator."""

    INIT = "init"  # Not yet refreshed
    LIVE = "live"  # Recently refreshed, all good
    REFRESHING = "refreshing"  # Currently refreshing (brief animation)
    WARN = "warn"  # Missed 1-2 refresh cycles
    ERROR = "error"  # Missed 3+ refresh cycles


# Thresholds in seconds (assuming 10s refresh interval)
WARN_THRESHOLD = 25  # ~2 missed cycles
ERROR_THRESHOLD = 45  # ~4 missed cycles
REFRESHING_DURATION = 0.5  # How long to show refreshing state


class RefreshIndicator(Static):
    """Minimal liveness indicator dot.

    Shows a simple dot that changes color based on refresh health:
    - init: dim dot (...)
    - live: green dot (●)
    - refreshing: pulsing coral dot (◉) - brief animation
    - warn: amber dot (●)
    - error: red dot (●)

    Parent widget should call mark_refreshed() when data is fetched.
    """

    DEFAULT_CSS = """
    RefreshIndicator {
        width: 3;
        text-align: right;
    }
    RefreshIndicator.init {
        color: #555555;
    }
    RefreshIndicator.live {
        color: #4a9f4a;
    }
    RefreshIndicator.refreshing {
        color: #e07850;
        text-style: bold;
    }
    RefreshIndicator.warn {
        color: #d4a017;
    }
    RefreshIndicator.error {
        color: #cc4444;
    }
    """

    def __init__(self, id: str | None = None) -> None:
        super().__init__("", id=id)
        self._last_refresh: float = 0.0
        self._state = LivenessState.INIT
        self._update_timer = None
        self._refreshing_until: float = 0.0

    def on_mount(self) -> None:
        """Start the update timer when mounted."""
        self._update_timer = self.set_interval(0.5, self._tick)
        self._update_display()

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed - triggers brief animation."""
        self._last_refresh = time.time()
        self._refreshing_until = self._last_refresh + REFRESHING_DURATION
        self._state = LivenessState.REFRESHING
        self._update_display()

    def _tick(self) -> None:
        """Called periodically to update state."""
        now = time.time()

        # Check if we're still in refreshing animation
        if self._refreshing_until > now:
            if self._state != LivenessState.REFRESHING:
                self._state = LivenessState.REFRESHING
                self._update_display()
            return

        # Determine state based on staleness
        if self._last_refresh == 0:
            new_state = LivenessState.INIT
        else:
            elapsed = now - self._last_refresh
            if elapsed < WARN_THRESHOLD:
                new_state = LivenessState.LIVE
            elif elapsed < ERROR_THRESHOLD:
                new_state = LivenessState.WARN
            else:
                new_state = LivenessState.ERROR

        if new_state != self._state:
            self._state = new_state
            self._update_display()

    def _update_display(self) -> None:
        """Update the displayed dot and CSS class."""
        # Remove old state classes
        for state in LivenessState:
            self.remove_class(state.value)

        # Add current state class
        self.add_class(self._state.value)

        # Choose dot character
        if self._state == LivenessState.INIT:
            dot = "·"
        elif self._state == LivenessState.REFRESHING:
            dot = "◉"
        else:
            dot = "●"

        self.update(dot)

    @property
    def last_refresh(self) -> float:
        """Get the timestamp of last refresh."""
        return self._last_refresh

    @property
    def state(self) -> LivenessState:
        """Get the current liveness state."""
        return self._state
