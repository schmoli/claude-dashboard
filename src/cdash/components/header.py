"""k9s-style header panel for the dashboard."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from cdash.components.indicators import RefreshIndicator
from cdash.data.resources import get_resource_stats
from cdash.theme import AMBER, CORAL, GREEN, TEXT_MUTED

# ASCII art logo for claude-dash (fits in ~7 lines)
LOGO = """\
       __         __
  ____/ /__ ____ / /
 / __/ / _ `(_-</ _ \\
 \\__/_/\\_,_/___/_//_/
      ⬡ dashboard"""


class HeaderPanel(Vertical):
    """k9s-style header with multi-row stats display.

    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Sessions:   3 active              │        __         __│
    │ Today:      42m / 128t            │   ____/ /__ ____ / /│
    │ CPU:        15%                   │  / __/ / _ `(_-</ _ │
    │ MEM:        1.2G                  │  \\__/_/\\_,_/___/_//_│
    │ Sync:       ● live  ⟳ 2f changed  │       ⬡ dashboard   │
    └─────────────────────────────────────────────────────────┘
    """

    DEFAULT_CSS = """
    HeaderPanel {
        dock: top;
        height: 6;
        background: $surface;
        padding: 0 1;
    }

    HeaderPanel .header-row {
        height: 1;
        width: 100%;
    }

    HeaderPanel .stats-col {
        width: 1fr;
        padding: 0 2;
    }

    HeaderPanel .logo-col {
        width: auto;
        min-width: 26;
        color: $warning;
    }

    HeaderPanel .stat-label {
        width: 12;
        color: $secondary;
    }

    HeaderPanel .stat-value {
        width: auto;
    }

    HeaderPanel .logo-line {
        width: auto;
        text-style: bold;
    }

    HeaderPanel .indicator-row {
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        logo_lines = LOGO.splitlines()

        # Row 1: Sessions / Logo line 1
        with Horizontal(classes="header-row"):
            yield Static("Sessions:", classes="stat-label")
            yield Static("0 active", id="stat-sessions", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static(logo_lines[0] if logo_lines else "", classes="logo-line logo-col")

        # Row 2: Today / Logo line 2
        with Horizontal(classes="header-row"):
            yield Static("Today:", classes="stat-label")
            yield Static("0m / 0t", id="stat-today", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static(logo_lines[1] if len(logo_lines) > 1 else "", classes="logo-line logo-col")

        # Row 3: CPU / Logo line 3
        with Horizontal(classes="header-row"):
            yield Static("CPU:", classes="stat-label")
            yield Static("0%", id="stat-cpu", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static(logo_lines[2] if len(logo_lines) > 2 else "", classes="logo-line logo-col")

        # Row 4: MEM / Logo line 4
        with Horizontal(classes="header-row"):
            yield Static("MEM:", classes="stat-label")
            yield Static("0M", id="stat-mem", classes="stat-value")
            yield Static("", classes="stats-col")
            yield Static(logo_lines[3] if len(logo_lines) > 3 else "", classes="logo-line logo-col")

        # Row 5: Sync indicator / Logo line 5 (or reload hint)
        with Horizontal(classes="header-row indicator-row"):
            yield Static("Sync:", classes="stat-label")
            yield RefreshIndicator(id="header-refresh")
            yield Static("", classes="stats-col")
            yield Static(logo_lines[4] if len(logo_lines) > 4 else "", id="logo-tagline", classes="logo-line logo-col")

    def update_stats(
        self,
        active_count: int,
        msgs_today: int = 0,
        tools_today: int = 0,
    ) -> None:
        """Update session and activity stats."""
        try:
            sessions_widget = self.query_one("#stat-sessions", Static)
            today_widget = self.query_one("#stat-today", Static)

            if active_count > 0:
                sessions_widget.update(f"[{GREEN}]{active_count} active[/]")
            else:
                sessions_widget.update(f"[{TEXT_MUTED}]0 active[/]")

            today_widget.update(f"[{CORAL}]{msgs_today}[/]m / [{CORAL}]{tools_today}[/]t")
        except Exception:
            pass

    def update_host_stats(self) -> None:
        """Refresh host resource stats from psutil."""
        stats = get_resource_stats()

        try:
            cpu_widget = self.query_one("#stat-cpu", Static)
            mem_widget = self.query_one("#stat-mem", Static)

            cpu_display = min(stats.cpu_percent, 999)
            if stats.memory_mb >= 1024:
                mem_display = f"{stats.memory_mb / 1024:.1f}G"
            else:
                mem_display = f"{stats.memory_mb:.0f}M"

            cpu_widget.update(f"[{CORAL}]{cpu_display:.0f}%[/]")
            mem_widget.update(f"[{CORAL}]{mem_display}[/]")
        except Exception:
            pass

    def mark_refreshed(self) -> None:
        """Mark data as just refreshed."""
        try:
            indicator = self.query_one("#header-refresh", RefreshIndicator)
            indicator.mark_refreshed()
        except Exception:
            pass

    def show_code_changed(self, changed: bool, file_count: int = 0) -> None:
        """Show/hide the code changed indicator in logo tagline."""
        try:
            widget = self.query_one("#logo-tagline", Static)
            if changed:
                widget.update(f"[bold {CORAL}]⟳ {file_count} files changed (r)[/]")
            else:
                widget.update(LOGO.splitlines()[4])
        except Exception:
            pass
