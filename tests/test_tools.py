"""Tests for tool usage parsing and display."""

import json
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from cdash.data.tools import (
    ToolUsage,
    horizontal_bar,
    parse_tool_calls_from_file,
    get_tool_usage_for_date,
)


class TestHorizontalBar:
    """Tests for horizontal bar generation."""

    def test_zero_max(self):
        """Zero max returns empty string."""
        result = horizontal_bar(0, 0)
        assert result == ""

    def test_full_bar(self):
        """Max value gives full bar."""
        result = horizontal_bar(100, 100, width=8)
        assert result == "████████"

    def test_half_bar(self):
        """Half value gives roughly half bar."""
        result = horizontal_bar(50, 100, width=8)
        # Should be about 4 blocks
        assert len(result) >= 3
        assert len(result) <= 5

    def test_small_value(self):
        """Small value gives partial block."""
        result = horizontal_bar(10, 100, width=8)
        assert len(result) >= 0
        assert len(result) <= 2


class TestToolUsage:
    """Tests for ToolUsage dataclass."""

    def test_top_tools(self):
        """top_tools returns sorted tools."""
        usage = ToolUsage(tool_counts={"Bash": 100, "Read": 50, "Edit": 75})
        top = usage.top_tools(2)
        assert len(top) == 2
        assert top[0] == ("Bash", 100)
        assert top[1] == ("Edit", 75)

    def test_top_tools_empty(self):
        """top_tools handles empty counts."""
        usage = ToolUsage(tool_counts={})
        top = usage.top_tools(5)
        assert top == []

    def test_total_calls(self):
        """total_calls sums all counts."""
        usage = ToolUsage(tool_counts={"Bash": 100, "Read": 50, "Edit": 75})
        assert usage.total_calls == 225


class TestParseToolCalls:
    """Tests for parse_tool_calls_from_file."""

    def test_parses_tool_use(self):
        """Parses tool_use entries from assistant messages."""
        data = [
            {"type": "user", "message": {"content": "hello"}},
            {
                "type": "assistant",
                "timestamp": "2026-01-16T12:00:00Z",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Bash"},
                        {"type": "tool_use", "name": "Read"},
                    ]
                },
            },
            {
                "type": "assistant",
                "timestamp": "2026-01-16T13:00:00Z",
                "message": {"content": [{"type": "tool_use", "name": "Bash"}]},
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")
            temp_path = Path(f.name)

        try:
            result = parse_tool_calls_from_file(temp_path)
            assert result["Bash"] == 2
            assert result["Read"] == 1
        finally:
            temp_path.unlink()

    def test_filters_by_date(self):
        """Filters by target date when provided."""
        data = [
            {
                "type": "assistant",
                "timestamp": "2026-01-15T12:00:00Z",
                "message": {"content": [{"type": "tool_use", "name": "Bash"}]},
            },
            {
                "type": "assistant",
                "timestamp": "2026-01-16T12:00:00Z",
                "message": {"content": [{"type": "tool_use", "name": "Read"}]},
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for entry in data:
                f.write(json.dumps(entry) + "\n")
            temp_path = Path(f.name)

        try:
            result = parse_tool_calls_from_file(temp_path, date(2026, 1, 16))
            assert "Bash" not in result
            assert result["Read"] == 1
        finally:
            temp_path.unlink()

    def test_handles_empty_file(self):
        """Handles empty file gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = parse_tool_calls_from_file(temp_path)
            assert result == Counter()
        finally:
            temp_path.unlink()

    def test_handles_invalid_json(self):
        """Handles invalid JSON lines gracefully."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write("not valid json\n")
            f.write('{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash"}]}}\n')
            temp_path = Path(f.name)

        try:
            result = parse_tool_calls_from_file(temp_path)
            assert result["Bash"] == 1
        finally:
            temp_path.unlink()


class TestToolBreakdownPanel:
    """Tests for ToolBreakdownPanel widget."""

    @pytest.mark.asyncio
    async def test_panel_present(self):
        """Tool breakdown panel is present in the app."""
        from cdash.app import ClaudeDashApp
        from cdash.components.tools import ToolBreakdownPanel

        app = ClaudeDashApp()
        async with app.run_test():
            panel = app.query_one(ToolBreakdownPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_has_title(self):
        """Panel has a title with section-title class."""
        from cdash.app import ClaudeDashApp
        from cdash.components.tools import ToolBreakdownPanel

        app = ClaudeDashApp()
        async with app.run_test():
            panel = app.query_one(ToolBreakdownPanel)
            titles = panel.query(".section-title")
            assert len(titles) >= 1
