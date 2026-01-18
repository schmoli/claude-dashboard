"""Main Textual application for Claude Dashboard.

k9s-style unified dashboard with sessions as focal point.
"""

import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer

from cdash.components.header import HeaderPanel
from cdash.components.sessions import SessionsPanel
from cdash.data.code_watcher import check_code_changes, get_repo_root, relaunch_app
from cdash.data.sessions import get_active_sessions
from cdash.data.stats import load_stats_cache
from cdash.theme import create_claude_theme


class ClaudeDashApp(App):
    """Claude Code monitoring dashboard - k9s style.

    Unified layout:
    ┌─────────────────────────────────────────────────────────────────┐
    │ claude-dash │ 3 active │ 42m/128t │ 15% 1.2G 8pr ●              │ <- Header
    ├─────────────────────────────────────────────────────────────────┤
    │              ── sessions(active)[3] ──                          │ <- Title
    │ NAME              STATUS   DUR    STATS  TOOL     PROMPT        │ <- Table
    │ cdash@main        ● ACT    5m     12/48  ⚙Read    "fix the..."  │
    │ api@feat-auth     ● ACT    12m    45/156 ⚙Bash    "implement... │
    ├─────────────────────────────────────────────────────────────────┤
    │ q Quit  r Reload  s Stats                                       │ <- Footer
    └─────────────────────────────────────────────────────────────────┘
    """

    TITLE = "claude-dash"
    CSS_PATH = Path(__file__).parent / "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "relaunch", "Reload"),
    ]

    # Refresh interval in seconds
    REFRESH_INTERVAL = 3.0  # Fast refresh for live feel

    def __init__(self) -> None:
        super().__init__()
        self._start_time = time.time()
        self._repo_root = get_repo_root()
        self._code_changed = False

    def compose(self) -> ComposeResult:
        yield HeaderPanel()
        yield SessionsPanel()
        yield Footer()

    def on_mount(self) -> None:
        """Set up the refresh timer when the app mounts."""
        # Register and activate the Claude theme
        self.register_theme(create_claude_theme())
        self.theme = "claude"

        # Defer first refresh slightly to allow UI to render
        self.set_timer(0.1, self._refresh_data)
        self.set_interval(self.REFRESH_INTERVAL, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh all data displays."""
        # Update active session count and today's stats in header
        active_sessions = get_active_sessions()
        header = self.query_one(HeaderPanel)

        # Get today's stats
        msgs_today = 0
        tools_today = 0
        stats_cache = load_stats_cache()
        if stats_cache:
            today = stats_cache.get_today()
            if today:
                msgs_today = today.message_count
                tools_today = today.tool_call_count

        active_count = len(active_sessions)
        header.update_stats(active_count, msgs_today, tools_today)
        header.update_host_stats()
        header.mark_refreshed()

        # Check for code changes
        change_status = check_code_changes(self._start_time, self._repo_root)
        self._code_changed = change_status.has_changes
        header.show_code_changed(change_status.has_changes, len(change_status.changed_files))

        # Update sessions panel
        try:
            sessions_panel = self.query_one(SessionsPanel)
            sessions_panel.refresh_sessions()
        except Exception:
            pass

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)

    async def action_relaunch(self) -> None:
        """Relaunch the application to pick up code changes."""
        # Exit cleanly then relaunch
        self.exit(0)
        relaunch_app()
