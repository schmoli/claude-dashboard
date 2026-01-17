"""Tool usage parsing from session JSONL files."""

import json
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from cdash.data.sessions import get_projects_dir, list_projects

# Simple cache for tool usage
_tool_cache: dict[str, "ToolUsage"] = {}
_tool_cache_time: dict[str, float] = {}
_CACHE_TTL = 30.0  # seconds - less frequent refresh for tools


@dataclass
class ToolUsage:
    """Aggregated tool usage data."""

    tool_counts: dict[str, int]

    def top_tools(self, n: int = 6) -> list[tuple[str, int]]:
        """Get top N tools by usage count."""
        sorted_tools = sorted(self.tool_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tools[:n]

    @property
    def total_calls(self) -> int:
        """Total tool calls."""
        return sum(self.tool_counts.values())


def parse_tool_calls_from_file(
    session_file: Path, target_date: date | None = None
) -> Counter[str]:
    """Parse tool calls from a session JSONL file.

    Args:
        session_file: Path to session JSONL file
        target_date: If provided, only count tools from this date

    Returns:
        Counter of tool name -> count
    """
    tool_counts: Counter[str] = Counter()
    target_date_str = target_date.isoformat() if target_date else None

    try:
        with open(session_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") != "assistant":
                        continue

                    # Check date if filtering
                    if target_date_str:
                        timestamp = entry.get("timestamp", "")
                        if not timestamp.startswith(target_date_str):
                            continue

                    # Extract tool calls from message content
                    message = entry.get("message", {})
                    content = message.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "tool_use":
                                tool_name = item.get("name", "unknown")
                                tool_counts[tool_name] += 1
                except json.JSONDecodeError:
                    continue
    except (OSError, PermissionError):
        pass

    return tool_counts


def get_tool_usage_for_date(target_date: date | None = None, use_cache: bool = True) -> ToolUsage:
    """Get aggregated tool usage for a specific date.

    Args:
        target_date: Date to aggregate for (defaults to today)
        use_cache: If True, return cached data if available and fresh

    Returns:
        ToolUsage with aggregated counts
    """
    if target_date is None:
        target_date = date.today()

    cache_key = target_date.isoformat()

    # Return cached data if fresh
    if use_cache and cache_key in _tool_cache:
        if time.time() - _tool_cache_time.get(cache_key, 0) < _CACHE_TTL:
            return _tool_cache[cache_key]

    total_counts: Counter[str] = Counter()

    for _project_name, project_dir in list_projects():
        for session_file in project_dir.glob("*.jsonl"):
            if session_file.is_file():
                counts = parse_tool_calls_from_file(session_file, target_date)
                total_counts.update(counts)

    result = ToolUsage(tool_counts=dict(total_counts))

    # Update cache
    _tool_cache[cache_key] = result
    _tool_cache_time[cache_key] = time.time()

    return result


def horizontal_bar(value: int, max_value: int, width: int = 12) -> str:
    """Generate a horizontal bar using Unicode block characters.

    Args:
        value: Current value
        max_value: Maximum value (for scaling)
        width: Maximum bar width in characters

    Returns:
        String representation of bar
    """
    if max_value == 0:
        return ""

    # Full and partial block chars
    full_block = "█"
    partial_blocks = " ▏▎▍▌▋▊▉█"

    # Calculate how many full blocks and the remainder
    ratio = value / max_value
    total_eighths = int(ratio * width * 8)
    full_count = total_eighths // 8
    remainder = total_eighths % 8

    bar = full_block * full_count
    if remainder > 0 and full_count < width:
        bar += partial_blocks[remainder]

    return bar
