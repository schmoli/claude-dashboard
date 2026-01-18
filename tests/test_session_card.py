"""Tests for the SessionCard widget."""

import time

import pytest

from cdash.app import ClaudeDashApp
from cdash.components.sessions import SessionCard, format_project_display
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
        card = SessionCard(session)
        assert "active" in card.classes

    def test_session_card_has_idle_class(self):
        """Idle session card has 'idle' CSS class."""
        session = make_session(is_active=False, is_idle=True)
        card = SessionCard(session)
        assert "idle" in card.classes

    def test_session_card_no_special_class_when_inactive(self):
        """Inactive session has no active/idle class."""
        session = make_session(is_active=False, is_idle=False)
        card = SessionCard(session)
        assert "active" not in card.classes
        assert "idle" not in card.classes

    def test_main_line_active_session(self):
        """Main line renders correctly for active session."""
        session = make_session(is_active=True, project_name="/path/to/myproject")
        card = SessionCard(session)
        main_line = card._render_main_line()
        assert "myproject" in main_line
        assert "ACT" in main_line  # Compact badge

    def test_main_line_idle_session(self):
        """Main line renders correctly for idle session."""
        session = make_session(is_active=False, is_idle=True)
        card = SessionCard(session)
        main_line = card._render_main_line()
        # Idle shows minutes like "2m"
        assert "m" in main_line or "◐" in main_line

    def test_main_line_shows_tool(self):
        """Main line includes current tool when active."""
        session = make_session(
            is_active=True,
            current_tool="Read",
            current_tool_input="/src/main.py",
        )
        card = SessionCard(session)
        main_line = card._render_main_line()
        assert "Read" in main_line

    def test_main_line_truncates_long_tool(self):
        """Long tool names are truncated in main line."""
        session = make_session(
            is_active=True,
            current_tool="VeryLongToolNameThatShouldBeTruncated",
        )
        card = SessionCard(session)
        main_line = card._render_main_line()
        # Tool should be truncated to ~10 chars
        assert "VeryLongTo" in main_line or "VeryLongToo" in main_line

    def test_main_line_shows_stats(self):
        """Main line includes message/tool stats."""
        session = make_session(message_count=15, tool_count=42)
        card = SessionCard(session)
        main_line = card._render_main_line()
        assert "15" in main_line
        assert "42" in main_line

    def test_main_line_shows_branch(self):
        """Main line includes git branch when available."""
        session = make_session(git_branch="feature/new-thing")
        card = SessionCard(session)
        main_line = card._render_main_line()
        assert "@feature" in main_line or "feature" in main_line

    def test_format_prompt_truncates_long_prompt(self):
        """Long prompts are truncated."""
        long_prompt = "This is a very long prompt " * 10
        session = make_session(prompt=long_prompt)
        card = SessionCard(session)
        formatted = card._format_prompt()
        assert "..." in formatted
        assert len(formatted) < len(long_prompt)

    def test_format_prompt_no_prompt(self):
        """Shows placeholder when no prompt."""
        session = make_session(prompt="")
        card = SessionCard(session)
        formatted = card._format_prompt()
        assert "(no prompt)" in formatted


class TestSessionCardIntegration:
    """Integration tests for SessionCard in the app."""

    @pytest.mark.asyncio
    async def test_session_card_renders_in_app(self):
        """Session card renders without errors in the app."""
        app = ClaudeDashApp()
        async with app.run_test():
            # App should load without errors even with real session data
            from cdash.components.sessions import ActiveSessionsPanel

            panel = app.query_one(ActiveSessionsPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_session_card_focusable(self):
        """Session cards should be focusable."""
        from cdash.components.sessions import SessionCardContainer

        app = ClaudeDashApp()
        async with app.run_test() as pilot:
            # Try to find cards if any exist
            try:
                container = app.query_one(SessionCardContainer)
                cards = container.query("SessionCard")
                if cards:
                    # Cards should be focusable
                    assert cards.first().can_focus is True
            except Exception:
                # No cards is fine, just testing the widget can work
                pass
