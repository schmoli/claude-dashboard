"""CI/GitHub Actions UI components."""

from datetime import datetime, timezone

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static
from textual.worker import Worker

from cdash.data.github import (
    RepoStats,
    WorkflowRun,
    calculate_repo_stats,
    discover_claude_repos,
    fetch_workflow_runs,
)
from cdash.data.settings import CdashSettings, load_settings, save_settings


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string."""
    now = datetime.now(timezone.utc)
    diff = now - dt

    minutes = int(diff.total_seconds() / 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


class CIActivityPanel(Vertical):
    """Compact CI activity panel for Overview tab."""

    DEFAULT_CSS = """
    CIActivityPanel {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }

    CIActivityPanel > .ci-header {
        text-style: bold;
    }

    CIActivityPanel > .ci-stats {
        height: 1;
    }

    CIActivityPanel > .ci-repos {
        height: auto;
        max-height: 3;
        padding-left: 2;
        color: $text-muted;
    }

    CIActivityPanel > .ci-hint {
        color: $text-muted;
        text-align: right;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._runs_today = 0
        self._passed = 0
        self._failed = 0
        self._top_repos: list[RepoStats] = []

    def compose(self) -> ComposeResult:
        yield Static("CI ACTIVITY (today)", classes="ci-header")
        yield Static("", classes="ci-stats")
        yield Static("", classes="ci-repos")
        yield Static("[6: CI tab]", classes="ci-hint")

    def update_stats(self, runs_today: int, passed: int, failed: int) -> None:
        """Update summary statistics."""
        self._runs_today = runs_today
        self._passed = passed
        self._failed = failed
        self._refresh_display()

    def update_repos(self, stats: list[RepoStats]) -> None:
        """Update top repos list."""
        # Show top 2 repos by runs_today
        visible = [s for s in stats if not s.is_hidden]
        self._top_repos = sorted(visible, key=lambda s: s.runs_today, reverse=True)[:2]
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the display."""
        try:
            stats_widget = self.query_one(".ci-stats", Static)
            stats_widget.update(
                f"[cyan]{self._runs_today}[/] runs  "
                f"[green]✓ {self._passed}[/] passed  "
                f"[red]✗ {self._failed}[/] failed"
            )
        except Exception:
            pass

        try:
            repos_widget = self.query_one(".ci-repos", Static)
            if self._top_repos:
                lines = []
                for s in self._top_repos:
                    name = s.repo.split("/")[-1]  # Just repo name
                    passed = int(s.runs_today * s.success_rate)
                    failed = s.runs_today - passed
                    lines.append(f"{name}: {s.runs_today} runs ({passed}✓ {failed}✗)")
                repos_widget.update("\n".join(lines))
            else:
                repos_widget.update("[dim]No CI activity[/]")
        except Exception:
            pass

    def render(self) -> str:
        """Render for testing purposes."""
        return (
            f"{self._runs_today} runs {self._passed} passed {self._failed} failed "
            + " ".join(s.repo for s in self._top_repos)
        )


class RepoRow(Static):
    """Single repository row in CI tab."""

    # Fixed columns: TODAY(5) + WEEK(6) + SUCCESS(7) + LAST(12) + spacing(~10)
    FIXED_WIDTH = 40
    MIN_REPO_WIDTH = 20

    DEFAULT_CSS = """
    RepoRow {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, stats: RepoStats) -> None:
        super().__init__()
        self._stats = stats

    def render(self) -> str:
        s = self._stats

        # Calculate available width for repo name
        try:
            available = self.size.width - self.FIXED_WIDTH
            repo_width = max(self.MIN_REPO_WIDTH, available)
        except Exception:
            repo_width = 32  # fallback

        repo = s.repo
        if len(repo) > repo_width:
            repo = repo[: repo_width - 3] + "..."

        # Format last run
        if s.last_run:
            last_time = format_relative_time(s.last_run.created_at)
            last_status = "✓" if s.last_run.is_success else "✗"
            last = f"{last_time} {last_status}"
        else:
            last = "-"

        success_pct = f"{int(s.success_rate * 100)}%"

        return f"{repo:<{repo_width}} {s.runs_today:>5}  {s.runs_week:>6}  {success_pct:>7}   {last}"


class RunRow(Static):
    """Single workflow run row."""

    DEFAULT_CSS = """
    RunRow {
        height: 1;
        padding: 0 1;
    }
    """

    def __init__(self, run: WorkflowRun) -> None:
        super().__init__()
        self._run = run

    def render(self) -> str:
        r = self._run
        status = "[green]✓[/]" if r.is_success else "[red]✗[/]"

        # Format trigger info
        if r.pr_number:
            trigger = f"PR #{r.pr_number}"
        else:
            trigger = r.trigger[:12]

        # Truncate title
        title = r.title
        if len(title) > 25:
            title = title[:22] + "..."

        time = format_relative_time(r.created_at)

        repo_short = r.repo.split("/")[-1]
        return f'{status} {repo_short:<16} {trigger:<12} "{title}"  {time}'


class CITab(Vertical):
    """Dedicated CI tab with full repo breakdown."""

    DEFAULT_CSS = """
    CITab {
        height: auto;
        padding: 1;
    }

    CITab > .ci-title {
        text-style: bold;
        margin-bottom: 1;
    }

    CITab > .ci-header-row {
        color: $text-muted;
        padding: 0 1;
        margin-bottom: 0;
    }

    CITab > #repo-list {
        height: auto;
        max-height: 10;
        margin-bottom: 1;
    }

    CITab > .hidden-info {
        color: $text-muted;
        text-style: italic;
        padding: 0 1;
    }

    CITab > .runs-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    CITab > #runs-list {
        height: auto;
        max-height: 8;
    }

    CITab > #loading-container {
        height: 3;
        align: center middle;
    }

    CITab > .status-msg {
        color: $text-muted;
        text-style: italic;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("h", "toggle_hidden", "Hide/Show repos"),
        ("r", "refresh", "Refresh"),
        ("d", "discover", "Discover repos"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._repo_stats: list[RepoStats] = []
        self._recent_runs: list[WorkflowRun] = []
        self._hidden_count = 0
        self._loading = False
        self._discovered = False

    def compose(self) -> ComposeResult:
        yield Static("GITHUB ACTIONS (Claude Code)", classes="ci-title")
        yield Static("", classes="ci-header-row", id="header-row")
        yield Vertical(id="repo-list")
        yield Static("", classes="hidden-info", id="hidden-info")
        yield Static("RECENT RUNS", classes="runs-title")
        yield Vertical(id="runs-list")
        yield Static("", classes="status-msg", id="status-msg")

    def on_mount(self) -> None:
        """Load data when mounted."""
        # Check if we have discovered repos
        settings = load_settings()
        if not settings.discovered_repos:
            self._show_status("Discovering repos with claude-code-action...")
            self._run_discovery()
        else:
            self._load_runs_for_repos(settings)

    def _show_status(self, msg: str) -> None:
        """Show a status message."""
        try:
            status = self.query_one("#status-msg", Static)
            status.update(msg)
        except Exception:
            pass

    @work(thread=True)
    def _run_discovery(self) -> list[str]:
        """Discover repos in background thread."""
        repos = discover_claude_repos()
        if repos:
            settings = CdashSettings(discovered_repos=repos)
            save_settings(settings)
        return repos

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker completion."""
        if event.worker.name == "_run_discovery" and event.worker.is_finished:
            repos = event.worker.result
            if repos:
                self._show_status(f"Found {len(repos)} repos. Loading runs...")
                settings = load_settings()
                self._load_runs_for_repos(settings)
            else:
                self._show_status("No repos found with claude-code-action")
        elif event.worker.name == "_fetch_all_runs" and event.worker.is_finished:
            self._show_status("")
            self._refresh_display()

    @work(thread=True)
    def _fetch_all_runs(self, repos: list[str], hidden: list[str]) -> None:
        """Fetch runs for all repos in background."""
        all_runs = []
        repo_stats = []
        for repo in repos:
            runs = fetch_workflow_runs(repo, days=7)
            all_runs.extend(runs)
            stats = calculate_repo_stats(repo, runs, hidden)
            repo_stats.append(stats)
        # Sort runs by date
        all_runs.sort(key=lambda r: r.created_at, reverse=True)
        self._repo_stats = repo_stats
        self._recent_runs = all_runs
        self._hidden_count = sum(1 for s in repo_stats if s.is_hidden)

    def _load_runs_for_repos(self, settings: CdashSettings) -> None:
        """Start loading runs for discovered repos."""
        self._fetch_all_runs(settings.discovered_repos, settings.hidden_repos)

    def refresh_data(self) -> None:
        """Refresh CI data from GitHub."""
        settings = load_settings()
        if settings.discovered_repos:
            self._show_status("Refreshing...")
            self._load_runs_for_repos(settings)

    def action_discover(self) -> None:
        """Re-run repo discovery."""
        self._show_status("Discovering repos...")
        self._run_discovery()

    def update_data(
        self,
        repo_stats: list[RepoStats],
        recent_runs: list[WorkflowRun],
    ) -> None:
        """Update the display with new data."""
        self._repo_stats = repo_stats
        self._recent_runs = recent_runs
        self._hidden_count = sum(1 for s in repo_stats if s.is_hidden)
        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the UI."""
        # Update repo list
        try:
            repo_list = self.query_one("#repo-list", Vertical)
            repo_list.remove_children()

            visible = [s for s in self._repo_stats if not s.is_hidden]
            # Sort by runs_today desc, then runs_week desc
            visible.sort(key=lambda s: (s.runs_today, s.runs_week), reverse=True)

            for stats in visible:
                repo_list.mount(RepoRow(stats))
        except Exception:
            pass

        # Update hidden count
        try:
            hidden_info = self.query_one("#hidden-info", Static)
            if self._hidden_count > 0:
                hidden_info.update(
                    f"── Hidden: {self._hidden_count} repos (press H to manage) ──"
                )
            else:
                hidden_info.update("")
        except Exception:
            pass

        # Update runs list
        try:
            runs_list = self.query_one("#runs-list", Vertical)
            runs_list.remove_children()

            for run in self._recent_runs[:8]:  # Show last 8 runs
                runs_list.mount(RunRow(run))
        except Exception:
            pass

    def action_toggle_hidden(self) -> None:
        """Toggle hidden repos modal (future)."""
        self.notify("Hidden repos management coming soon")

    def action_refresh(self) -> None:
        """Force refresh data."""
        self.refresh_data()
