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
