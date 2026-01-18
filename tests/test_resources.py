"""Tests for resource stats data loading and display."""

from unittest.mock import MagicMock, patch

import pytest

from cdash.data.resources import ResourceStats, find_claude_processes, get_resource_stats


class TestResourceStats:
    """Tests for ResourceStats dataclass."""

    def test_creates_resource_stats(self):
        """Can create a ResourceStats instance."""
        stats = ResourceStats(
            process_count=2,
            cpu_percent=25.5,
            memory_mb=512.0,
            memory_percent=4.2,
        )
        assert stats.process_count == 2
        assert stats.cpu_percent == 25.5
        assert stats.memory_mb == 512.0
        assert stats.memory_percent == 4.2


class TestFindClaudeProcesses:
    """Tests for finding Claude processes."""

    def test_finds_process_by_name(self):
        """Finds processes with 'claude' in name."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "claude", "cmdline": []}

        with patch("cdash.data.resources.psutil.process_iter", return_value=[mock_proc]):
            procs = find_claude_processes()
            assert len(procs) == 1
            assert procs[0] == mock_proc

    def test_finds_process_by_cmdline(self):
        """Finds processes with 'claude' in command line."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "node", "cmdline": ["/usr/local/bin/node", "/path/to/claude"]}

        with patch("cdash.data.resources.psutil.process_iter", return_value=[mock_proc]):
            procs = find_claude_processes()
            assert len(procs) == 1

    def test_skips_unrelated_processes(self):
        """Skips processes without 'claude' in name or cmdline."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "python", "cmdline": ["python", "script.py"]}

        with patch("cdash.data.resources.psutil.process_iter", return_value=[mock_proc]):
            procs = find_claude_processes()
            assert len(procs) == 0

    def test_handles_empty_cmdline(self):
        """Handles processes with None cmdline."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "other", "cmdline": None}

        with patch("cdash.data.resources.psutil.process_iter", return_value=[mock_proc]):
            procs = find_claude_processes()
            assert len(procs) == 0


class TestGetResourceStats:
    """Tests for get_resource_stats."""

    def test_returns_stats_with_no_processes(self):
        """Returns zero stats when no Claude processes found."""
        mock_vm = MagicMock()
        mock_vm.total = 16 * 1024 * 1024 * 1024  # 16GB

        with (
            patch("cdash.data.resources.find_claude_processes", return_value=[]),
            patch("cdash.data.resources.psutil.virtual_memory", return_value=mock_vm),
        ):
            stats = get_resource_stats(use_cache=False)
            assert stats.process_count == 0
            assert stats.cpu_percent == 0.0
            assert stats.memory_mb == 0.0
            assert stats.memory_percent == 0.0

    def test_aggregates_multiple_processes(self):
        """Aggregates stats across multiple processes."""
        mock_proc1 = MagicMock()
        mock_proc1.cpu_percent.return_value = 10.0
        mock_mem1 = MagicMock()
        mock_mem1.rss = 100 * 1024 * 1024  # 100MB
        mock_proc1.memory_info.return_value = mock_mem1

        mock_proc2 = MagicMock()
        mock_proc2.cpu_percent.return_value = 15.0
        mock_mem2 = MagicMock()
        mock_mem2.rss = 200 * 1024 * 1024  # 200MB
        mock_proc2.memory_info.return_value = mock_mem2

        mock_vm = MagicMock()
        mock_vm.total = 16 * 1024 * 1024 * 1024  # 16GB

        with (
            patch(
                "cdash.data.resources.find_claude_processes", return_value=[mock_proc1, mock_proc2]
            ),
            patch("cdash.data.resources.psutil.virtual_memory", return_value=mock_vm),
        ):
            stats = get_resource_stats(use_cache=False)
            assert stats.process_count == 2
            assert stats.cpu_percent == 25.0
            assert stats.memory_mb == 300.0
            # 300MB / 16GB * 100 = 1.831%
            assert abs(stats.memory_percent - 1.831) < 0.01


class TestResourceStatsWidget:
    """Tests for the ResourceStatsWidget component."""

    @pytest.mark.asyncio
    async def test_widget_present_in_overview(self):
        """ResourceStatsWidget is present in Overview tab."""
        from cdash.app import ClaudeDashApp
        from cdash.components.resources import ResourceStatsWidget

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            widget = app.query_one(ResourceStatsWidget)
            assert widget is not None

    @pytest.mark.asyncio
    async def test_widget_has_stat_blocks(self):
        """Widget contains CPU, memory, and process count stat blocks."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            cpu_stat = app.query_one("#cpu-stat")
            mem_stat = app.query_one("#mem-stat")
            proc_stat = app.query_one("#proc-stat")
            assert cpu_stat is not None
            assert mem_stat is not None
            assert proc_stat is not None
