"""Session data loading and active session detection."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Simple cache for session data
_sessions_cache: list["Session"] | None = None
_sessions_cache_time: float = 0
_CACHE_TTL = 5.0  # seconds


@dataclass
class Session:
    """Represents a Claude Code session."""

    session_id: str
    project_path: str
    project_name: str
    cwd: str
    last_modified: float
    prompt_preview: str
    current_tool: str | None
    is_active: bool
    started_at: float = 0  # timestamp of first message

    @property
    def is_idle(self) -> bool:
        """Idle = modified 60s-5min ago."""
        age = time.time() - self.last_modified
        return 60 < age <= 300


def format_duration(started_at: float) -> str:
    """Format duration as Xm, Xh, Xd.

    Args:
        started_at: Unix timestamp of when session started

    Returns:
        Human-readable duration string or empty if started_at is 0
    """
    if started_at == 0:
        return ""
    mins = int((time.time() - started_at) / 60)
    if mins < 60:
        return f"{mins}m"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h"
    return f"{hours // 24}d"


def get_claude_dir() -> Path:
    """Get the Claude data directory."""
    return Path.home() / ".claude"


def get_projects_dir() -> Path:
    """Get the projects directory."""
    return get_claude_dir() / "projects"


def list_projects() -> Iterator[tuple[str, Path]]:
    """List all projects with their paths.

    Yields:
        Tuples of (project_name, project_path)
    """
    projects_dir = get_projects_dir()
    if not projects_dir.exists():
        return

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            # Convert encoded path back to readable name
            # e.g., "-home-user-project" -> "/home/user/project"
            name = project_dir.name.replace("-", "/", 1).replace("-", "/")
            yield name, project_dir


def find_session_files(project_dir: Path) -> Iterator[Path]:
    """Find all session JSONL files in a project directory.

    Args:
        project_dir: Path to the project directory

    Yields:
        Paths to session JSONL files
    """
    for file in project_dir.iterdir():
        if file.suffix == ".jsonl" and file.is_file():
            yield file


def parse_session_file(session_file: Path, project_name: str) -> Session | None:
    """Parse a session JSONL file to extract session info.

    Args:
        session_file: Path to the session JSONL file
        project_name: Name of the project this session belongs to

    Returns:
        Session object or None if file is empty/invalid
    """
    try:
        mtime = session_file.stat().st_mtime
        session_id = session_file.stem

        # Read the file to extract info
        prompt_preview = ""
        current_tool = None
        cwd = ""
        started_at = 0.0

        with open(session_file, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Get cwd from first message that has it
                if not cwd and "cwd" in entry:
                    cwd = entry.get("cwd", "")

                # Get started_at from first timestamp
                if started_at == 0.0 and "timestamp" in entry:
                    timestamp_str = entry.get("timestamp", "")
                    if timestamp_str:
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            started_at = dt.timestamp()
                        except (ValueError, AttributeError):
                            pass

                # Get prompt preview from first user message
                if not prompt_preview and entry.get("type") == "user":
                    message = entry.get("message", {})
                    content = message.get("content", "")
                    if isinstance(content, str):
                        # Truncate to first 30 chars
                        prompt_preview = content[:50].strip()
                        if len(content) > 50:
                            prompt_preview += "..."

                # Track latest tool_use
                if entry.get("type") == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                timestamp_str = entry.get("timestamp", "")
                                if timestamp_str and tool_name:
                                    # Parse ISO timestamp to epoch
                                    try:
                                        # Simple approach: use mtime as proxy
                                        current_tool = tool_name
                                    except Exception:
                                        pass

        # Determine if session is active (modified in last 60 seconds)
        is_active = (time.time() - mtime) < 60

        return Session(
            session_id=session_id,
            project_path=str(session_file.parent),
            project_name=project_name,
            cwd=cwd,
            last_modified=mtime,
            prompt_preview=prompt_preview,
            current_tool=current_tool if is_active else None,
            is_active=is_active,
            started_at=started_at,
        )
    except (OSError, PermissionError):
        return None


def load_all_sessions(use_cache: bool = True) -> list[Session]:
    """Load all sessions from all projects.

    Args:
        use_cache: If True, return cached data if available and fresh

    Returns:
        List of Session objects, sorted by last_modified (newest first)
    """
    global _sessions_cache, _sessions_cache_time

    # Return cached data if fresh
    if use_cache and _sessions_cache is not None:
        if time.time() - _sessions_cache_time < _CACHE_TTL:
            return _sessions_cache

    sessions = []

    for project_name, project_dir in list_projects():
        for session_file in find_session_files(project_dir):
            session = parse_session_file(session_file, project_name)
            if session:
                sessions.append(session)

    # Sort by last_modified, newest first
    sessions.sort(key=lambda s: s.last_modified, reverse=True)

    # Update cache
    _sessions_cache = sessions
    _sessions_cache_time = time.time()

    return sessions


def get_active_sessions() -> list[Session]:
    """Get only active sessions.

    Returns:
        List of active Session objects
    """
    return [s for s in load_all_sessions() if s.is_active]
