"""Active sessions panel with spacious multi-line cards."""

import time

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.data.sessions import Session, format_duration, load_all_sessions
from cdash.theme import AMBER, CORAL, GREEN, TEXT_MUTED


def format_project_display(project_name: str | None) -> str:
    """Format project name for display, handling worktrees."""
    if not project_name:
        return "unknown"
    if "/.worktrees/" in project_name:
        parts = project_name.split("/.worktrees/")
        parent = parts[0].split("/")[-1]
        worktree = parts[1].split("/")[0]
        return f"{parent}#{worktree}"
    return project_name.split("/")[-1]


class SessionCard(Static):
    """Multi-line session card that updates in-place (no flashing).

    Layout (3 lines):
    ┌─────────────────────────────────────────────────────────────────┐
    │ ● project-name          ACT   ⏱29m   68/58                      │
    │   ⚙ Bash                                                        │
    │   "Implement the following plan: # k9s-Style Dashboard..."      │
    └─────────────────────────────────────────────────────────────────┘
    """

    DEFAULT_CSS = """
    SessionCard {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
        background: $surface;
        border-left: thick $surface;
    }
    SessionCard.active {
        border-left: thick $success;
    }
    SessionCard.idle {
        border-left: thick $warning;
    }
    """

    def __init__(self, session: Session, card_id: str) -> None:
        super().__init__(id=card_id)
        self._session = session
        self._update_classes()

    def _update_classes(self) -> None:
        """Update CSS classes based on session state."""
        self.remove_class("active", "idle")
        if self._session.is_active:
            self.add_class("active")
        elif self._session.is_idle:
            self.add_class("idle")

    def update_session(self, session: Session) -> None:
        """Update card with new session data (in-place, no remount)."""
        self._session = session
        self._update_classes()
        self.refresh()  # Re-render

    def render(self) -> str:
        """Render 3-line card content."""
        s = self._session

        # Line 1: status indicator + project + badge + duration + stats
        if s.is_active:
            status = f"[bold {GREEN}]●[/]"
            badge = f"[{GREEN}]ACT[/]"
        elif s.is_idle:
            status = f"[bold {AMBER}]◐[/]"
            idle_mins = int((time.time() - s.last_modified) // 60)
            badge = f"[{AMBER}]{idle_mins}m idle[/]"
        else:
            status = "[dim]○[/]"
            badge = ""

        project = format_project_display(s.project_name)
        if s.git_branch:
            project += f"[{TEXT_MUTED}]@{s.git_branch[:12]}[/]"

        dur = format_duration(s.started_at)
        duration = f"⏱{dur}" if dur else ""
        stats = f"[{TEXT_MUTED}]{s.message_count}m/{s.tool_count}t[/]"

        line1 = f"{status} [bold]{project}[/]  {badge}  {duration}  {stats}"

        # Line 2: current tool (if any)
        if s.current_tool:
            tool_input = ""
            if s.current_tool_input:
                inp = s.current_tool_input
                if len(inp) > 50:
                    inp = inp[:47] + "..."
                tool_input = f" [{TEXT_MUTED}]{inp}[/]"
            line2 = f"  [{CORAL}]⚙ {s.current_tool}[/]{tool_input}"
        else:
            line2 = ""

        # Line 3: prompt preview
        if s.full_prompt:
            prompt = s.full_prompt.replace("\n", " ").strip()
            if len(prompt) > 70:
                prompt = prompt[:67] + "..."
            line3 = f'  [{TEXT_MUTED}]"{prompt}"[/]'
        else:
            line3 = f"  [{TEXT_MUTED}](no prompt)[/]"

        # Combine lines
        lines = [line1]
        if line2:
            lines.append(line2)
        lines.append(line3)
        return "\n".join(lines)


class SessionsPanel(Vertical):
    """Main sessions panel with spacious multi-line cards.

    Uses in-place updates to avoid flashing on refresh.
    """

    DEFAULT_CSS = """
    SessionsPanel {
        height: 1fr;
        padding: 0 1;
        background: $background;
    }
    SessionsPanel > .section-title {
        text-align: center;
        color: $secondary;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }
    SessionsPanel > VerticalScroll {
        height: 1fr;
    }
    SessionsPanel > .no-sessions {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        padding: 2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._cards: dict[str, SessionCard] = {}

    def compose(self) -> ComposeResult:
        yield Static("── sessions(all)[0] ──", id="section-title", classes="section-title")
        yield VerticalScroll(id="cards-container")

    def on_mount(self) -> None:
        """Initial load."""
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        """Refresh sessions with in-place card updates (no flashing)."""
        sessions = load_all_sessions()

        # Filter to active and idle only
        active = [s for s in sessions if s.is_active]
        idle = [s for s in sessions if s.is_idle]
        combined = active + idle

        # Update title
        try:
            title = self.query_one("#section-title", Static)
            if active:
                title.update(f"── sessions(active)[{len(active)}] ──")
            elif combined:
                title.update(f"── sessions(idle)[{len(combined)}] ──")
            else:
                title.update("── sessions(none)[0] ──")
        except Exception:
            pass

        try:
            container = self.query_one("#cards-container", VerticalScroll)
        except Exception:
            return

        # Build set of current session IDs
        current_ids = {s.session_id for s in combined}
        existing_ids = set(self._cards.keys())

        # Remove cards for sessions that no longer exist
        for sid in existing_ids - current_ids:
            if sid in self._cards:
                self._cards[sid].remove()
                del self._cards[sid]

        # Update or create cards
        for i, session in enumerate(combined):
            sid = session.session_id
            if sid in self._cards:
                # Update existing card in-place
                self._cards[sid].update_session(session)
            else:
                # Create new card
                card = SessionCard(session, card_id=f"card-{sid}")
                self._cards[sid] = card
                container.mount(card)

        # Handle empty state
        if not combined and not self._cards:
            try:
                container.query_one(".no-sessions")
            except Exception:
                container.mount(Static("No active sessions", classes="no-sessions"))
        else:
            # Remove empty state message if sessions exist
            for widget in container.query(".no-sessions"):
                widget.remove()


# ============================================================================
# Legacy classes kept for backwards compatibility with existing tests
# ============================================================================


class SessionItem(Static):
    """Legacy session item."""

    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session

    def render(self) -> str:
        s = self.session
        if s.is_active:
            status = f"[bold {GREEN}]●[/]"
        elif s.is_idle:
            status = f"[bold {AMBER}]●[/]"
        else:
            status = "[dim]○[/]"
        project_display = format_project_display(s.project_name)
        preview = s.prompt_preview[:25] if s.prompt_preview else ""
        if len(s.prompt_preview) > 25:
            preview += "..."
        tool = f"⚙ {s.current_tool}" if s.current_tool else ""
        duration = ""
        if s.is_active or s.is_idle:
            dur = format_duration(s.started_at)
            if dur:
                duration = f"({dur})"
        return f'{status} {project_display:<16} "{preview}" {tool} {duration}'


class SessionsHeader(Horizontal):
    """Legacy header."""

    def compose(self) -> ComposeResult:
        yield Static("ACTIVE SESSIONS", classes="section-title")
        yield Static("", classes="header-spacer")
        yield RefreshIndicator(id="sessions-refresh")


class SessionCardContainer(VerticalScroll):
    """Legacy container."""

    DEFAULT_CSS = """
    SessionCardContainer {
        height: auto;
        max-height: 25;
    }
    """


class ActiveSessionsPanel(Vertical):
    """Legacy panel for tests."""

    def compose(self) -> ComposeResult:
        yield SessionsHeader()
        yield SessionCardContainer()

    def refresh_sessions(self) -> None:
        try:
            indicator = self.query_one("#sessions-refresh", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass
