"""Tests for GitHub Actions data fetching."""

from datetime import datetime, timezone

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


class TestGhApi:
    """Tests for GitHub API calls via gh CLI."""

    def test_gh_api_returns_json(self, monkeypatch):
        """gh_api returns parsed JSON from gh CLI."""
        from cdash.data.github import gh_api
        import subprocess

        class MockResult:
            stdout = '{"login": "testuser"}'
            returncode = 0

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = gh_api("/user")
        assert result == {"login": "testuser"}

    def test_gh_api_returns_none_on_error(self, monkeypatch):
        """gh_api returns None when gh CLI fails."""
        from cdash.data.github import gh_api
        import subprocess

        class MockResult:
            returncode = 1
            stderr = "error"

        def mock_run(*args, **kwargs):
            return MockResult()

        monkeypatch.setattr(subprocess, "run", mock_run)

        result = gh_api("/user")
        assert result is None
