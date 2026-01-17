"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def claude_dir(tmp_path):
    """Create a mock ~/.claude directory structure for testing."""
    claude = tmp_path / ".claude"
    claude.mkdir()

    # Create basic structure
    (claude / "projects").mkdir()
    (claude / "plugins" / "cache").mkdir(parents=True)
    (claude / "agents").mkdir()

    # Create stats-cache.json
    stats = claude / "stats-cache.json"
    stats.write_text("""{
    "version": 1,
    "lastComputedDate": "2026-01-17",
    "dailyActivity": [
        {"date": "2026-01-17", "messageCount": 100, "sessionCount": 3, "toolCallCount": 50}
    ]
}""")

    return claude
