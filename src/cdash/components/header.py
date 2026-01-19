"""Cockpit-style header panel with individual instrument gauges."""

import time

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from cdash.data.resources import get_resource_stats
from cdash.theme import AMBER, CORAL, GREEN, RED, TEXT_MUTED

# Border color for visibility on black
BORDER = "#555555"
BORDER_ACCENT = "#D97757"  # coral for logo panel


class HeaderPanel(Horizontal):
    """Cockpit-style header with individual instrument gauges.

    Layout:
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐ ┌─────────────┐
    │ SESSIONS│ │ MESSAGES│ │  TOOLS  │ │   CPU   │ │     NAV      │ │    LOGO     │
    │    2    │ │  1.2k   │ │   890   │ │ ████░░  │ │ ▸ 1 overview │ │  ___/ /__   │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────────┘ └─────────────┘
    """

    DEFAULT_CSS = """
    HeaderPanel {
        dock: top;
        height: 5;
        background: $background;
        padding: 0 1;
    }

    HeaderPanel .gauge {
        border: round #555555;
        background: $surface;
        width: 12;
        height: 100%;
        margin-right: 1;
        padding: 0 1;
    }

    HeaderPanel .gauge-wide {
        border: round #555555;
        background: $surface;
        width: 16;
        height: 100%;
        margin-right: 1;
        padding: 0 1;
    }

    HeaderPanel #nav-panel {
        border: round #555555;
        background: $surface;
        width: 18;
        height: 100%;
        margin-right: 1;
        padding: 0 1;
    }

    HeaderPanel #logo-panel {
        border: round #D97757;
        background: $surface;
        width: 1fr;
        height: 100%;
        padding: 0 1;
    }

    HeaderPanel .gauge-label {
        height: 1;
        color: #888888;
        text-style: bold;
    }

    HeaderPanel .gauge-value {
        height: 1;
        text-align: center;
    }

    HeaderPanel .gauge-bar {
        height: 1;
    }

    HeaderPanel .nav-row {
        height: 1;
    }

    HeaderPanel .logo-line {
        color: $warning;
        text-style: bold;
    }

    HeaderPanel .logo-tagline {
        color: $primary;
        text-style: bold;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._last_refresh = time.time()

    def compose(self) -> ComposeResult:
        # Gauge 1: Sessions
        with Vertical(id="sessions-gauge", classes="gauge"):
            yield Static("SESSIONS", classes="gauge-label")
            yield Static(f"[{TEXT_MUTED}]0[/]", id="stat-sessions", classes="gauge-value")
            yield Static("", classes="gauge-bar")

        # Gauge 2: CPU with bar
        with Vertical(id="cpu-gauge", classes="gauge"):
            yield Static("CPU", classes="gauge-label")
            yield Static(f"[{TEXT_MUTED}]0%[/]", id="stat-cpu", classes="gauge-value")
            yield Static("░░░░░░░░", id="cpu-bar", classes="gauge-bar")

        # Gauge 3: Memory
        with Vertical(id="mem-gauge", classes="gauge"):
            yield Static("MEM", classes="gauge-label")
            yield Static(f"[{TEXT_MUTED}]0M[/]", id="stat-mem", classes="gauge-value")
            yield Static("", classes="gauge-bar")

        # Gauge 4: Disk (~/.claude size)
        with Vertical(id="disk-gauge", classes="gauge"):
            yield Static("DISK", classes="gauge-label")
            yield Static(f"[{TEXT_MUTED}]0M[/]", id="stat-disk", classes="gauge-value")
            yield Static("", classes="gauge-bar")

        # Gauge 5: Rate (tools/min)
        with Vertical(id="rate-gauge", classes="gauge"):
            yield Static("RATE", classes="gauge-label")
            yield Static(f"[{TEXT_MUTED}]0/m[/]", id="stat-rate", classes="gauge-value")
            yield Static("", classes="gauge-bar")

        # Navigation panel
        with Vertical(id="nav-panel"):
            yield Static(f"[bold {CORAL}]▸ 1 overview[/]", id="nav-1", classes="nav-row")
            yield Static(f"[{TEXT_MUTED}]  2 github[/]", id="nav-2", classes="nav-row")
            yield Static(f"[{TEXT_MUTED}]  3 plugins[/]", id="nav-3", classes="nav-row")

        # Logo panel
        with Vertical(id="logo-panel"):
            yield Static("[bold #E5B567] ___/ /_ ___ / /[/]", classes="logo-line")
            yield Static("[bold #E5B567]/ __/ _ `(_-</ _ \\[/]", classes="logo-line")
            yield Static("⬡ dashboard", id="logo-tagline", classes="logo-tagline")

    def _format_count(self, n: int) -> str:
        """Format large numbers compactly (1234 -> 1.2k)."""
        if n >= 1000:
            return f"{n/1000:.1f}k"
        return str(n)

    def _render_bar(self, percent: float) -> str:
        """Render a percentage as a colored bar."""
        bar_width = 8
        filled = int(percent / 100 * bar_width)
        filled = min(bar_width, max(0, filled))
        empty = bar_width - filled

        if percent > 80:
            color = RED
        elif percent > 50:
            color = AMBER
        else:
            color = GREEN

        return f"[{color}]{'█' * filled}[/][#333333]{'░' * empty}[/]"

    def update_stats(
        self,
        active_count: int,
        msgs_today: int = 0,
        tools_today: int = 0,
    ) -> None:
        """Update session and activity stats."""
        try:
            sessions_widget = self.query_one("#stat-sessions", Static)

            if active_count > 0:
                sessions_widget.update(f"[bold {GREEN}]{active_count}[/]")
            else:
                sessions_widget.update(f"[{TEXT_MUTED}]0[/]")

            # Calculate rate (tools per minute since start of day)
            # Simple approximation: tools_today / minutes since midnight
            from datetime import datetime
            now = datetime.now()
            mins_since_midnight = now.hour * 60 + now.minute
            if mins_since_midnight > 0 and tools_today > 0:
                rate = tools_today / mins_since_midnight
                rate_widget = self.query_one("#stat-rate", Static)
                if rate >= 1:
                    rate_widget.update(f"[{CORAL}]{rate:.0f}/m[/]")
                else:
                    rate_widget.update(f"[{CORAL}]{rate:.1f}/m[/]")
        except Exception:
            pass

    def update_host_stats(self) -> None:
        """Refresh host resource stats from psutil."""
        stats = get_resource_stats()

        try:
            cpu_widget = self.query_one("#stat-cpu", Static)
            cpu_bar = self.query_one("#cpu-bar", Static)
            mem_widget = self.query_one("#stat-mem", Static)
            disk_widget = self.query_one("#stat-disk", Static)

            cpu_pct = min(stats.cpu_percent, 100)

            if stats.memory_mb >= 1024:
                mem_display = f"{stats.memory_mb / 1024:.1f}G"
            else:
                mem_display = f"{stats.memory_mb:.0f}M"

            # Format ~/.claude size
            if stats.claude_dir_mb >= 1024:
                disk_display = f"{stats.claude_dir_mb / 1024:.1f}G"
            else:
                disk_display = f"{stats.claude_dir_mb:.0f}M"

            cpu_widget.update(f"[{CORAL}]{cpu_pct:.0f}%[/]")
            cpu_bar.update(self._render_bar(cpu_pct))
            mem_widget.update(f"[{CORAL}]{mem_display}[/]")
            disk_widget.update(f"[{CORAL}]{disk_display}[/]")
        except Exception:
            pass

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed (update timestamp)."""
        self._last_refresh = time.time()

    def show_code_changed(self, changed: bool, file_count: int = 0) -> None:
        """Show/hide the code changed indicator in logo tagline."""
        try:
            widget = self.query_one("#logo-tagline", Static)
            if changed:
                widget.update(f"[bold {CORAL}]⟳ {file_count}f changed[/]")
            else:
                widget.update("⬡ dashboard")
        except Exception:
            pass

    def set_current_view(self, view_key: str) -> None:
        """Update navigation to highlight active view.

        Args:
            view_key: The key ("1", "2", "3", "4") of the active view
        """
        # Nav items: key -> (id, label)
        nav_items = {
            "1": ("nav-1", "overview"),
            "2": ("nav-2", "github"),
            "3": ("nav-3", "plugins"),
            "4": ("nav-4", "mcp"),
        }

        for key, (nav_id, label) in nav_items.items():
            try:
                widget = self.query_one(f"#{nav_id}", Static)
                if key == view_key:
                    # Active: arrow indicator, bold coral
                    widget.update(f"[bold {CORAL}]▸ {key} {label}[/]")
                else:
                    # Inactive: indented, muted
                    widget.update(f"[{TEXT_MUTED}]  {key} {label}[/]")
            except Exception:
                pass
