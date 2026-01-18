"""CI/GitHub Actions UI components."""

import subprocess
from datetime import datetime, timezone

from textual import work
from textual.app import ComposeResult
from textual.containers import Center, Horizontal, Vertical
from textual.widgets import LoadingIndicator, Static
from textual.worker import Worker

from cdash.components.indicators import RefreshIndicator
from cdash.data.github import (
    RepoStats,
    WorkflowRun,
    calculate_repo_stats,
    discover_claude_repos,
    fetch_workflow_runs,
)
from cdash.data.settings import CdashSettings, load_settings, save_settings
from cdash.theme import AMBER, CORAL, GREEN, RED


def format_total_duration(seconds: int) -> str:
    """Format total duration as human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    mins = seconds // 60
    if mins < 60:
        return f"{mins}m"
    hours = mins // 60
    remaining_mins = mins % 60
    if remaining_mins:
        return f"{hours}h{remaining_mins}m"
    return f"{hours}h"


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


class CIHeader(Horizontal):
    """Header with title and refresh indicator."""

    def compose(self) -> ComposeResult:
        yield Static("GITHUB (today)", classes="ci-header")
        yield Static("", classes="header-spacer")
        yield RefreshIndicator(id="ci-refresh")


class CIActivityPanel(Vertical):
    """Compact CI activity panel for Overview tab."""

    def __init__(self) -> None:
        super().__init__()
        self._runs_today = 0
        self._passed = 0
        self._failed = 0
        self._top_repos: list[RepoStats] = []

    def compose(self) -> ComposeResult:
        yield CIHeader()
        yield Static("", classes="ci-stats")
        yield Static("", classes="ci-repos")
        yield Static("[2: GitHub]", classes="ci-hint")

    def update_stats(self, runs_today: int, passed: int, failed: int) -> None:
        """Update summary statistics."""
        self._runs_today = runs_today
        self._passed = passed
        self._failed = failed
        self._refresh_display()
        # Mark refresh indicator
        try:
            indicator = self.query_one("#ci-refresh", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass

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
                f"[{CORAL}]{self._runs_today}[/] runs  "
                f"[{GREEN}]✓ {self._passed}[/] passed  "
                f"[{RED}]✗ {self._failed}[/] failed"
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
        return f"{self._runs_today} runs {self._passed} passed {self._failed} failed " + " ".join(
            s.repo for s in self._top_repos
        )


class RepoRow(Static):
    """Single repository row in CI tab."""

    # Fixed columns: TODAY(5) + WEEK(6) + SUCCESS(7) + LAST(12) + spacing(~10)
    FIXED_WIDTH = 40
    MIN_REPO_WIDTH = 20

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

        return (
            f"{repo:<{repo_width}} {s.runs_today:>5}  {s.runs_week:>6}  {success_pct:>7}   {last}"
        )


class RunRow(Static):
    """Single workflow run row."""

    def __init__(self, run: WorkflowRun, index: int = 0) -> None:
        super().__init__()
        self._run = run
        self._index = index

    def render(self) -> str:
        r = self._run
        status = f"[{GREEN}]✓[/]" if r.is_success else f"[{RED}]✗[/]"

        # Format trigger info
        if r.pr_number:
            trigger = f"PR #{r.pr_number}"
        else:
            trigger = r.trigger[:12]

        # Truncate title
        title = r.title
        if len(title) > 20:
            title = title[:17] + "..."

        time = format_relative_time(r.created_at)

        # Duration
        duration = r.duration_formatted or "-"

        # Failure reason badge for non-success
        failure_badge = ""
        if r.conclusion and r.conclusion != "success":
            failure_badge = f" [{RED}]{r.conclusion}[/]"

        repo_short = r.repo.split("/")[-1]
        return f'{status} {repo_short:<14} {trigger:<12} "{title}"  {duration:>5}  {time}{failure_badge}'


class CITab(Vertical):
    """Dedicated CI tab with full repo breakdown."""

    BINDINGS = [
        ("h", "toggle_hidden", "Hide/Show repos"),
        ("r", "refresh", "Refresh"),
        ("d", "discover", "Discover repos"),
        ("o", "open_run", "Open run in browser"),
        ("p", "open_pr", "Open PR in browser"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._repo_stats: list[RepoStats] = []
        self._recent_runs: list[WorkflowRun] = []
        self._hidden_count = 0
        self._loading = False
        self._discovered = False
        # Aggregate stats
        self._runs_today = 0
        self._passed_today = 0
        self._total_duration_today = 0
        self._selected_run_index = 0

    def compose(self) -> ComposeResult:
        yield Static("GITHUB ACTIONS (Claude Code)", classes="ci-title")
        yield Static("", classes="ci-aggregate-stats", id="aggregate-stats")
        yield Center(LoadingIndicator(), id="loading-container")
        yield Static("", classes="ci-header-row", id="header-row")
        yield Vertical(id="repo-list")
        yield Static("", classes="hidden-info", id="hidden-info")
        yield Static("RECENT RUNS  [dim](o: open run, p: open PR)[/dim]", classes="runs-title")
        yield Vertical(id="runs-list")
        yield Static("", classes="status-msg", id="status-msg")

    def on_mount(self) -> None:
        """Load data when mounted."""
        self._update_header()
        self._show_loading(True)
        # Check if we have discovered repos
        settings = load_settings()
        if not settings.discovered_repos:
            self._show_status("Discovering repos...")
            self._run_discovery()
        else:
            self._show_status("Loading CI data...")
            self._load_runs_for_repos(settings)

    def on_resize(self) -> None:
        """Update header and rows on resize."""
        self._update_header()
        self._refresh_display()

    def _update_header(self) -> None:
        """Update header row to match current width."""
        try:
            header = self.query_one("#header-row", Static)
            available = self.size.width - RepoRow.FIXED_WIDTH - 4  # account for padding
            repo_width = max(RepoRow.MIN_REPO_WIDTH, available)
            header.update(
                f"{'REPO':<{repo_width}} {'TODAY':>5}  {'WEEK':>6}  {'SUCCESS':>7}   LAST RUN"
            )
        except Exception:
            pass

    def _show_status(self, msg: str) -> None:
        """Show a status message."""
        try:
            status = self.query_one("#status-msg", Static)
            status.update(msg)
        except Exception:
            pass

    def _show_loading(self, show: bool) -> None:
        """Show or hide the loading indicator."""
        try:
            loading = self.query_one("#loading-container", Center)
            loading.display = show
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
                self._show_status(f"Found {len(repos)} repos. Loading...")
                settings = load_settings()
                self._load_runs_for_repos(settings)
            else:
                self._show_loading(False)
                self._show_status("No repos found with claude-code-action")
        elif event.worker.name == "_fetch_all_runs" and event.worker.is_finished:
            self._show_loading(False)
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
        # Calculate aggregate stats for today
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_runs = [r for r in self._recent_runs if r.created_at >= today_start]
        self._runs_today = len(today_runs)
        self._passed_today = sum(1 for r in today_runs if r.is_success)
        self._total_duration_today = sum(
            r.duration_seconds or 0 for r in today_runs if r.status == "completed"
        )

        # Update aggregate stats display
        try:
            agg_stats = self.query_one("#aggregate-stats", Static)
            if self._runs_today > 0:
                pass_rate = int(self._passed_today / self._runs_today * 100)
                duration_str = format_total_duration(self._total_duration_today)
                agg_stats.update(
                    f"TODAY: [{CORAL}]{self._runs_today}[/] runs | "
                    f"[{AMBER}]{duration_str}[/] total | "
                    f"[{GREEN}]{pass_rate}%[/] pass"
                )
            else:
                agg_stats.update("[dim]No runs today[/dim]")
        except Exception:
            pass

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
                hidden_info.update(f"── Hidden: {self._hidden_count} repos (press H to manage) ──")
            else:
                hidden_info.update("")
        except Exception:
            pass

        # Update runs list
        try:
            runs_list = self.query_one("#runs-list", Vertical)
            runs_list.remove_children()

            for idx, run in enumerate(self._recent_runs[:8]):  # Show last 8 runs
                runs_list.mount(RunRow(run, index=idx))
        except Exception:
            pass

    def action_toggle_hidden(self) -> None:
        """Toggle hidden repos modal (future)."""
        self.notify("Hidden repos management coming soon")

    def action_refresh(self) -> None:
        """Force refresh data."""
        self.refresh_data()

    def action_open_run(self) -> None:
        """Open the most recent run in browser."""
        if self._recent_runs:
            run = self._recent_runs[0]
            if run.html_url:
                subprocess.run(["open", run.html_url], check=False)
                self.notify(f"Opening run: {run.title[:30]}")
            else:
                self.notify("No URL available for this run")
        else:
            self.notify("No runs to open")

    def action_open_pr(self) -> None:
        """Open the PR associated with the most recent run."""
        if self._recent_runs:
            run = self._recent_runs[0]
            if run.pr_number:
                # Construct PR URL from repo and PR number
                pr_url = f"https://github.com/{run.repo}/pull/{run.pr_number}"
                subprocess.run(["open", pr_url], check=False)
                self.notify(f"Opening PR #{run.pr_number}")
            else:
                self.notify("Most recent run has no associated PR")
        else:
            self.notify("No runs available")
