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
    """Ultra-compact session card - 2 lines max.

    Line 1: ● project@branch ACT ⏱5m 12m/48t ⚙ Tool
    Line 2: "prompt preview..."
    """

    DEFAULT_CSS = """
    SessionCard {
        height: auto;
        padding: 0 1;
        margin: 0;
        background: $surface;
        border-left: thick $surface;
    }
    SessionCard:focus {
        border-left: thick $primary;
    }
    SessionCard.active {
        border-left: thick $success;
    }
    SessionCard.idle {
        border-left: thick $warning;
    }
    SessionCard > .card-line {
        height: 1;
        width: 100%;
    }
    """

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session
        if session.is_active:
            self.add_class("active")
        elif session.is_idle:
            self.add_class("idle")

    def compose(self) -> ComposeResult:
        """Build ultra-compact 2-line layout."""
        # Line 1: status + project + badge + duration + stats + tool
        yield Static(self._render_main_line(), classes="card-line")
        # Line 2: prompt only
        yield Static(self._format_prompt(), classes="card-line")

    def _render_main_line(self) -> str:
        """Render single dense line: ● project@br ACT ⏱5m 12m/48t ⚙Tool."""
        import time

        s = self.session

        # Status indicator + badge
        if s.is_active:
            status = f"[bold {GREEN}]●[/]"
            badge = f"[{GREEN}]ACT[/]"
        elif s.is_idle:
            status = f"[bold {AMBER}]◐[/]"
            idle_mins = int((time.time() - s.last_modified) // 60)
            badge = f"[{AMBER}]{idle_mins}m[/]"
        else:
            status = "[dim]○[/]"
            badge = ""

        # Project name + branch (truncated)
        project_display = format_project_display(s.project_name)
        if len(project_display) > 16:
            project_display = project_display[:14] + ".."
        if s.git_branch:
            branch = s.git_branch[:8]
            project_display += f"[{TEXT_MUTED}]@{branch}[/]"

        # Duration
        dur = format_duration(s.started_at)
        duration = f"⏱{dur}" if dur else ""

        # Stats ultra-compact
        stats = f"[{TEXT_MUTED}]{s.message_count}/{s.tool_count}[/]"

        # Current tool (inline, short)
        tool = ""
        if s.current_tool:
            tool_name = s.current_tool[:10] if len(s.current_tool) > 10 else s.current_tool
            tool = f"[bold]⚙{tool_name}[/]"

        # Assemble
        parts = [f"{status} [bold]{project_display}[/]", badge, duration, stats, tool]
        return " ".join(p for p in parts if p)

    def _format_prompt(self) -> str:
        """Format single-line prompt preview (compact)."""
        s = self.session
        if not s.full_prompt:
            return f"[{TEXT_MUTED}](no prompt)[/]"

        # Single line, ~60 chars
        prompt = s.full_prompt.replace("\n", " ").strip()
        if len(prompt) > 60:
            prompt = prompt[:57] + "..."

        return f'[{TEXT_MUTED}]"{prompt}"[/]'


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
