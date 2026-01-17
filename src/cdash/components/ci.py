"""CI/GitHub Actions UI components."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.github import RepoStats


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
