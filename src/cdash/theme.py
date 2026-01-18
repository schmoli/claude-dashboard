"""Claude Dashboard theme - Warm Terminal aesthetic.

Anthropic coral/terracotta branding merged with sophisticated terminal aesthetic.
"""

from textual.design import ColorSystem
from textual.theme import Theme

# Color constants for use in Rich markup
CORAL = "#D97757"  # Primary accent
BLUE = "#6A9BCC"  # Secondary
GREEN = "#788C5D"  # Success
AMBER = "#E5B567"  # Warning
RED = "#CC6666"  # Error/danger
TEXT = "#E8E6DC"  # Warm white text
TEXT_MUTED = "#B0AEA5"  # Mid gray
BG = "#1A1918"  # Deep charcoal
SURFACE = "#252422"  # Elevated surface
PANEL = "#302E2B"  # Card background

# Nerd Font icons for tabs
TAB_ICONS = {
    "overview": "\uf56e",  # 󰕮 dashboard
    "plugins": "\uf03d7",  # 󰏗 package (using fallback)
    "mcp": "\uf048b",  # 󰒋 server (using fallback)
    "skills": "\uf0e7",  # lightning bolt
    "ci": "\uf09b",  # github
}

# Fallback ASCII icons if Nerd Fonts not available
TAB_ICONS_ASCII = {
    "overview": "◉",
    "plugins": "⬡",
    "mcp": "◎",
    "skills": "⚡",
    "ci": "◈",
}


def create_claude_theme() -> Theme:
    """Create the Claude Dashboard theme with warm terminal colors."""
    return Theme(
        name="claude",
        primary=CORAL,
        secondary=BLUE,
        warning=AMBER,
        error=RED,
        success=GREEN,
        accent=CORAL,
        dark=True,
        luminosity_spread=0.15,
        text_alpha=0.95,
        variables={
            "text": TEXT,
            "text-muted": TEXT_MUTED,
            "background": BG,
            "surface": SURFACE,
            "panel": PANEL,
            "primary-darken-1": "#C46647",
            "primary-darken-2": "#A85539",
            "primary-darken-3": "#8C4730",
            "border": "#404040",
            "border-subtle": "#333333",
        },
    )


# Color system for direct use in Rich markup
COLORS = ColorSystem(
    primary=CORAL,
    secondary=BLUE,
    warning=AMBER,
    error=RED,
    success=GREEN,
    accent=CORAL,
    dark=True,
)
