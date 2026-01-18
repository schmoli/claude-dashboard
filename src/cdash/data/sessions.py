"""Session data loading and active session detection."""

import json
import time
from dataclasses import dataclass, field
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
    # New fields for session cards
    git_branch: str = ""
    message_count: int = 0
    tool_count: int = 0
    recent_tools: list[str] = field(default_factory=list)  # last 5 tools
    current_tool_input: str = ""  # file path or command
    full_prompt: str = ""  # full first user message

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


def _decode_project_path(encoded: str) -> str:
    """Decode an encoded project path back to the original filesystem path.

    Claude encodes paths by replacing / with -. We decode by finding the
    longest valid path prefix. This correctly handles hyphenated folder names.

    Args:
        encoded: Encoded path like "-Users-toli-code-project-name"

    Returns:
        Decoded path like "/Users/toli/code/project-name"
    """
    # Remove leading hyphen (represents root /)
    if encoded.startswith("-"):
        encoded = encoded[1:]

    parts = encoded.split("-")
    if not parts:
        return "/"

    # Build path by greedily finding longest existing prefixes
    result_parts = []
    i = 0
    while i < len(parts):
        # Try joining remaining parts with hyphens to find existing path
        # Start with single part, then try multi-part combinations
        found = False
        for j in range(len(parts), i, -1):
            candidate = "-".join(parts[i:j])
            test_path = "/" + "/".join(result_parts + [candidate])
            if Path(test_path).exists():
                result_parts.append(candidate)
                i = j
                found = True
                break
        if not found:
            # No existing path found, use single part
            result_parts.append(parts[i])
            i += 1

    return "/" + "/".join(result_parts)


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
            # e.g., "-Users-toli-code-project" -> "/Users/toli/code/project"
            name = _decode_project_path(project_dir.name)
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
        full_prompt = ""
        current_tool = None
        current_tool_input = ""
        cwd = ""
        started_at = 0.0
        git_branch = ""
        message_count = 0
        tool_count = 0
        all_tools: list[str] = []  # collect all tools for recent_tools

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

                # Get prompt from first user message
                if not full_prompt and entry.get("type") == "user":
                    message = entry.get("message", {})
                    content = message.get("content", "")
                    if isinstance(content, str):
                        full_prompt = content
                        # Truncate preview to first 50 chars
                        prompt_preview = content[:50].strip()
                        if len(content) > 50:
                            prompt_preview += "..."

                # Count user messages
                if entry.get("type") == "user":
                    message_count += 1

                # Track tool usage
                if entry.get("type") == "assistant":
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "")
                                if tool_name:
                                    tool_count += 1
                                    all_tools.append(tool_name)
                                    current_tool = tool_name
                                    # Extract tool input for context
                                    tool_input = item.get("input", {})
                                    if isinstance(tool_input, dict):
                                        # Get file_path for Read/Edit/Write
                                        if "file_path" in tool_input:
                                            current_tool_input = tool_input["file_path"]
                                        # Get command for Bash
                                        elif "command" in tool_input:
                                            cmd = tool_input["command"]
                                            # Truncate long commands
                                            current_tool_input = cmd[:40] + "..." if len(cmd) > 40 else cmd
                                        # Get pattern for Glob/Grep
                                        elif "pattern" in tool_input:
                                            current_tool_input = tool_input["pattern"]
                                        else:
                                            current_tool_input = ""

                # Look for git branch in summary messages
                if entry.get("type") == "summary":
                    summary = entry.get("summary", "")
                    if isinstance(summary, str) and "branch:" in summary.lower():
                        # Try to extract branch from summary
                        for line_text in summary.split("\n"):
                            if "branch:" in line_text.lower():
                                parts = line_text.split(":", 1)
                                if len(parts) > 1:
                                    git_branch = parts[1].strip()
                                    break

        # Determine if session is active (modified in last 60 seconds)
        is_active = (time.time() - mtime) < 60

        # Get last 5 tools for recent_tools display
        recent_tools = all_tools[-5:] if all_tools else []

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
            git_branch=git_branch,
            message_count=message_count,
            tool_count=tool_count,
            recent_tools=recent_tools,
            current_tool_input=current_tool_input if is_active else "",
            full_prompt=full_prompt,
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
