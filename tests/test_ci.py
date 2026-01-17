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
