"""Resource stats widget showing CPU/memory for Claude processes."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from cdash.data.resources import get_resource_stats
from cdash.theme import BLUE, CORAL


class ResourceStatsWidget(Horizontal):
    """Compact widget showing CPU and memory usage for Claude processes."""

    def __init__(self) -> None:
        super().__init__()
        self._cpu = 0.0
        self._mem_mb = 0.0
        self._mem_pct = 0.0
        self._proc_count = 0

    def compose(self) -> ComposeResult:
        yield Static("HOST", classes="header-title")
        yield Static("", id="cpu-stat", classes="stat-block")
        yield Static("", id="mem-stat", classes="stat-block")
        yield Static("", id="proc-stat", classes="stat-block")

    def refresh_stats(self) -> None:
        """Refresh resource stats from psutil."""
        stats = get_resource_stats()
        self._cpu = stats.cpu_percent
        self._mem_mb = stats.memory_mb
        self._mem_pct = stats.memory_percent
        self._proc_count = stats.process_count
        self._update_display()

    def _update_display(self) -> None:
        """Update all display widgets."""
        try:
            cpu_widget = self.query_one("#cpu-stat", Static)
            mem_widget = self.query_one("#mem-stat", Static)
            proc_widget = self.query_one("#proc-stat", Static)

            # Format CPU (cap display at 999%)
            cpu_display = min(self._cpu, 999)
            cpu_widget.update(f"[{CORAL} bold]{cpu_display:.0f}%[/] cpu")

            # Format memory (show MB if under 1GB, else GB)
            if self._mem_mb >= 1024:
                mem_display = f"{self._mem_mb / 1024:.1f}GB"
            else:
                mem_display = f"{self._mem_mb:.0f}MB"
            mem_widget.update(f"[{CORAL} bold]{mem_display}[/] ram")

            # Process count
            proc_word = "proc" if self._proc_count == 1 else "procs"
            proc_widget.update(f"[{BLUE}]{self._proc_count}[/] {proc_word}")
        except Exception:
            pass
