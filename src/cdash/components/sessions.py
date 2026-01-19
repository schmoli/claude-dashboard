"""Active sessions panel with spacious multi-line cards."""

import time

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.data.sessions import (
    Session,
    format_duration,
    format_file_size,
    format_relative_time,
    load_all_sessions,
)
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


def trim_path_to_project(context: str, project_path: str | None) -> str:
    """Trim absolute paths to be relative to the project directory.

    Since the project name is already shown in the card header, we strip
    the project path prefix from file paths to reduce redundancy.

    Args:
        context: Tool context string (may contain file path)
        project_path: Absolute path to the project directory

    Returns:
        Context with project prefix stripped, or original if not a subpath
    """
    if not context or not project_path:
        return context

    # Ensure project_path ends without trailing slash for clean stripping
    project_path = project_path.rstrip("/")

    # Check if context starts with project path
    if context.startswith(project_path + "/"):
        # Return path relative to project (without leading ./)
        return context[len(project_path) + 1:]

    return context


class SectionHeader(Static):
    """Section divider: ── ACTIVE ───────────────────────────── [2] ──"""

    DEFAULT_CSS = """
    SectionHeader {
        height: 1;
        margin: 0 1 1 1;
        color: $text-muted;
    }
    """

    def __init__(self, label: str, count: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._count = count

    def update_count(self, count: int) -> None:
        """Update the count and refresh."""
        self._count = count
        self.refresh()

    def render(self) -> str:
        left = f"── {self._label} "
        right = f" [{self._count}] ──"
        fill_width = 60 - len(left) - len(right)
        fill = "─" * max(0, fill_width)
        return f"[{TEXT_MUTED}]{left}{fill}{right}[/]"


class SessionCardFrame(Vertical):
    """Framed session panel with CSS round border.

    Cockpit-style instrument panel displaying live session state.
    """

    DEFAULT_CSS = """
    SessionCardFrame {
        border: round #555555;
        padding: 0 1;
        margin: 0 1 1 1;
        background: $surface;
        height: auto;
    }
    SessionCardFrame.active {
        border: round $success;
    }
    SessionCardFrame.idle {
        border: round $warning;
    }
    """

    def __init__(self, session: Session, card_id: str) -> None:
        super().__init__(id=card_id)
        self._session = session
        self._content = Static("")
        self._update_classes()

    def _update_classes(self) -> None:
        """Update CSS classes based on session state."""
        self.remove_class("active", "idle")
        if self._session.is_active:
            self.add_class("active")
        elif self._session.is_idle:
            self.add_class("idle")

    def compose(self) -> ComposeResult:
        self._content.update(self._render_content())
        yield self._content

    def update_session(self, session: Session) -> None:
        """Update card with new session data (in-place, no remount)."""
        self._session = session
        self._update_classes()
        self._content.update(self._render_content())

    def _render_context_bar(self, percentage: float) -> str:
        """Render context usage bar with color coding."""
        filled = int(percentage / 100 * 8)
        filled = min(8, max(0, filled))
        empty = 8 - filled

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
        if len(path) > 35:
            path = path[:32] + "..."
        return path

    def _render_content(self) -> str:
        """Render session card content with tree connectors for tools."""
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

        title = s.github_repo or format_project_display(s.project_name)
        lines.append(f"{status} [bold]{title}[/]  {badge}")

        # Line 2: branch + duration + file size
        branch = s.git_branch[:40] if s.git_branch else ""
        dur = format_duration(s.started_at)
        duration = f"{dur}" if dur else ""
        file_size = format_file_size(s.context_chars)
        lines.append(f"  [{TEXT_MUTED}]{branch}[/]  {duration}  💾 {file_size}")

        # Line 3: prompt preview
        if s.full_prompt:
            prompt = s.full_prompt.replace("\n", " ").strip()
            if len(prompt) > 65:
                prompt = prompt[:62] + "..."
            lines.append(f'  [{TEXT_MUTED}]"{prompt}"[/]')
        else:
            lines.append(f"  [{TEXT_MUTED}](no prompt)[/]")

        # Lines 4-6: Tool history with tree connectors
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
            num_tools = len(s.recent_tool_calls)
            for i, tc in enumerate(s.recent_tool_calls):
                is_last = (i == num_tools - 1)
                prefix = "└─" if is_last else "├─"
                icon = tool_icons.get(tc.tool_name, "⚙")
                trimmed = trim_path_to_project(tc.context, s.project_name)
                context = trimmed[:45] + "..." if len(trimmed) > 45 else trimmed
                rel_time = format_relative_time(tc.timestamp)
                lines.append(
                    f"  {prefix} [{CORAL}]{icon} {tc.tool_name:<6}[/] "
                    f"[{TEXT_MUTED}]{context:<45}[/] "
                    f"[{TEXT_MUTED}]{rel_time:>4}[/]"
                )
        elif s.current_tool:
            icon = tool_icons.get(s.current_tool, "⚙")
            trimmed = trim_path_to_project(s.current_tool_input or "", s.project_name)
            context = trimmed[:45] + "..." if len(trimmed) > 45 else trimmed
            lines.append(f"  └─ [{CORAL}]{icon} {s.current_tool}[/] [{TEXT_MUTED}]{context}[/]")

        # Footer: stats + path
        stats = f"{s.message_count} msgs • {s.tool_count} tools"
        path = self._format_path_display(s.project_name)
        lines.append(f"  [{TEXT_MUTED}]{stats}  {path}[/]")

        return "\n".join(lines)


# Legacy alias for backwards compatibility
class SessionCard(Static):
    """Legacy session card - use SessionCardFrame for new code."""

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

        # Line 2: branch + duration + file size
        branch = s.git_branch[:40] if s.git_branch else ""
        dur = format_duration(s.started_at)
        duration = f"{dur}" if dur else ""
        file_size = format_file_size(s.context_chars)
        lines.append(f"  [{TEXT_MUTED}]{branch}[/]  {duration}  💾 {file_size}")

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
                trimmed = trim_path_to_project(tc.context, s.project_name)
                context = trimmed[:45] + "..." if len(trimmed) > 45 else trimmed
                rel_time = format_relative_time(tc.timestamp)
                lines.append(
                    f"  [{CORAL}]{icon} {tc.tool_name:<6}[/] "
                    f"[{TEXT_MUTED}]{context:<50}[/] "
                    f"[{TEXT_MUTED}]{rel_time:>4}[/]"
                )
        elif s.current_tool:
            # Fallback to current tool if no recent_tool_calls
            icon = tool_icons.get(s.current_tool, "⚙")
            trimmed = trim_path_to_project(s.current_tool_input or "", s.project_name)
            context = trimmed[:45] + "..." if len(trimmed) > 45 else trimmed
            lines.append(f"  [{CORAL}]{icon} {s.current_tool}[/] [{TEXT_MUTED}]{context}[/]")

        # Footer: stats + path
        stats = f"{s.message_count} msgs • {s.tool_count} tools"
        path = self._format_path_display(s.project_name)
        lines.append(f"  [{TEXT_MUTED}]{stats}  {path}[/]")

        return "\n".join(lines)


class SessionsPanel(Vertical):
    """Cockpit-style sessions panel with grouped sections.

    Displays sessions as instrument panels grouped by state (active/idle).
    Uses in-place updates to avoid flashing on refresh.
    """

    DEFAULT_CSS = """
    SessionsPanel {
        height: 1fr;
        padding: 0;
        background: $background;
    }
    SessionsPanel > VerticalScroll {
        height: 1fr;
    }
    SessionsPanel .no-sessions {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        padding: 2;
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cards: dict[str, SessionCardFrame] = {}

    def compose(self) -> ComposeResult:
        yield VerticalScroll(id="cards-container")

    def on_mount(self) -> None:
        """Initial load."""
        self.refresh_sessions()

    def refresh_sessions(self) -> None:
        """Refresh sessions with in-place card updates (no flashing)."""
        sessions = load_all_sessions()

        # Filter to active and idle, sorted: active first, then idle
        active = [s for s in sessions if s.is_active]
        idle = [s for s in sessions if s.is_idle]
        combined = active + idle

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

        # Check if order matches - get current DOM order
        current_dom_order = [w.id.replace("card-", "") for w in container.query(SessionCardFrame)]
        desired_order = [s.session_id for s in combined]

        # If order doesn't match, remount all cards in correct order
        if current_dom_order != desired_order:
            # Remove all cards from DOM (but keep in dict)
            for card in list(container.query(SessionCardFrame)):
                card.remove()

            # Remount in correct order
            for session in combined:
                sid = session.session_id
                if sid in self._cards:
                    self._cards[sid].update_session(session)
                    container.mount(self._cards[sid])
                else:
                    card = SessionCardFrame(session, card_id=f"card-{sid}")
                    self._cards[sid] = card
                    container.mount(card)
        else:
            # Order matches, just update in-place
            for session in combined:
                sid = session.session_id
                if sid in self._cards:
                    self._cards[sid].update_session(session)
                else:
                    card = SessionCardFrame(session, card_id=f"card-{sid}")
                    self._cards[sid] = card
                    container.mount(card)

        # Handle empty state
        if not combined and not self._cards:
            try:
                container.query_one(".no-sessions")
            except Exception:
                container.mount(Static("No active sessions", classes="no-sessions"))
        else:
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
