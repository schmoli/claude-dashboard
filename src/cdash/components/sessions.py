"""Active sessions widget for displaying Claude Code sessions."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.data.sessions import Session, format_duration, load_all_sessions
from cdash.theme import AMBER, GREEN, TEXT_MUTED


def format_project_display(project_name: str | None) -> str:
    """Format project name for display, handling worktrees.

    For worktrees like '/path/to/project/.worktrees/8', returns 'project#8'.
    For regular paths like '/path/to/project', returns 'project'.
    """
    if not project_name:
        return "unknown"

    if "/.worktrees/" in project_name:
        parts = project_name.split("/.worktrees/")
        parent = parts[0].split("/")[-1]
        worktree = parts[1].split("/")[0]
        return f"{parent}#{worktree}"

    return project_name.split("/")[-1]


class SessionItem(Static):
    """A single session item in the list (legacy, kept for compatibility)."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session

    def render(self) -> str:
        """Render the session item."""
        s = self.session

        # Colored status indicators using theme colors
        if s.is_active:
            status = f"[bold {GREEN}]●[/]"
        elif s.is_idle:
            status = f"[bold {AMBER}]●[/]"
        else:
            status = "[dim]○[/]"

        # Project name (handles worktrees)
        project_display = format_project_display(s.project_name)

        # Truncate prompt preview
        preview = s.prompt_preview[:25] if s.prompt_preview else ""
        if len(s.prompt_preview) > 25:
            preview += "..."

        # Tool indicator (only for active sessions)
        tool = f"⚙ {s.current_tool}" if s.current_tool else ""

        # Duration for active/idle sessions
        duration = ""
        if s.is_active or s.is_idle:
            dur = format_duration(s.started_at)
            if dur:
                duration = f"({dur})"

        return f'{status} {project_display:<16} "{preview}" {tool} {duration}'


class SessionCard(Widget, can_focus=True):
    """Multi-line session card with rich information display."""

    DEFAULT_CSS = """
    SessionCard {
        height: auto;
        padding: 1;
        margin: 0 0 1 0;
        background: $surface;
        border: round #333333;
    }
    SessionCard:focus {
        border: round $primary;
    }
    SessionCard.active {
        border: round $success;
    }
    SessionCard.idle {
        border: round $warning;
    }
    SessionCard > .card-header {
        height: 1;
        width: 100%;
    }
    SessionCard > .card-branch {
        height: 1;
        color: $text-muted;
    }
    SessionCard > .card-divider {
        height: 1;
        color: #444444;
    }
    SessionCard > .card-prompt {
        height: auto;
        max-height: 3;
        padding: 0;
    }
    SessionCard > .card-tool {
        height: 1;
    }
    SessionCard > .card-footer {
        height: 1;
        width: 100%;
    }
    """

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session
        # Add CSS class based on session state
        if session.is_active:
            self.add_class("active")
        elif session.is_idle:
            self.add_class("idle")

    def compose(self) -> ComposeResult:
        """Build the card layout."""
        s = self.session

        # Header: status + project name + badge + duration
        yield Static(self._render_header(), classes="card-header")

        # Branch line (if available)
        if s.git_branch:
            yield Static(f"[{TEXT_MUTED}]branch: {s.git_branch}[/]", classes="card-branch")

        # Divider
        yield Static("[#444444]" + "─" * 60 + "[/]", classes="card-divider")

        # Prompt preview (2 lines max, full prompt on expand)
        prompt_text = self._format_prompt()
        yield Static(prompt_text, classes="card-prompt")

        # Divider
        yield Static("[#444444]" + "─" * 60 + "[/]", classes="card-divider")

        # Current tool with context (if active)
        tool_text = self._render_tool()
        if tool_text:
            yield Static(tool_text, classes="card-tool")

        # Footer: recent tools + stats
        yield Static(self._render_footer(), classes="card-footer")

    def _render_header(self) -> str:
        """Render the card header line."""
        s = self.session

        # Status indicator
        if s.is_active:
            status = f"[bold {GREEN}]●[/]"
            badge = f"[bold {GREEN}][ACTIVE][/]"
        elif s.is_idle:
            import time

            status = f"[bold {AMBER}]◐[/]"
            idle_mins = int((time.time() - s.last_modified) // 60)
            badge = f"[{AMBER}][IDLE {idle_mins}m][/]"
        else:
            status = "[dim]○[/]"
            badge = ""

        # Project name
        project_display = format_project_display(s.project_name)

        # Duration
        duration = ""
        dur = format_duration(s.started_at)
        if dur:
            duration = f"⏱ {dur}"

        # Build header with proper spacing
        left = f"{status} [bold]{project_display}[/]"
        right = f"{badge} {duration}".strip()

        return f"{left:<40} {right:>30}"

    def _format_prompt(self) -> str:
        """Format the prompt preview (2 lines)."""
        s = self.session
        if not s.full_prompt:
            return f"[{TEXT_MUTED}](no prompt)[/]"

        # Show first ~120 chars across 2 lines
        prompt = s.full_prompt.replace("\n", " ").strip()
        if len(prompt) > 120:
            prompt = prompt[:117] + "..."

        return f'[italic]"{prompt}"[/]'

    def _render_tool(self) -> str:
        """Render current tool with context."""
        s = self.session
        if not s.current_tool:
            return ""

        tool_display = f"[bold]⚙ {s.current_tool}[/]"
        if s.current_tool_input:
            # Truncate long paths/commands
            input_display = s.current_tool_input
            if len(input_display) > 50:
                input_display = "..." + input_display[-47:]
            tool_display += f" [{TEXT_MUTED}]{input_display}[/]"

        return tool_display

    def _render_footer(self) -> str:
        """Render the footer with recent tools and stats."""
        s = self.session

        # Recent tools chain (left side)
        if s.recent_tools:
            chain = "→".join(s.recent_tools)
            recent = f"[{TEXT_MUTED}]Recent: {chain}[/]"
        else:
            recent = ""

        # Stats (right side)
        stats = f"[{TEXT_MUTED}]📊 {s.message_count} msgs, {s.tool_count} tools[/]"

        # Pad to fill width
        return f"{recent:<45} {stats:>25}"


class SessionsHeader(Horizontal):
    """Header with title and refresh indicator."""

    def compose(self) -> ComposeResult:
        yield Static("ACTIVE SESSIONS", classes="section-title")
        yield Static("", classes="header-spacer")
        yield RefreshIndicator(id="sessions-refresh")


class SessionCardContainer(VerticalScroll):
    """Scrollable container for session cards."""

    DEFAULT_CSS = """
    SessionCardContainer {
        height: auto;
        max-height: 25;
    }
    """


class ActiveSessionsPanel(Vertical):
    """Panel displaying active sessions with rich cards."""

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield SessionsHeader()
        with SessionCardContainer():
            yield from self._build_session_cards()

    def _build_session_cards(self) -> list[Widget]:
        """Build session card widgets."""
        # Get all sessions
        sessions = load_all_sessions()

        if not sessions:
            return [Static("No active sessions", classes="no-sessions")]

        # Only show active and idle sessions (green/yellow)
        active = [s for s in sessions if s.is_active]
        idle = [s for s in sessions if s.is_idle]

        # Combine: active first, then idle (max 10 total)
        combined = active[:7] + idle[: 10 - len(active[:7])]

        if not combined:
            return [Static("No active sessions", classes="no-sessions")]

        return [SessionCard(session) for session in combined]

    def refresh_sessions(self) -> None:
        """Refresh the sessions list."""
        # Find the container
        try:
            container = self.query_one(SessionCardContainer)
        except Exception:
            return

        # Remove old cards
        for widget in container.query("SessionCard, .no-sessions"):
            widget.remove()

        # Add new cards
        for card in self._build_session_cards():
            container.mount(card)

        # Mark refresh indicator
        try:
            indicator = self.query_one("#sessions-refresh", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass
