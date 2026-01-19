"""Active sessions panel with spacious multi-line cards."""

import time

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.data.sessions import Session, format_duration, format_relative_time, load_all_sessions
from cdash.theme import AMBER, CORAL, GREEN, RED, TEXT_MUTED


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

    def _render_context_bar(self, percentage: float) -> str:
        """Render context usage bar with color coding."""
        # 8-char bar
        filled = int(percentage / 100 * 8)
        filled = min(8, max(0, filled))
        empty = 8 - filled

        # Color based on percentage: green < 50%, yellow 50-80%, red > 80%
        if percentage > 80:
            color = RED
        elif percentage > 50:
            color = AMBER
        else:
            color = GREEN

        bar = "█" * filled + "░" * empty
        return f"[{color}]{bar}[/] [{TEXT_MUTED}]{percentage:.0f}%[/]"

    def _format_path_display(self, path: str | None) -> str:
        """Format path with home substitution."""
        if not path:
            return ""
        import os
        home = os.path.expanduser("~")
        if path.startswith(home):
            path = "~" + path[len(home):]
        # Truncate from right if too long
        if len(path) > 35:
            path = path[:32] + "..."
        return path

    def render(self) -> str:
        """Render H6e session card layout.

        Layout:
        ┌─────────────────────────────────────────────────────────────────┐
        │ ● schmoli/claude-dashboard                               ACTIVE │
        │   feature/branch-name                         3h   ████████░░ 82%│
        │   "Implement the following plan..."                             │
        │   ⚙ Bash   command...                                      now  │
        │   📖 Read   file.py                                          2m  │
        │   ✏️ Edit   other.py                                          5m  │
        │   140 msgs • 116 tools                    ~/code/project/path   │
        └─────────────────────────────────────────────────────────────────┘
        """
        s = self._session
        lines = []

        # Line 1: GitHub repo (or project) + status badge
        if s.is_active:
            status = f"[bold {GREEN}]●[/]"
            badge = f"[{GREEN}]ACTIVE[/]"
        elif s.is_idle:
            status = f"[bold {AMBER}]◐[/]"
            idle_mins = int((time.time() - s.last_modified) // 60)
            badge = f"[{AMBER}]IDLE {idle_mins}m[/]"
        else:
            status = "[dim]○[/]"
            badge = "[dim]DONE[/]"

        # Use GitHub repo if available, otherwise project name
        title = s.github_repo or format_project_display(s.project_name)
        lines.append(f"{status} [bold]{title}[/]  {badge}")

        # Line 2: branch + duration + context bar
        branch = s.git_branch[:40] if s.git_branch else ""
        dur = format_duration(s.started_at)
        duration = f"{dur}" if dur else ""
        context_bar = self._render_context_bar(s.context_percentage)
        lines.append(f"  [{TEXT_MUTED}]{branch}[/]  {duration}  {context_bar}")

        # Line 3: prompt preview
        if s.full_prompt:
            prompt = s.full_prompt.replace("\n", " ").strip()
            if len(prompt) > 65:
                prompt = prompt[:62] + "..."
            lines.append(f'  [{TEXT_MUTED}]"{prompt}"[/]')
        else:
            lines.append(f"  [{TEXT_MUTED}](no prompt)[/]")

        # Lines 4-6: Tool history (last 3 with context and relative time)
        tool_icons = {
            "Bash": "⚙",
            "Read": "📖",
            "Edit": "✏️",
            "Write": "📝",
            "Grep": "🔍",
            "Glob": "📁",
            "Task": "🤖",
            "WebFetch": "🌐",
            "WebSearch": "🔎",
        }

        if s.recent_tool_calls:
            for tc in s.recent_tool_calls:
                icon = tool_icons.get(tc.tool_name, "⚙")
                context = tc.context[:45] + "..." if len(tc.context) > 45 else tc.context
                rel_time = format_relative_time(tc.timestamp)
                lines.append(
                    f"  [{CORAL}]{icon} {tc.tool_name:<6}[/] "
                    f"[{TEXT_MUTED}]{context:<50}[/] "
                    f"[{TEXT_MUTED}]{rel_time:>4}[/]"
                )
        elif s.current_tool:
            # Fallback to current tool if no recent_tool_calls
            icon = tool_icons.get(s.current_tool, "⚙")
            context = s.current_tool_input[:45] + "..." if len(s.current_tool_input or "") > 45 else (s.current_tool_input or "")
            lines.append(f"  [{CORAL}]{icon} {s.current_tool}[/] [{TEXT_MUTED}]{context}[/]")

        # Footer: stats + path
        stats = f"{s.message_count} msgs • {s.tool_count} tools"
        path = self._format_path_display(s.project_name)
        lines.append(f"  [{TEXT_MUTED}]{stats}  {path}[/]")

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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
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
