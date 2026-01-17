"""Tests for session data loading."""

import json
import time
from pathlib import Path

from cdash.data.sessions import (
    Session,
    find_session_files,
    parse_session_file,
)


class TestSession:
    """Tests for the Session dataclass."""

    def test_session_creation(self):
        """Can create a Session with all fields."""
        session = Session(
            session_id="test-uuid",
            project_path="/home/user/project",
            project_name="/home/user/project",
            cwd="/home/user/project",
            last_modified=time.time(),
            prompt_preview="Hello world",
            current_tool="Read",
            is_active=True,
        )
        assert session.session_id == "test-uuid"
        assert session.is_active is True
        assert session.current_tool == "Read"


class TestFindSessionFiles:
    """Tests for finding session files in a project directory."""

    def test_finds_jsonl_files(self, tmp_path: Path):
        """Finds .jsonl files in directory."""
        (tmp_path / "session1.jsonl").touch()
        (tmp_path / "session2.jsonl").touch()
        (tmp_path / "other.txt").touch()

        files = list(find_session_files(tmp_path))
        assert len(files) == 2
        assert all(f.suffix == ".jsonl" for f in files)

    def test_ignores_subdirectories(self, tmp_path: Path):
        """Doesn't recurse into subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "session.jsonl").touch()

        files = list(find_session_files(tmp_path))
        assert len(files) == 0


class TestParseSessionFile:
    """Tests for parsing session JSONL files."""

    def test_parses_session_file(self, tmp_path: Path):
        """Can parse a valid session file."""
        session_file = tmp_path / "test-session-id.jsonl"

        # Write sample session data
        entries = [
            {
                "type": "user",
                "cwd": "/home/user/project",
                "sessionId": "test-session-id",
                "message": {"role": "user", "content": "Hello, can you help me?"},
                "timestamp": "2026-01-17T04:00:00.000Z",
            },
            {
                "type": "assistant",
                "sessionId": "test-session-id",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "tool_use", "name": "Read", "input": {"file_path": "/test"}}
                    ],
                },
                "timestamp": "2026-01-17T04:00:01.000Z",
            },
        ]

        with open(session_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        session = parse_session_file(session_file, "project-name")

        assert session is not None
        assert session.session_id == "test-session-id"
        assert session.project_name == "project-name"
        assert session.cwd == "/home/user/project"
        assert "Hello, can you help me?" in session.prompt_preview
        # File was just created, so it's active and shows current tool
        assert session.is_active is True
        assert session.current_tool == "Read"

    def test_handles_empty_file(self, tmp_path: Path):
        """Returns session even for empty file."""
        session_file = tmp_path / "empty.jsonl"
        session_file.touch()

        session = parse_session_file(session_file, "project")

        assert session is not None
        assert session.session_id == "empty"
        assert session.prompt_preview == ""

    def test_handles_invalid_json_lines(self, tmp_path: Path):
        """Skips invalid JSON lines gracefully."""
        session_file = tmp_path / "bad.jsonl"
        session_file.write_text('not valid json\n{"type": "user"}\n')

        session = parse_session_file(session_file, "project")

        assert session is not None  # Should still return a session


class TestActiveSessionDetection:
    """Tests for active session detection."""

    def test_recent_file_is_active(self, tmp_path: Path):
        """Session is active if file was modified recently."""
        session_file = tmp_path / "recent.jsonl"
        session_file.write_text('{"type": "user"}\n')

        session = parse_session_file(session_file, "project")

        # File was just created, so it should be active
        assert session is not None
        assert session.is_active is True

    def test_old_file_is_inactive(self, tmp_path: Path):
        """Session is inactive if file is old."""
        import os

        session_file = tmp_path / "old.jsonl"
        session_file.write_text('{"type": "user"}\n')

        # Set mtime to 5 minutes ago
        old_time = time.time() - 300
        os.utime(session_file, (old_time, old_time))

        session = parse_session_file(session_file, "project")

        assert session is not None
        assert session.is_active is False
        assert session.current_tool is None  # No tool shown for inactive sessions
