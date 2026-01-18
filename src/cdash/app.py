"""Main Textual application for Claude Dashboard."""

import time
from pathlib import Path

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Static

from cdash.components.indicators import RefreshIndicator
from cdash.components.tabs import DashboardTabs, OverviewTab
from cdash.data.code_watcher import check_code_changes, get_repo_root, relaunch_app
from cdash.data.github import RepoStats, calculate_repo_stats, fetch_workflow_runs
from cdash.data.resources import get_resource_stats
from cdash.data.sessions import get_active_sessions
from cdash.data.settings import load_settings
from cdash.data.stats import load_stats_cache
from cdash.theme import AMBER, BLUE, CORAL, GREEN, TEXT_MUTED, create_claude_theme


class StatusBar(Horizontal):
    """Compact status bar - single source of all dashboard stats.

    Layout: claude-dash │ 3 active │ 42m 128t │ 15%cpu 1.2GB 8pr ● │ ⟳ changed(r)
    """

    def __init__(self) -> None:
        super().__init__()
        self._active_count = 0
        self._msgs = 0
        self._tools = 0
        self._cpu = 0.0
        self._mem_mb = 0.0
        self._proc_count = 0

    def compose(self) -> ComposeResult:
        yield Static("claude-dash", id="app-name")
        yield Static("", id="active-count")
        yield Static("", id="today-stats")
        yield Static("", id="host-stats")
        yield RefreshIndicator(id="status-refresh")
        yield Static("", id="code-changed")

    def update_stats(
        self,
        active_count: int,
        msgs_today: int = 0,
        tools_today: int = 0,
    ) -> None:
        """Update session and activity stats."""
        self._active_count = active_count
        self._msgs = msgs_today
        self._tools = tools_today

        try:
            count_widget = self.query_one("#active-count", Static)
            stats_widget = self.query_one("#today-stats", Static)

            if active_count > 0:
                count_widget.update(f"│ [{GREEN}]{active_count}[/] active")
            else:
                count_widget.update(f"│ [{TEXT_MUTED}]0 active[/]")

            stats_widget.update(f"│ [{CORAL}]{msgs_today}[/]m [{CORAL}]{tools_today}[/]t")
        except Exception:
            pass

    def update_host_stats(self) -> None:
        """Refresh host resource stats from psutil."""
        stats = get_resource_stats()
        self._cpu = stats.cpu_percent
        self._mem_mb = stats.memory_mb
        self._proc_count = stats.process_count

        try:
            host_widget = self.query_one("#host-stats", Static)

            # CPU
            cpu_display = min(self._cpu, 999)
            # Memory
            if self._mem_mb >= 1024:
                mem_display = f"{self._mem_mb / 1024:.1f}G"
            else:
                mem_display = f"{self._mem_mb:.0f}M"

            txt = f"│ [{CORAL}]{cpu_display:.0f}%[/] [{CORAL}]{mem_display}[/]"
            txt += f" [{BLUE}]{self._proc_count}[/]pr"
            host_widget.update(txt)
        except Exception:
            pass

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed."""
        try:
            indicator = self.query_one("#status-refresh", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass

    def show_code_changed(self, changed: bool, file_count: int = 0) -> None:
        """Show/hide the code changed indicator."""
        try:
            widget = self.query_one("#code-changed", Static)
            if changed:
                widget.update(f"│ [{AMBER}]⟳{file_count}f(r)[/]")
            else:
                widget.update("")
        except Exception:
            pass


class ClaudeDashApp(App):
    """Claude Code monitoring dashboard."""

    TITLE = "claude-dash"
    CSS_PATH = Path(__file__).parent / "app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "relaunch", "Reload"),
        ("s", "toggle_stats", "Stats"),
        ("1", "switch_tab('tab-overview')", "Overview"),
        ("2", "switch_tab('tab-github')", "GitHub"),
        ("3", "switch_tab('tab-plugins')", "Plugins"),
        ("4", "switch_tab('tab-mcp')", "MCP"),
    ]

    # Refresh interval in seconds
    REFRESH_INTERVAL = 3.0  # Fast refresh for live feel

    def __init__(self) -> None:
        super().__init__()
        self._start_time = time.time()
        self._repo_root = get_repo_root()
        self._code_changed = False

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
        status_bar.update_host_stats()
        status_bar.mark_refreshed()

        # Check for code changes
        change_status = check_code_changes(self._start_time, self._repo_root)
        self._code_changed = change_status.has_changes
        status_bar.show_code_changed(change_status.has_changes, len(change_status.changed_files))

        # Update overview tab (sessions only now - stats moved to StatusBar)
        try:
            overview_tab = self.query_one(OverviewTab)
            overview_tab.refresh_data()
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

    def action_toggle_stats(self) -> None:
        """Toggle the stats collapsible panel."""
        from textual.widgets import Collapsible

        try:
            collapsible = self.query_one("#stats-collapsible", Collapsible)
            collapsible.collapsed = not collapsible.collapsed
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
