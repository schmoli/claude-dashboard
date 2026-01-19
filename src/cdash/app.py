"""Main Textual application for Claude Dashboard.

k9s-style unified dashboard with sessions as focal point.
"""

import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer

from cdash.components.ci import CITab
from cdash.components.header import HeaderPanel
from cdash.components.mcp import MCPServersTab
from cdash.components.plugins import PluginsTab
from cdash.components.sessions import SessionsPanel
from cdash.data.code_watcher import check_code_changes, get_repo_root, relaunch_app
from cdash.data.sessions import get_active_sessions
from cdash.data.stats import load_stats_cache
from cdash.theme import create_claude_theme


# View configuration: key -> (id, display name, panel class)
VIEWS = {
    "1": ("overview", "overview", SessionsPanel),
    "2": ("github", "github", CITab),
    "3": ("plugins", "plugins", PluginsTab),
    "4": ("mcp", "mcp", MCPServersTab),
}


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
        ("1", "view_1", "Overview"),
        ("2", "view_2", "GitHub"),
        ("3", "view_3", "Plugins"),
        ("4", "view_4", "MCP"),
    ]

    # Refresh interval in seconds
    REFRESH_INTERVAL = 3.0  # Fast refresh for live feel

    def __init__(self) -> None:
        super().__init__()
        self._start_time = time.time()
        self._repo_root = get_repo_root()
        self._code_changed = False
        self._current_view = "1"  # Default to overview

    def compose(self) -> ComposeResult:
        yield HeaderPanel()
        # Content container with all view panels
        with Container(id="content"):
            yield SessionsPanel(id="view-overview")
            yield CITab(id="view-github")
            yield PluginsTab(id="view-plugins")
            yield MCPServersTab(id="view-mcp")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the refresh timer when the app mounts."""
        # Register and activate the Claude theme
        self.register_theme(create_claude_theme())
        self.theme = "claude"

        # Initialize view visibility (show only overview by default)
        self._switch_to_view("1")

        # Defer first refresh slightly to allow UI to render
        self.set_timer(0.1, self._refresh_data)
        self.set_interval(self.REFRESH_INTERVAL, self._refresh_data)

    def _refresh_data(self) -> None:
        """Refresh all data displays."""
        # Update active session count and today's stats in header
        active_sessions = get_active_sessions()
        try:
            header = self.query_one(HeaderPanel)
        except Exception:
            # HeaderPanel not yet mounted (app still initializing)
            return

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

        # Refresh only the active view's panel
        self._refresh_current_view()

    def _refresh_current_view(self) -> None:
        """Refresh data for the currently active view."""
        view_id = VIEWS[self._current_view][0]
        try:
            if view_id == "overview":
                panel = self.query_one("#view-overview", SessionsPanel)
                panel.refresh_sessions()
            elif view_id == "plugins":
                panel = self.query_one("#view-plugins", PluginsTab)
                panel.refresh_plugins()
            elif view_id == "mcp":
                panel = self.query_one("#view-mcp", MCPServersTab)
                panel.refresh_servers()
            elif view_id == "github":
                panel = self.query_one("#view-github", CITab)
                panel.refresh_data()
        except Exception:
            pass

    def _switch_to_view(self, key: str) -> None:
        """Switch to the specified view."""
        if key not in VIEWS:
            return

        self._current_view = key
        view_id, view_name, _ = VIEWS[key]

        # Hide all panels, show only the selected one
        for k, (vid, _, _) in VIEWS.items():
            try:
                panel = self.query_one(f"#view-{vid}")
                panel.display = (k == key)
            except Exception:
                pass

        # Update header navigation highlighting
        try:
            header = self.query_one(HeaderPanel)
            header.set_current_view(key)
        except Exception:
            pass

        # Refresh the newly visible panel
        self._refresh_current_view()

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)

    async def action_relaunch(self) -> None:
        """Relaunch the application to pick up code changes."""
        # Exit cleanly then relaunch
        self.exit(0)
        relaunch_app()

    def action_view_1(self) -> None:
        """Switch to Overview view."""
        self._switch_to_view("1")

    def action_view_2(self) -> None:
        """Switch to GitHub view."""
        self._switch_to_view("2")

    def action_view_3(self) -> None:
        """Switch to Plugins view."""
        self._switch_to_view("3")

    def action_view_4(self) -> None:
        """Switch to MCP Servers view."""
        self._switch_to_view("4")
