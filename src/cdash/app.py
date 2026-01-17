"""Main Textual application for Claude Dashboard."""

from textual.app import App, ComposeResult
from textual.widgets import Footer, Static

from cdash.components.tabs import DashboardTabs, OverviewTab
from cdash.data.github import fetch_workflow_runs, calculate_repo_stats
from cdash.data.sessions import get_active_sessions
from cdash.data.settings import load_settings
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

        # Get CI data (if repos are configured)
        ci_runs, ci_passed, ci_failed = 0, 0, 0
        ci_repos = []
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

        # Refresh the overview tab data with stats for header
        try:
            overview_tab = self.query_one(OverviewTab)
            overview_tab.refresh_data(
                msgs_today=msgs_today,
                tools_today=tools_today,
                active_count=active_count,
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

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit(0)
