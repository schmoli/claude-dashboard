"""Tests for the SessionCard widget."""

import time
from unittest.mock import patch

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.sessions import (
    MIN_CARD_VISIBILITY,
    SessionCard,
    SessionsPanel,
    format_project_display,
    trim_path_to_project,
)
from cdash.data.sessions import Session


def make_session(
    project_name: str = "/test/project",
    is_active: bool = True,
    is_idle: bool = False,
    prompt: str = "Test prompt",
    current_tool: str | None = None,
    current_tool_input: str = "",
    git_branch: str = "",
    message_count: int = 5,
    tool_count: int = 10,
    recent_tools: list[str] | None = None,
) -> Session:
    """Create a test session with configurable properties."""
    now = time.time()
    if is_active:
        last_modified = now  # Active = modified in last 60s
    elif is_idle:
        last_modified = now - 120  # Idle = 60s-5min ago
    else:
        last_modified = now - 600  # Inactive = older than 5min

    return Session(
        session_id="test-session",
        project_path="/test/project",
        project_name=project_name,
        cwd="/test/project",
        last_modified=last_modified,
        prompt_preview=prompt[:50] + "..." if len(prompt) > 50 else prompt,
        current_tool=current_tool if is_active else None,
        is_active=is_active,
        started_at=now - 1800,  # 30 min ago
        git_branch=git_branch,
        message_count=message_count,
        tool_count=tool_count,
        recent_tools=recent_tools or [],
        current_tool_input=current_tool_input if is_active else "",
        full_prompt=prompt,
    )


class TestSessionCard:
    """Tests for SessionCard widget."""

    def test_session_card_has_active_class(self):
        """Active session card has 'active' CSS class."""
        session = make_session(is_active=True)
        card = SessionCard(session, card_id="test-card")
        assert "active" in card.classes

    def test_session_card_has_idle_class(self):
        """Idle session card has 'idle' CSS class."""
        session = make_session(is_active=False, is_idle=True)
        card = SessionCard(session, card_id="test-card")
        assert "idle" in card.classes

    def test_session_card_no_special_class_when_inactive(self):
        """Inactive session has no active/idle class."""
        session = make_session(is_active=False, is_idle=False)
        card = SessionCard(session, card_id="test-card")
        assert "active" not in card.classes
        assert "idle" not in card.classes

    def test_render_active_session(self):
        """Render outputs correctly for active session."""
        session = make_session(is_active=True, project_name="/path/to/myproject")
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        assert "myproject" in rendered
        assert "ACT" in rendered  # Compact badge

    def test_render_idle_session(self):
        """Render outputs correctly for idle session."""
        session = make_session(is_active=False, is_idle=True)
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        # Idle shows idle indicator
        assert "idle" in rendered or "◐" in rendered

    def test_render_shows_tool(self):
        """Render includes current tool when active."""
        session = make_session(
            is_active=True,
            current_tool="Read",
            current_tool_input="/src/main.py",
        )
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        assert "Read" in rendered

    def test_render_shows_stats(self):
        """Render includes message/tool stats."""
        session = make_session(message_count=15, tool_count=42)
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        assert "15" in rendered
        assert "42" in rendered

    def test_render_shows_branch(self):
        """Render includes git branch when available."""
        session = make_session(git_branch="feature/new-thing")
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        assert "@feature" in rendered or "feature" in rendered

    def test_render_truncates_long_prompt(self):
        """Long prompts are truncated in render."""
        long_prompt = "This is a very long prompt " * 10
        session = make_session(prompt=long_prompt)
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        assert "..." in rendered

    def test_render_no_prompt(self):
        """Shows placeholder when no prompt."""
        session = make_session(prompt="")
        card = SessionCard(session, card_id="test-card")
        rendered = card.render()
        assert "(no prompt)" in rendered


class TestSessionCardIntegration:
    """Integration tests for SessionCard in the app."""

    @pytest.mark.asyncio
    async def test_sessions_panel_renders_in_app(self):
        """Sessions panel renders without errors in the app."""
        app = ClaudeDashApp()
        async with app.run_test():
            # App should load without errors
            panel = app.query_one(SessionsPanel)
            assert panel is not None


class TestFormatProjectDisplay:
    """Tests for format_project_display function."""

    def test_simple_project(self):
        """Simple project path returns just the name."""
        result = format_project_display("/home/user/myproject")
        assert result == "myproject"

    def test_worktree_project(self):
        """Worktree path shows parent#worktree format."""
        result = format_project_display("/home/user/repo/.worktrees/123")
        assert result == "repo#123"

    def test_none_project(self):
        """None project returns 'unknown'."""
        result = format_project_display(None)
        assert result == "unknown"


class TestTrimPathToProject:
    """Tests for trim_path_to_project function."""

    def test_trims_project_prefix(self):
        """Strips project path prefix from file path."""
        result = trim_path_to_project(
            "/Users/toli/code/project/src/main.py",
            "/Users/toli/code/project",
        )
        assert result == "src/main.py"

    def test_handles_trailing_slash(self):
        """Works with trailing slash in project path."""
        result = trim_path_to_project(
            "/Users/toli/code/project/src/main.py",
            "/Users/toli/code/project/",
        )
        assert result == "src/main.py"

    def test_preserves_non_subpath(self):
        """Returns original if context is not under project."""
        result = trim_path_to_project(
            "/other/path/file.py",
            "/Users/toli/code/project",
        )
        assert result == "/other/path/file.py"

    def test_handles_empty_context(self):
        """Returns empty string for empty context."""
        result = trim_path_to_project("", "/Users/toli/code/project")
        assert result == ""

    def test_handles_none_project(self):
        """Returns original context when project is None."""
        result = trim_path_to_project("/some/file.py", None)
        assert result == "/some/file.py"

    def test_handles_non_path_context(self):
        """Non-path context (commands, queries) unchanged."""
        result = trim_path_to_project(
            "npm run build",
            "/Users/toli/code/project",
        )
        assert result == "npm run build"

    def test_handles_partial_match(self):
        """Doesn't strip if project is only partial match."""
        result = trim_path_to_project(
            "/Users/toli/code/project-other/src/file.py",
            "/Users/toli/code/project",
        )
        # Should NOT strip because project-other != project
        assert result == "/Users/toli/code/project-other/src/file.py"


class TestSessionCardStickiness:
    """Tests for session card stickiness behavior."""

    def make_session_with_id(
        self,
        session_id: str,
        is_active: bool = True,
        is_idle: bool = False,
        project_name: str = "/test/project",
    ) -> Session:
        """Create a test session with a specific ID."""
        now = time.time()
        if is_active:
            last_modified = now
        elif is_idle:
            last_modified = now - 120
        else:
            last_modified = now - 600  # Inactive

        return Session(
            session_id=session_id,
            project_path=project_name,
            project_name=project_name,
            cwd=project_name,
            last_modified=last_modified,
            prompt_preview="Test",
            current_tool=None,
            is_active=is_active,
            started_at=now - 1800,
            git_branch="main",
            message_count=5,
            tool_count=10,
            recent_tools=[],
            current_tool_input="",
            full_prompt="Test prompt",
        )

    def test_active_session_tracked_on_first_show(self):
        """Active sessions are tracked when first shown."""
        panel = SessionsPanel()
        panel._card_first_shown = {}

        active_session = self.make_session_with_id("sess-1", is_active=True)

        with patch("cdash.components.sessions.load_all_sessions") as mock_load:
            mock_load.return_value = [active_session]
            with patch("cdash.components.sessions.time.time") as mock_time:
                mock_time.return_value = 1000.0
                # Call refresh_sessions but catch the DOM query exception
                try:
                    panel.refresh_sessions()
                except Exception:
                    pass

        assert "sess-1" in panel._card_first_shown
        assert panel._card_first_shown["sess-1"] == 1000.0

    def test_inactive_session_stays_visible_within_window(self):
        """Session stays visible within MIN_CARD_VISIBILITY window."""
        panel = SessionsPanel()
        # Simulate session was first shown at t=1000
        panel._card_first_shown = {"sess-1": 1000.0}

        # Session is now inactive (last_modified > 5min ago)
        inactive_session = self.make_session_with_id("sess-1", is_active=False, is_idle=False)

        with patch("cdash.components.sessions.load_all_sessions") as mock_load:
            mock_load.return_value = [inactive_session]
            with patch("cdash.components.sessions.time.time") as mock_time:
                # Current time is still within window (1000 + 60 = 1060 < 1000 + 180)
                mock_time.return_value = 1060.0
                try:
                    panel.refresh_sessions()
                except Exception:
                    pass

        # Session should still be tracked (not removed from dict)
        assert "sess-1" in panel._card_first_shown

    def test_inactive_session_removed_after_window_expires(self):
        """Session is removed after MIN_CARD_VISIBILITY window expires."""
        panel = SessionsPanel()
        # Simulate session was first shown at t=1000
        panel._card_first_shown = {"sess-1": 1000.0}

        # Session is now inactive
        inactive_session = self.make_session_with_id("sess-1", is_active=False, is_idle=False)

        with patch("cdash.components.sessions.load_all_sessions") as mock_load:
            mock_load.return_value = [inactive_session]
            with patch("cdash.components.sessions.time.time") as mock_time:
                # Current time is past window (1000 + 200 > 1000 + 180)
                mock_time.return_value = 1000.0 + MIN_CARD_VISIBILITY + 20
                try:
                    panel.refresh_sessions()
                except Exception:
                    pass

        # Session should be removed from tracking
        assert "sess-1" not in panel._card_first_shown

    def test_idle_session_updates_tracking(self):
        """Idle sessions keep their original first_shown time."""
        panel = SessionsPanel()
        # Session was first shown at t=1000
        panel._card_first_shown = {"sess-1": 1000.0}

        # Session is now idle
        idle_session = self.make_session_with_id("sess-1", is_active=False, is_idle=True)

        with patch("cdash.components.sessions.load_all_sessions") as mock_load:
            mock_load.return_value = [idle_session]
            with patch("cdash.components.sessions.time.time") as mock_time:
                mock_time.return_value = 1100.0
                try:
                    panel.refresh_sessions()
                except Exception:
                    pass

        # Original timestamp should be preserved
        assert panel._card_first_shown["sess-1"] == 1000.0

    def test_min_card_visibility_constant(self):
        """MIN_CARD_VISIBILITY is 180 seconds (3 minutes)."""
        assert MIN_CARD_VISIBILITY == 180.0
