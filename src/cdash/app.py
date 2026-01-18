"""Main Textual application for Claude Dashboard."""

from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Static

from cdash.components.tabs import DashboardTabs, OverviewTab
from cdash.data.github import RepoStats, calculate_repo_stats, fetch_workflow_runs
from cdash.data.sessions import get_active_sessions
from cdash.data.settings import load_settings
from cdash.data.stats import load_stats_cache
from cdash.theme import GREEN, create_claude_theme


class StatusBar(Horizontal):
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
            count_widget.update(f"│ [{GREEN}]{active_count}[/] active")
        else:
            count_widget.update("")

        if msgs_today > 0 or tools_today > 0:
            stats_widget.update(f"│ {msgs_today} msgs │ {tools_today} tools")
        else:
            stats_widget.update("")


class ClaudeDashApp(App):
    """Claude Code monitoring dashboard."""

    TITLE = "claude-dash"
    CSS_PATH = Path(__file__).parent / "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "switch_tab('tab-overview')", "Overview"),
        ("2", "switch_tab('tab-plugins')", "Plugins"),
        ("3", "switch_tab('tab-mcp')", "MCP"),
        ("4", "switch_tab('tab-skills')", "Skills"),
        ("5", "switch_tab('tab-agents')", "Agents"),
        ("6", "switch_tab('tab-ci')", "CI"),
    ]

    # Refresh interval in seconds
    REFRESH_INTERVAL = 3.0  # Fast refresh for live feel

    def compose(self) -> ComposeResult:
        yield StatusBar()
        yield DashboardTabs(id="main-content")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the refresh timer when the app mounts."""
        # Register and activate the Claude theme
        self.register_theme(create_claude_theme())
        self.theme = "claude"

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

        active_count = len(active_sessions)
        status_bar.update_stats(active_count, msgs_today, tools_today)

        # Update overview with local stats (CI fetched async)
        try:
            overview_tab = self.query_one(OverviewTab)
            overview_tab.refresh_data(
                msgs_today=msgs_today,
                tools_today=tools_today,
                active_count=active_count,
            )
        except Exception:
            pass

        # Fetch CI data in background
        self._fetch_ci_data_async()

    @work(thread=True, exclusive=True, name="ci_refresh")
    def _fetch_ci_data_async(self) -> None:
        """Fetch CI data in background thread."""
        ci_runs, ci_passed, ci_failed = 0, 0, 0
        ci_repos: list[RepoStats] = []
        try:
            settings = load_settings()
            for repo in settings.discovered_repos:
                if repo not in settings.hidden_repos:
                    runs = fetch_workflow_runs(repo, days=1)
                    stats = calculate_repo_stats(repo, runs, settings.hidden_repos)
                    ci_repos.append(stats)
                    ci_runs += stats.runs_today
                    ci_passed += sum(1 for r in runs if r.is_success)
                    ci_failed += len(runs) - sum(1 for r in runs if r.is_success)
        except Exception:
            pass

        # Update UI from main thread
        self.call_from_thread(self._update_ci_display, ci_runs, ci_passed, ci_failed, ci_repos)

    def _update_ci_display(
        self,
        ci_runs: int,
        ci_passed: int,
        ci_failed: int,
        ci_repos: list[RepoStats],
    ) -> None:
        """Update CI display on main thread."""
        try:
            overview_tab = self.query_one(OverviewTab)
            overview_tab.update_ci(
                ci_runs=ci_runs,
                ci_passed=ci_passed,
                ci_failed=ci_failed,
                ci_repos=ci_repos,
            )
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        tabs = self.query_one(DashboardTabs)
        tabs.active = tab_id

    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)
