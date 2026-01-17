# Iteration 9: CI Tab Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add GitHub Actions monitoring for repos using claude-code-action, with Overview integration and dedicated CI tab.

**Architecture:** Data layer fetches from GitHub API via `gh` CLI, caches discovered repos in settings file. UI shows summary on Overview tab, full details in new CI tab. Hidden repos stored in settings.

**Tech Stack:** Python, Textual, subprocess (gh CLI), JSON settings file

---

## Task 1: Settings Module

**Files:**
- Create: `src/cdash/data/settings.py`
- Test: `tests/test_settings.py`

**Step 1: Write failing test for settings load**

```python
# tests/test_settings.py
"""Tests for cdash settings management."""

from pathlib import Path
import json

import pytest

from cdash.data.settings import (
    CdashSettings,
    load_settings,
    save_settings,
    get_settings_path,
)


class TestLoadSettings:
    """Tests for loading settings."""

    def test_returns_defaults_when_file_missing(self, tmp_path: Path):
        """Returns default settings when file doesn't exist."""
        settings_path = tmp_path / "cdash-settings.json"
        result = load_settings(settings_path)
        assert result.discovered_repos == []
        assert result.hidden_repos == []

    def test_loads_existing_settings(self, tmp_path: Path):
        """Loads settings from existing file."""
        settings_path = tmp_path / "cdash-settings.json"
        settings_path.write_text(json.dumps({
            "github_actions": {
                "discovered_repos": ["owner/repo1", "owner/repo2"],
                "hidden_repos": ["owner/hidden"],
                "last_discovery": "2026-01-17T10:00:00Z"
            }
        }))
        result = load_settings(settings_path)
        assert result.discovered_repos == ["owner/repo1", "owner/repo2"]
        assert result.hidden_repos == ["owner/hidden"]


class TestSaveSettings:
    """Tests for saving settings."""

    def test_saves_settings_to_file(self, tmp_path: Path):
        """Saves settings to JSON file."""
        settings_path = tmp_path / "cdash-settings.json"
        settings = CdashSettings(
            discovered_repos=["owner/repo"],
            hidden_repos=["owner/hidden"],
            last_discovery="2026-01-17T12:00:00Z"
        )
        save_settings(settings, settings_path)

        data = json.loads(settings_path.read_text())
        assert data["github_actions"]["discovered_repos"] == ["owner/repo"]
        assert data["github_actions"]["hidden_repos"] == ["owner/hidden"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_settings.py -v`
Expected: FAIL with "No module named 'cdash.data.settings'"

**Step 3: Write implementation**

```python
# src/cdash/data/settings.py
"""Cdash settings management."""

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CdashSettings:
    """Settings for cdash application."""

    discovered_repos: list[str] = field(default_factory=list)
    hidden_repos: list[str] = field(default_factory=list)
    last_discovery: str | None = None


def get_settings_path() -> Path:
    """Get path to cdash settings file."""
    return Path.home() / ".claude" / "cdash-settings.json"


def load_settings(settings_path: Path | None = None) -> CdashSettings:
    """Load settings from file, returning defaults if missing."""
    if settings_path is None:
        settings_path = get_settings_path()

    if not settings_path.exists():
        return CdashSettings()

    try:
        with settings_path.open() as f:
            data = json.load(f)
        gh = data.get("github_actions", {})
        return CdashSettings(
            discovered_repos=gh.get("discovered_repos", []),
            hidden_repos=gh.get("hidden_repos", []),
            last_discovery=gh.get("last_discovery"),
        )
    except (json.JSONDecodeError, OSError):
        return CdashSettings()


def save_settings(settings: CdashSettings, settings_path: Path | None = None) -> None:
    """Save settings to file."""
    if settings_path is None:
        settings_path = get_settings_path()

    data = {
        "github_actions": {
            "discovered_repos": settings.discovered_repos,
            "hidden_repos": settings.hidden_repos,
            "last_discovery": settings.last_discovery,
        }
    }

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w") as f:
        json.dump(data, f, indent=2)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_settings.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/data/settings.py tests/test_settings.py
git commit -m "feat(data): add settings module for cdash config"
```

---

## Task 2: GitHub Data Models

**Files:**
- Create: `src/cdash/data/github.py`
- Test: `tests/test_github.py`

**Step 1: Write failing test for data models**

```python
# tests/test_github.py
"""Tests for GitHub Actions data fetching."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from cdash.data.github import (
    WorkflowRun,
    RepoStats,
    parse_workflow_run,
    calculate_repo_stats,
)


class TestWorkflowRun:
    """Tests for WorkflowRun dataclass."""

    def test_creates_workflow_run(self):
        """Creates WorkflowRun from data."""
        run = WorkflowRun(
            repo="owner/repo",
            run_id=12345,
            workflow_name="CI",
            status="completed",
            conclusion="success",
            trigger="pull_request",
            pr_number=42,
            title="Fix bug",
            created_at=datetime(2026, 1, 17, 10, 0, 0, tzinfo=timezone.utc),
            html_url="https://github.com/owner/repo/actions/runs/12345",
        )
        assert run.repo == "owner/repo"
        assert run.conclusion == "success"


class TestParseWorkflowRun:
    """Tests for parsing GitHub API response."""

    def test_parses_api_response(self):
        """Parses workflow run from API JSON."""
        api_data = {
            "id": 12345,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "event": "pull_request",
            "head_branch": "feature",
            "created_at": "2026-01-17T10:00:00Z",
            "html_url": "https://github.com/owner/repo/actions/runs/12345",
            "display_title": "Fix auth bug",
            "pull_requests": [{"number": 42}],
        }
        run = parse_workflow_run("owner/repo", api_data)
        assert run.run_id == 12345
        assert run.conclusion == "success"
        assert run.pr_number == 42
        assert run.title == "Fix auth bug"


class TestCalculateRepoStats:
    """Tests for calculating repo statistics."""

    def test_calculates_stats_from_runs(self):
        """Calculates success rate and counts from runs."""
        now = datetime.now(timezone.utc)
        runs = [
            WorkflowRun("o/r", 1, "CI", "completed", "success", "push", None, "t", now, ""),
            WorkflowRun("o/r", 2, "CI", "completed", "failure", "push", None, "t", now, ""),
            WorkflowRun("o/r", 3, "CI", "completed", "success", "push", None, "t", now, ""),
        ]
        stats = calculate_repo_stats("o/r", runs, hidden_repos=[])
        assert stats.runs_today == 3
        assert stats.success_rate == pytest.approx(0.667, rel=0.01)
        assert stats.is_hidden is False

    def test_marks_hidden_repos(self):
        """Marks repo as hidden when in hidden list."""
        stats = calculate_repo_stats("o/r", [], hidden_repos=["o/r"])
        assert stats.is_hidden is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_github.py -v`
Expected: FAIL with "No module named 'cdash.data.github'"

**Step 3: Write implementation**

```python
# src/cdash/data/github.py
"""GitHub Actions data fetching and parsing."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""

    repo: str
    run_id: int
    workflow_name: str
    status: str  # "queued", "in_progress", "completed"
    conclusion: str | None  # "success", "failure", "cancelled", etc.
    trigger: str  # "pull_request", "issue_comment", "push", etc.
    pr_number: int | None
    title: str
    created_at: datetime
    html_url: str

    @property
    def is_success(self) -> bool:
        """Check if run was successful."""
        return self.conclusion == "success"


@dataclass
class RepoStats:
    """Aggregated statistics for a repository."""

    repo: str
    runs_today: int
    runs_week: int
    success_rate: float  # 0.0 - 1.0
    last_run: WorkflowRun | None
    is_hidden: bool


def parse_workflow_run(repo: str, data: dict) -> WorkflowRun:
    """Parse a workflow run from GitHub API response."""
    pr_number = None
    if data.get("pull_requests"):
        pr_number = data["pull_requests"][0].get("number")

    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

    return WorkflowRun(
        repo=repo,
        run_id=data["id"],
        workflow_name=data.get("name", ""),
        status=data.get("status", ""),
        conclusion=data.get("conclusion"),
        trigger=data.get("event", ""),
        pr_number=pr_number,
        title=data.get("display_title", ""),
        created_at=created_at,
        html_url=data.get("html_url", ""),
    )


def calculate_repo_stats(
    repo: str,
    runs: list[WorkflowRun],
    hidden_repos: list[str],
) -> RepoStats:
    """Calculate statistics for a repository from its runs."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    runs_today = [r for r in runs if r.created_at >= today_start]
    runs_week = [r for r in runs if r.created_at >= week_ago]

    # Calculate success rate from completed runs this week
    completed = [r for r in runs_week if r.status == "completed" and r.conclusion]
    if completed:
        successes = sum(1 for r in completed if r.is_success)
        success_rate = successes / len(completed)
    else:
        success_rate = 0.0

    last_run = runs[0] if runs else None

    return RepoStats(
        repo=repo,
        runs_today=len(runs_today),
        runs_week=len(runs_week),
        success_rate=success_rate,
        last_run=last_run,
        is_hidden=repo in hidden_repos,
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_github.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/data/github.py tests/test_github.py
git commit -m "feat(data): add GitHub workflow run models and stats"
```

---

## Task 3: GitHub API Client

**Files:**
- Modify: `src/cdash/data/github.py`
- Test: `tests/test_github.py` (add tests)

**Step 1: Add failing test for gh CLI wrapper**

```python
# Add to tests/test_github.py

class TestGhApi:
    """Tests for GitHub API calls via gh CLI."""

    def test_gh_api_returns_json(self, mocker):
        """gh_api returns parsed JSON from gh CLI."""
        from cdash.data.github import gh_api

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.stdout = '{"login": "testuser"}'
        mock_run.return_value.returncode = 0

        result = gh_api("/user")
        assert result == {"login": "testuser"}
        mock_run.assert_called_once()

    def test_gh_api_returns_none_on_error(self, mocker):
        """gh_api returns None when gh CLI fails."""
        from cdash.data.github import gh_api

        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "error"

        result = gh_api("/user")
        assert result is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_github.py::TestGhApi -v`
Expected: FAIL with "cannot import name 'gh_api'"

**Step 3: Add gh_api implementation**

```python
# Add to src/cdash/data/github.py (at top after imports)

import json
import subprocess


def gh_api(endpoint: str, method: str = "GET") -> dict | list | None:
    """Call GitHub API via gh CLI.

    Args:
        endpoint: API endpoint (e.g., "/user/repos")
        method: HTTP method

    Returns:
        Parsed JSON response or None on error.
    """
    try:
        result = subprocess.run(
            ["gh", "api", endpoint, "-X", method],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_github.py::TestGhApi -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/data/github.py tests/test_github.py
git commit -m "feat(data): add gh CLI wrapper for GitHub API"
```

---

## Task 4: Repo Discovery

**Files:**
- Modify: `src/cdash/data/github.py`
- Test: `tests/test_github.py` (add tests)

**Step 1: Add failing test for discovery**

```python
# Add to tests/test_github.py

class TestDiscoverClaudeRepos:
    """Tests for discovering repos with claude-code-action."""

    def test_discovers_repo_with_claude_action(self, mocker):
        """Finds repo that uses claude-code-action."""
        from cdash.data.github import discover_claude_repos

        mock_gh = mocker.patch("cdash.data.github.gh_api")

        # Mock /user/repos
        mock_gh.side_effect = [
            [{"full_name": "owner/repo1"}, {"full_name": "owner/repo2"}],
            # workflows for repo1
            {"workflows": [{"path": ".github/workflows/ci.yml"}]},
            # workflow content for repo1 (has claude-code-action)
            {"content": "dXNlczogYW50aHJvcGljcy9jbGF1ZGUtY29kZS1hY3Rpb24="},  # base64
            # workflows for repo2
            {"workflows": [{"path": ".github/workflows/test.yml"}]},
            # workflow content for repo2 (no claude)
            {"content": "cnVuczogbnBtIHRlc3Q="},  # base64 "runs: npm test"
        ]

        repos = discover_claude_repos()
        assert repos == ["owner/repo1"]

    def test_returns_empty_when_no_claude_repos(self, mocker):
        """Returns empty list when no repos use claude-code-action."""
        from cdash.data.github import discover_claude_repos

        mock_gh = mocker.patch("cdash.data.github.gh_api")
        mock_gh.side_effect = [
            [{"full_name": "owner/repo"}],
            {"workflows": []},
        ]

        repos = discover_claude_repos()
        assert repos == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_github.py::TestDiscoverClaudeRepos -v`
Expected: FAIL with "cannot import name 'discover_claude_repos'"

**Step 3: Add discovery implementation**

```python
# Add to src/cdash/data/github.py

import base64


def discover_claude_repos() -> list[str]:
    """Discover repos that use claude-code-action.

    Scans all accessible repos for workflows containing claude-code-action.
    """
    repos = gh_api("/user/repos?per_page=100")
    if not repos:
        return []

    claude_repos = []

    for repo_data in repos:
        repo = repo_data.get("full_name", "")
        if not repo:
            continue

        if _repo_has_claude_action(repo):
            claude_repos.append(repo)

    return sorted(claude_repos)


def _repo_has_claude_action(repo: str) -> bool:
    """Check if a repo has any workflow using claude-code-action."""
    workflows = gh_api(f"/repos/{repo}/actions/workflows")
    if not workflows:
        return False

    for wf in workflows.get("workflows", []):
        path = wf.get("path", "")
        if not path:
            continue

        # Fetch workflow file content
        content_data = gh_api(f"/repos/{repo}/contents/{path}")
        if not content_data:
            continue

        # Decode base64 content
        try:
            content_b64 = content_data.get("content", "")
            content = base64.b64decode(content_b64).decode("utf-8")
        except Exception:
            continue

        # Check for claude-code-action
        if "claude-code-action" in content or "anthropics/claude-code" in content:
            return True

    return False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_github.py::TestDiscoverClaudeRepos -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/data/github.py tests/test_github.py
git commit -m "feat(data): add claude-code-action repo discovery"
```

---

## Task 5: Fetch Workflow Runs

**Files:**
- Modify: `src/cdash/data/github.py`
- Test: `tests/test_github.py` (add tests)

**Step 1: Add failing test for fetching runs**

```python
# Add to tests/test_github.py

class TestFetchWorkflowRuns:
    """Tests for fetching workflow runs."""

    def test_fetches_runs_for_repo(self, mocker):
        """Fetches and parses workflow runs from API."""
        from cdash.data.github import fetch_workflow_runs

        mock_gh = mocker.patch("cdash.data.github.gh_api")
        mock_gh.return_value = {
            "workflow_runs": [
                {
                    "id": 123,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "created_at": "2026-01-17T10:00:00Z",
                    "html_url": "https://github.com/o/r/actions/runs/123",
                    "display_title": "Update deps",
                    "pull_requests": [],
                }
            ]
        }

        runs = fetch_workflow_runs("owner/repo")
        assert len(runs) == 1
        assert runs[0].run_id == 123
        assert runs[0].is_success

    def test_returns_empty_on_api_error(self, mocker):
        """Returns empty list when API fails."""
        from cdash.data.github import fetch_workflow_runs

        mock_gh = mocker.patch("cdash.data.github.gh_api")
        mock_gh.return_value = None

        runs = fetch_workflow_runs("owner/repo")
        assert runs == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_github.py::TestFetchWorkflowRuns -v`
Expected: FAIL with "cannot import name 'fetch_workflow_runs'"

**Step 3: Add fetch implementation**

```python
# Add to src/cdash/data/github.py

from datetime import timedelta


def fetch_workflow_runs(repo: str, days: int = 7) -> list[WorkflowRun]:
    """Fetch recent workflow runs for a repository.

    Args:
        repo: Repository in "owner/repo" format
        days: Number of days of history to fetch

    Returns:
        List of WorkflowRun objects, newest first.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    data = gh_api(f"/repos/{repo}/actions/runs?per_page=50&created=>={since_str}")
    if not data:
        return []

    runs = []
    for run_data in data.get("workflow_runs", []):
        try:
            run = parse_workflow_run(repo, run_data)
            runs.append(run)
        except Exception:
            continue

    # Sort by created_at descending (newest first)
    runs.sort(key=lambda r: r.created_at, reverse=True)
    return runs
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_github.py::TestFetchWorkflowRuns -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/data/github.py tests/test_github.py
git commit -m "feat(data): add workflow runs fetching"
```

---

## Task 6: CI Activity Panel (Overview)

**Files:**
- Create: `src/cdash/components/ci.py`
- Test: `tests/test_ci.py`

**Step 1: Write failing test for CI panel**

```python
# tests/test_ci.py
"""Tests for CI components."""

from datetime import datetime, timezone

import pytest

from cdash.data.github import WorkflowRun, RepoStats


class TestCIActivityPanel:
    """Tests for CI activity panel on Overview tab."""

    def test_renders_summary_stats(self):
        """Renders today's run counts."""
        from cdash.components.ci import CIActivityPanel

        panel = CIActivityPanel()
        panel.update_stats(runs_today=15, passed=12, failed=3)

        rendered = panel.render()
        assert "15" in rendered
        assert "12" in rendered
        assert "3" in rendered

    def test_renders_top_repos(self):
        """Renders top repos by activity."""
        from cdash.components.ci import CIActivityPanel

        panel = CIActivityPanel()
        stats = [
            RepoStats("owner/repo1", 8, 40, 0.95, None, False),
            RepoStats("owner/repo2", 5, 20, 0.80, None, False),
        ]
        panel.update_repos(stats)

        rendered = panel.render()
        assert "repo1" in rendered
        assert "repo2" in rendered
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ci.py -v`
Expected: FAIL with "No module named 'cdash.components.ci'"

**Step 3: Write CI panel implementation**

```python
# src/cdash/components/ci.py
"""CI/GitHub Actions UI components."""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ci.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/components/ci.py tests/test_ci.py
git commit -m "feat(ui): add CI activity panel for Overview tab"
```

---

## Task 7: CI Tab Component

**Files:**
- Modify: `src/cdash/components/ci.py`
- Test: `tests/test_ci.py` (add tests)

**Step 1: Add failing test for CI tab**

```python
# Add to tests/test_ci.py

class TestCITab:
    """Tests for dedicated CI tab."""

    @pytest.mark.asyncio
    async def test_ci_tab_has_title(self):
        """CI tab has header."""
        from cdash.components.ci import CITab

        tab = CITab()
        # Just verify it composes without error
        assert tab is not None

    def test_repo_row_renders(self):
        """Repo row displays stats correctly."""
        from cdash.components.ci import RepoRow

        now = datetime.now(timezone.utc)
        last_run = WorkflowRun(
            "o/r", 1, "CI", "completed", "success", "push", None, "t", now, ""
        )
        stats = RepoStats("owner/repo", 8, 42, 0.95, last_run, False)
        row = RepoRow(stats)

        rendered = row.render()
        assert "owner/repo" in rendered or "repo" in rendered
        assert "8" in rendered
        assert "42" in rendered
        assert "95%" in rendered
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_ci.py::TestCITab -v`
Expected: FAIL with "cannot import name 'CITab'"

**Step 3: Add CI tab implementation**

```python
# Add to src/cdash/components/ci.py

from cdash.data.github import WorkflowRun


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string."""
    from datetime import timezone
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


class RepoRow(Static):
    """Single repository row in CI tab."""

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
        # Truncate repo name if needed
        repo = s.repo
        if len(repo) > 24:
            repo = repo[:21] + "..."

        # Format last run
        if s.last_run:
            last_time = format_relative_time(s.last_run.created_at)
            last_status = "✓" if s.last_run.is_success else "✗"
            last = f"{last_time} {last_status}"
        else:
            last = "-"

        success_pct = f"{int(s.success_rate * 100)}%"

        return f"{repo:<24} {s.runs_today:>5}  {s.runs_week:>6}  {success_pct:>7}   {last}"


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
    """

    def __init__(self) -> None:
        super().__init__()
        self._repo_stats: list[RepoStats] = []
        self._recent_runs: list[WorkflowRun] = []
        self._hidden_count = 0

    def compose(self) -> ComposeResult:
        yield Static("GITHUB ACTIONS (Claude Code)", classes="ci-title")
        yield Static(
            "REPO                     TODAY    WEEK  SUCCESS   LAST RUN",
            classes="ci-header-row"
        )
        yield Vertical(id="repo-list")
        yield Static("", classes="hidden-info", id="hidden-info")
        yield Static("RECENT RUNS", classes="runs-title")
        yield Vertical(id="runs-list")

    def on_mount(self) -> None:
        """Load data when mounted."""
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh CI data from GitHub."""
        # This will be called by the app's refresh loop
        pass

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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_ci.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/cdash/components/ci.py tests/test_ci.py
git commit -m "feat(ui): add CI tab with repo table and recent runs"
```

---

## Task 8: Integrate CI Tab into App

**Files:**
- Modify: `src/cdash/components/tabs.py`
- Modify: `src/cdash/app.py`
- Test: `tests/test_tabs.py` (add test)

**Step 1: Add failing test for CI tab in app**

```python
# Add to tests/test_tabs.py

@pytest.mark.asyncio
async def test_ci_tab_accessible_via_key_6():
    """Can switch to CI tab with key 6."""
    from cdash.app import ClaudeDashApp
    from cdash.components.ci import CITab

    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("6")
        ci_tab = app.query_one(CITab)
        assert ci_tab is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tabs.py::test_ci_tab_accessible_via_key_6 -v`
Expected: FAIL

**Step 3: Update tabs.py to add CI tab**

```python
# src/cdash/components/tabs.py
# Add import at top:
from cdash.components.ci import CITab

# In DashboardTabs.compose(), add after Agents tab:
            with TabPane("CI", id="tab-ci"):
                yield CITab()
```

**Step 4: Update app.py bindings**

```python
# src/cdash/app.py
# Add to BINDINGS:
        ("6", "switch_tab('tab-ci')", "CI"),
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_tabs.py::test_ci_tab_accessible_via_key_6 -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/cdash/components/tabs.py src/cdash/app.py tests/test_tabs.py
git commit -m "feat(ui): integrate CI tab into app navigation"
```

---

## Task 9: Add CI Panel to Overview Tab

**Files:**
- Modify: `src/cdash/components/tabs.py`
- Modify: `src/cdash/app.py`

**Step 1: Add CIActivityPanel to OverviewTab**

```python
# src/cdash/components/tabs.py
# Add import:
from cdash.components.ci import CIActivityPanel

# In OverviewTab.compose(), add after StatsPanel:
        yield CIActivityPanel()

# Update OverviewTab.refresh_data() to accept CI data:
    def refresh_data(
        self, msgs_today: int = 0, tools_today: int = 0, active_count: int = 0,
        ci_runs: int = 0, ci_passed: int = 0, ci_failed: int = 0,
        ci_repos: list | None = None,
    ) -> None:
        # ... existing code ...
        try:
            ci_panel = self.query_one(CIActivityPanel)
            ci_panel.update_stats(ci_runs, ci_passed, ci_failed)
            if ci_repos:
                ci_panel.update_repos(ci_repos)
        except Exception:
            pass
```

**Step 2: Update app.py to fetch CI data**

```python
# src/cdash/app.py
# Add imports:
from cdash.data.github import fetch_workflow_runs, calculate_repo_stats
from cdash.data.settings import load_settings

# In _refresh_data(), add CI data fetching:
        # Get CI data
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

        # Update overview with CI data
        overview_tab.refresh_data(
            msgs_today=msgs_today,
            tools_today=tools_today,
            active_count=active_count,
            ci_runs=ci_runs,
            ci_passed=ci_passed,
            ci_failed=ci_failed,
            ci_repos=ci_repos,
        )
```

**Step 3: Run all tests**

Run: `pytest tests/ -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/cdash/components/tabs.py src/cdash/app.py
git commit -m "feat(ui): add CI activity panel to Overview tab"
```

---

## Task 10: Add Hidden Repos Toggle

**Files:**
- Modify: `src/cdash/data/settings.py`
- Modify: `src/cdash/components/ci.py`

**Step 1: Add toggle function to settings**

```python
# Add to src/cdash/data/settings.py

def toggle_hidden_repo(repo: str, settings_path: Path | None = None) -> bool:
    """Toggle a repo's hidden status. Returns new hidden state."""
    settings = load_settings(settings_path)
    if repo in settings.hidden_repos:
        settings.hidden_repos.remove(repo)
        is_hidden = False
    else:
        settings.hidden_repos.append(repo)
        is_hidden = True
    save_settings(settings, settings_path)
    return is_hidden
```

**Step 2: Add keybinding for H in CITab**

The hidden repos modal is a stretch goal. For now, just add the keybinding stub.

```python
# CITab already has the structure - add action method
# This would show a modal, but for MVP just log

    BINDINGS = [
        ("h", "toggle_hidden", "Hide/Show repos"),
        ("r", "refresh", "Refresh"),
    ]

    def action_toggle_hidden(self) -> None:
        """Toggle hidden repos modal (future)."""
        self.notify("Hidden repos management coming soon")

    def action_refresh(self) -> None:
        """Force refresh data."""
        self.refresh_data()
```

**Step 3: Run tests**

Run: `pytest tests/ -v`
Expected: PASS

**Step 4: Commit**

```bash
git add src/cdash/data/settings.py src/cdash/components/ci.py
git commit -m "feat(ui): add hidden repo toggle stub and keybindings"
```

---

## Task 11: Update CLAUDE.md and Final Test

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 2: Update CLAUDE.md iteration status**

Change iteration 9 to complete, add to "What's Working" section.

**Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update state for iteration 9 complete"
```

---

## Files Summary

| File | Action |
|------|--------|
| `src/cdash/data/settings.py` | CREATE |
| `src/cdash/data/github.py` | CREATE |
| `src/cdash/components/ci.py` | CREATE |
| `src/cdash/components/tabs.py` | MODIFY (add CITab import, add to DashboardTabs) |
| `src/cdash/app.py` | MODIFY (add binding, add CI data fetch) |
| `tests/test_settings.py` | CREATE |
| `tests/test_github.py` | CREATE |
| `tests/test_ci.py` | CREATE |
| `tests/test_tabs.py` | MODIFY (add CI tab test) |
| `CLAUDE.md` | MODIFY (update iteration status) |

---

## Verification

After all tasks complete:

```bash
# Full test suite
pytest tests/ -v

# Visual verification
python -m cdash
# - Press 1 to see Overview with CI panel
# - Press 6 to see CI tab
# - Verify data displays (may be empty if no repos discovered)
```
