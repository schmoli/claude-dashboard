"""Active sessions widget for displaying Claude Code sessions."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.sessions import Session, format_duration, load_all_sessions
from cdash.theme import AMBER, GREEN


class SessionItem(Static):
    """A single session item in the list."""

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

        # Project name (last component of path)
        project_display = s.project_name.split("/")[-1] if s.project_name else "unknown"

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


class ActiveSessionsPanel(Vertical):
    """Panel displaying active sessions."""

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield Static("ACTIVE SESSIONS", classes="section-title")
        yield from self._build_session_items()

    def _build_session_items(self) -> list[Static]:
        """Build session item widgets."""
        # Get all sessions (active ones will show with ● indicator)
        sessions = load_all_sessions()

        if not sessions:
            return [Static("No sessions found", classes="no-sessions")]

        # Show active sessions first, then recent inactive ones (up to 5 total)
        active = [s for s in sessions if s.is_active]
        inactive = [s for s in sessions if not s.is_active]

        items = []
        for session in active[:5]:
            items.append(SessionItem(session))

        # Fill remaining slots with inactive sessions
        remaining = 5 - len(items)
        for session in inactive[:remaining]:
            items.append(SessionItem(session))

        return items

    def refresh_sessions(self) -> None:
        """Refresh the sessions list."""
        # Remove old items
        for widget in self.query("SessionItem, .no-sessions"):
            widget.remove()

        # Add new items
        for item in self._build_session_items():
            self.mount(item)
