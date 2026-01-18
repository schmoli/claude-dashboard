"""Tests for session data loading."""

import json
import time
from pathlib import Path

from cdash.data.sessions import (
    Session,
    _decode_project_path,
    find_session_files,
    format_duration,
    list_projects,
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


class TestIsIdle:
    """Tests for the is_idle property."""

    def test_active_session_is_not_idle(self, tmp_path: Path):
        """Session modified < 60s ago is active, not idle."""
        session_file = tmp_path / "active.jsonl"
        session_file.write_text('{"type": "user"}\n')

        session = parse_session_file(session_file, "project")

        assert session is not None
        assert session.is_active is True
        assert session.is_idle is False

    def test_session_between_60s_and_5min_is_idle(self, tmp_path: Path):
        """Session modified 60s-5min ago is idle."""
        import os

        session_file = tmp_path / "idle.jsonl"
        session_file.write_text('{"type": "user"}\n')

        # Set mtime to 2 minutes ago (120s)
        idle_time = time.time() - 120
        os.utime(session_file, (idle_time, idle_time))

        session = parse_session_file(session_file, "project")

        assert session is not None
        assert session.is_active is False
        assert session.is_idle is True

    def test_session_older_than_5min_is_not_idle(self, tmp_path: Path):
        """Session modified > 5min ago is inactive (not idle)."""
        import os

        session_file = tmp_path / "inactive.jsonl"
        session_file.write_text('{"type": "user"}\n')

        # Set mtime to 10 minutes ago (600s)
        old_time = time.time() - 600
        os.utime(session_file, (old_time, old_time))

        session = parse_session_file(session_file, "project")

        assert session is not None
        assert session.is_active is False
        assert session.is_idle is False


class TestDecodeProjectPath:
    """Tests for project path decoding."""

    def test_hyphenated_folder_preserved_when_exists(self, tmp_path, monkeypatch):
        """Hyphenated folder names like claude-dashboard are preserved when path exists."""
        # Create actual directory structure in tmp_path
        # Simulate: /tmp/xxx/code/my-project
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        project_dir = code_dir / "my-project"
        project_dir.mkdir()

        # Create encoded name based on tmp_path structure
        # e.g., tmp_path = /private/var/folders/.../code/my-project
        # encoded would be: -private-var-folders-...-code-my-project
        encoded = str(tmp_path / "code" / "my-project").replace("/", "-")

        result = _decode_project_path(encoded)
        assert result == str(tmp_path / "code" / "my-project")
        assert "my-project" in result  # hyphen preserved

    def test_falls_back_to_simple_decode_when_path_missing(self):
        """When path doesn't exist, falls back to single-part decode."""
        # Path that definitely doesn't exist
        encoded = "-nonexistent-path-with-hyphens"
        result = _decode_project_path(encoded)
        # Falls back to treating each part separately
        assert result == "/nonexistent/path/with/hyphens"

    def test_real_path_decodes_correctly(self):
        """Test with a path we know exists on the system."""
        # /Users always exists on macOS
        encoded = "-Users"
        result = _decode_project_path(encoded)
        assert result == "/Users"


class TestListProjects:
    """Tests for project listing."""

    def test_lists_project_directories(self, tmp_path, monkeypatch):
        """Lists all project directories."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "-tmp-project1").mkdir()
        (projects_dir / "-tmp-project2").mkdir()

        monkeypatch.setattr(
            "cdash.data.sessions.get_projects_dir", lambda: projects_dir
        )

        projects = list(list_projects())
        assert len(projects) == 2

    def test_skips_non_directories(self, tmp_path, monkeypatch):
        """Skips files in projects directory."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()
        (projects_dir / "-tmp-project").mkdir()
        (projects_dir / "somefile.txt").touch()

        monkeypatch.setattr(
            "cdash.data.sessions.get_projects_dir", lambda: projects_dir
        )

        projects = list(list_projects())
        assert len(projects) == 1


class TestFormatDuration:
    """Tests for format_duration helper."""

    def test_format_zero_returns_empty(self):
        """Zero timestamp returns empty string."""
        assert format_duration(0) == ""

    def test_format_minutes(self):
        """Recent timestamps show minutes."""
        # 5 minutes ago
        started = time.time() - 5 * 60
        result = format_duration(started)
        assert result == "5m"

    def test_format_hours(self):
        """Older timestamps show hours."""
        # 2 hours ago
        started = time.time() - 2 * 60 * 60
        result = format_duration(started)
        assert result == "2h"

    def test_format_days(self):
        """Very old timestamps show days."""
        # 3 days ago
        started = time.time() - 3 * 24 * 60 * 60
        result = format_duration(started)
        assert result == "3d"

    def test_format_boundary_59_minutes(self):
        """59 minutes shows as minutes."""
        started = time.time() - 59 * 60
        result = format_duration(started)
        assert result == "59m"

    def test_format_boundary_60_minutes(self):
        """60 minutes shows as 1 hour."""
        started = time.time() - 60 * 60
        result = format_duration(started)
        assert result == "1h"

    def test_format_boundary_23_hours(self):
        """23 hours shows as hours."""
        started = time.time() - 23 * 60 * 60
        result = format_duration(started)
        assert result == "23h"

    def test_format_boundary_24_hours(self):
        """24 hours shows as 1 day."""
        started = time.time() - 24 * 60 * 60
        result = format_duration(started)
        assert result == "1d"
