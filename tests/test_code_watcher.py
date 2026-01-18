"""Tests for code change detection."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cdash.data.code_watcher import (
    CodeChangeStatus,
    check_code_changes,
    get_repo_root,
    get_tracked_python_files,
)


class TestCodeChangeStatus:
    """Tests for CodeChangeStatus dataclass."""

    def test_creates_status(self):
        """Test creating a status object."""
        status = CodeChangeStatus(has_changes=True, changed_files=["foo.py", "bar.py"])
        assert status.has_changes is True
        assert status.changed_files == ["foo.py", "bar.py"]

    def test_no_changes(self):
        """Test status with no changes."""
        status = CodeChangeStatus(has_changes=False, changed_files=[])
        assert status.has_changes is False
        assert status.changed_files == []


class TestGetRepoRoot:
    """Tests for get_repo_root function."""

    def test_returns_path_in_git_repo(self):
        """Test returns a path when in a git repo."""
        # The test itself runs in a git repo
        root = get_repo_root()
        # Should return something (we're in a git repo)
        assert root is not None
        assert root.exists()

    @patch("subprocess.run")
    def test_returns_none_on_error(self, mock_run):
        """Test returns None when git command fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        root = get_repo_root()
        assert root is None

    @patch("subprocess.run")
    def test_returns_none_on_timeout(self, mock_run):
        """Test returns None on timeout."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
        root = get_repo_root()
        assert root is None


class TestGetTrackedPythonFiles:
    """Tests for get_tracked_python_files function."""

    def test_returns_list(self):
        """Test returns a list of paths."""
        root = get_repo_root()
        if root:
            files = get_tracked_python_files(root)
            assert isinstance(files, list)
            # Should find some Python files
            assert len(files) > 0
            # All should be .py files
            for f in files:
                assert f.suffix == ".py"

    @patch("subprocess.run")
    def test_returns_empty_on_error(self, mock_run):
        """Test returns empty list when git command fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        files = get_tracked_python_files(Path("/tmp"))
        assert files == []


class TestCheckCodeChanges:
    """Tests for check_code_changes function."""

    def test_no_changes_when_recent_start(self):
        """Test no changes detected when app just started."""
        start_time = time.time()
        status = check_code_changes(start_time)
        # Files shouldn't have been modified after we started
        assert status.has_changes is False
        assert status.changed_files == []

    def test_detects_changes_with_old_start_time(self):
        """Test detects changes when start time is old."""
        # Use a very old start time
        start_time = 0.0
        status = check_code_changes(start_time)
        # All files will appear changed since they were modified after epoch
        assert status.has_changes is True
        assert len(status.changed_files) > 0

    def test_returns_no_changes_when_not_in_repo(self):
        """Test returns no changes when not in a git repo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pass a non-repo directory
            status = check_code_changes(time.time(), Path(tmpdir))
            assert status.has_changes is False
            assert status.changed_files == []

    def test_returns_no_changes_when_repo_root_is_none(self):
        """Test returns no changes when repo root is None."""
        with patch("cdash.data.code_watcher.get_repo_root", return_value=None):
            status = check_code_changes(time.time(), None)
            assert status.has_changes is False


class TestStatusBarCodeChanged:
    """Tests for StatusBar code changed indicator."""

    @pytest.mark.asyncio
    async def test_status_bar_has_code_changed_widget(self):
        """Test status bar contains code-changed widget."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            from textual.widgets import Static

            from cdash.app import StatusBar

            status_bar = app.query_one(StatusBar)
            code_changed = status_bar.query_one("#code-changed", Static)
            assert code_changed is not None

    @pytest.mark.asyncio
    async def test_code_changed_indicator_shows(self):
        """Test code changed indicator updates."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            from textual.widgets import Static

            from cdash.app import StatusBar

            status_bar = app.query_one(StatusBar)
            status_bar.show_code_changed(True, 3)
            code_changed = status_bar.query_one("#code-changed", Static)
            # Use render() method for Textual Static widgets
            console = code_changed.app.console
            with console.capture() as capture:
                console.print(code_changed.render())
            rendered = capture.get()
            # Compact format: ⟳3f(r) meaning "3 files changed, press r"
            assert "3f" in rendered or "3 file" in rendered

    @pytest.mark.asyncio
    async def test_code_changed_indicator_singular(self):
        """Test code changed indicator uses singular form."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            from textual.widgets import Static

            from cdash.app import StatusBar

            status_bar = app.query_one(StatusBar)
            status_bar.show_code_changed(True, 1)
            code_changed = status_bar.query_one("#code-changed", Static)
            console = code_changed.app.console
            with console.capture() as capture:
                console.print(code_changed.render())
            rendered = capture.get()
            # Compact format: ⟳1f(r) meaning "1 file changed, press r"
            assert "1f" in rendered or "1 file" in rendered

    @pytest.mark.asyncio
    async def test_code_changed_indicator_hides(self):
        """Test code changed indicator hides when no changes."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            from textual.widgets import Static

            from cdash.app import StatusBar

            status_bar = app.query_one(StatusBar)
            status_bar.show_code_changed(False, 0)
            code_changed = status_bar.query_one("#code-changed", Static)
            console = code_changed.app.console
            with console.capture() as capture:
                console.print(code_changed.render())
            rendered = capture.get().strip()
            assert rendered == ""


class TestRelaunchBinding:
    """Tests for relaunch key binding."""

    @pytest.mark.asyncio
    async def test_r_binding_exists(self):
        """Test r key binding is registered."""
        from cdash.app import ClaudeDashApp

        app = ClaudeDashApp()
        # BINDINGS are tuples: (key, action, description)
        bindings = {b[0]: b[1] for b in app.BINDINGS}
        assert "r" in bindings
        assert "relaunch" in bindings["r"]
