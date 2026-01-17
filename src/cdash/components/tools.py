"""Tool breakdown widget for displaying tool usage statistics."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static

from cdash.data.tools import get_tool_usage_for_date


def horizontal_bar_colored(value: int, max_val: int, width: int = 12) -> str:
    """Generate a colored horizontal bar using Unicode block characters.

    Args:
        value: Current value
        max_val: Maximum value (for scaling)
        width: Maximum bar width in characters

    Returns:
        String representation of bar with Rich markup for color
    """
    if max_val == 0:
        return ""

    filled = int((value / max_val) * width) if max_val > 0 else 0
    empty = width - filled

    # Higher usage = brighter color
    if filled == width:
        color = "green"
    elif filled > width // 2:
        color = "yellow"
    else:
        color = "white"

    return f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"


class ToolItem(Static):
    """A single tool in the breakdown list."""

    def __init__(self, name: str, count: int, max_count: int) -> None:
        super().__init__()
        self.tool_name = name
        self.count = count
        self.max_count = max_count

    def render(self) -> str:
        """Render the tool item with colored bar."""
        bar = horizontal_bar_colored(self.count, self.max_count, width=12)
        return f"{self.tool_name:<10} {bar} [cyan]{self.count:>3}[/]"


class ToolBreakdownPanel(Vertical):
    """Panel displaying tool usage breakdown for today."""

    DEFAULT_CSS = """
    ToolBreakdownPanel {
        height: auto;
        padding: 0 1;
        margin-top: 1;
    }

    ToolBreakdownPanel > .section-title {
        text-style: bold;
        color: $text;
        padding: 0;
        margin-bottom: 1;
    }

    ToolBreakdownPanel > ToolItem {
        height: 1;
        padding: 0;
    }

    ToolBreakdownPanel > .no-data {
        color: $text-muted;
        text-style: italic;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the tool breakdown panel."""
        yield Static("TOOL BREAKDOWN (today)", classes="section-title")
        yield from self._build_tool_items()

    def _build_tool_items(self) -> list[Static]:
        """Build tool item widgets."""
        usage = get_tool_usage_for_date()

        if not usage.tool_counts:
            return [Static("No tool usage today", classes="no-data")]

        top_tools = usage.top_tools(6)
        if not top_tools:
            return [Static("No tool usage today", classes="no-data")]

        max_count = top_tools[0][1] if top_tools else 1

        items = []
        for name, count in top_tools:
            items.append(ToolItem(name, count, max_count))

        return items

    def refresh_tools(self) -> None:
        """Refresh the tool breakdown display."""
        # Remove old items
        for widget in self.query("ToolItem, .no-data"):
            widget.remove()

        # Add new items
        for item in self._build_tool_items():
            self.mount(item)
