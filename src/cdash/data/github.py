"""GitHub Actions data fetching and parsing."""

import base64
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


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
