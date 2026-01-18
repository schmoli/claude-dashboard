"""Code change detection for auto-reload functionality."""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodeChangeStatus:
    """Status of code changes since app start."""

    has_changes: bool
    changed_files: list[str]


def get_repo_root() -> Path | None:
    """Get the root of the git repository.

    Returns:
        Path to repo root, or None if not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def get_tracked_python_files(repo_root: Path) -> list[Path]:
    """Get all tracked Python files in src/.

    Args:
        repo_root: Root of the git repository.

    Returns:
        List of tracked .py file paths.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "src/**/*.py"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            timeout=5,
        )
        if result.returncode == 0:
            files = [repo_root / f for f in result.stdout.strip().split("\n") if f]
            return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return []


def check_code_changes(start_time: float, repo_root: Path | None = None) -> CodeChangeStatus:
    """Check if any tracked Python files changed since start_time.

    Args:
        start_time: Unix timestamp when the app started.
        repo_root: Optional repo root path. Auto-detected if not provided.

    Returns:
        CodeChangeStatus with change info.
    """
    if repo_root is None:
        repo_root = get_repo_root()

    if repo_root is None:
        return CodeChangeStatus(has_changes=False, changed_files=[])

    tracked_files = get_tracked_python_files(repo_root)
    changed = []

    for filepath in tracked_files:
        try:
            if filepath.exists():
                mtime = filepath.stat().st_mtime
                if mtime > start_time:
                    changed.append(filepath.name)
        except OSError:
            pass

    return CodeChangeStatus(has_changes=len(changed) > 0, changed_files=changed)


def relaunch_app() -> None:
    """Relaunch the current application.

    Replaces the current process with a new instance.
    """
    os.execv(sys.executable, [sys.executable] + sys.argv)
