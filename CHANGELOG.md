# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Host resource stats on Overview tab (CPU, memory, disk usage)
- Liveness indicator dots replacing refresh timestamps
- Rich session cards with collapsible stats
- Loading indicator during startup
- Code change detection with status indicator

### Changed

- CI tab renamed to "GitHub" tab, moved to position 2
- Plugins tab: compact table rows instead of cards
- Layout: dashboard-focused redesign
- Header: k9s-style multi-row with stats and logo
- Keyboard: header menu for panel switching
- Header: self-documenting sync indicator

### Removed

- Skills tab
- Agents tab

### Fixed

- Loading screen visibility on startup
- Parent project name detection for worktree sessions
- Hyphenated project names now preserved correctly

## [0.7.0] - 2026-01-18

### Changed

- Complete UI makeover with "Warm Terminal" aesthetic
- Centralized stylesheet (app.tcss) replacing inline DEFAULT_CSS
- Custom theme with Anthropic coral/terracotta branding
- Card-based panel design with rounded borders
- Tab icons using ASCII glyphs (◉ ⬡ ◎ ⚡ ● ◈)

### Added

- `theme.py` with color constants (CORAL, BLUE, GREEN, AMBER, RED)
- Hover states on interactive rows
- Textual scrollbar styling

### Technical

- External CSS via `CSS_PATH` attribute
- Theme registration via `register_theme()` + `self.theme`
- Removed all component DEFAULT_CSS blocks

## [0.6.1] - 2026-01-17

### Added

- TodayHeader widget with big numbers (messages, tools, active count)
- Refresh indicator showing time since last data refresh
- Colored session status: green (active), yellow (idle), dim (inactive)
- Session duration display (Xm, Xh, Xd format)
- Idle session detection (60s-5min since last activity)

## [0.6.0] - 2026-01-17

### Added

- Plugins tab showing installed plugins from ~/.claude/plugins/cache/
- Plugin metadata parsing (name, version, description, source)
- Skills and agents count per plugin
- Sorted plugin list by name

## [0.5.0] - 2026-01-17

### Added

- Tab infrastructure with 5 tabs (Overview, Plugins, MCP, Skills, Agents)
- Keyboard navigation with 1-5 keys to switch tabs
- Placeholder content for unimplemented tabs
- State preserved when switching between tabs

## [0.4.0] - 2026-01-17

### Added

- Tool breakdown panel showing top 6 tools used today
- Horizontal bar chart visualization for tool usage
- Parse tool_use entries from session JSONL files

## [0.3.0] - 2026-01-17

### Added

- Today's message/tool counts in status bar
- Weekly trend sparkline visualization
- Projects ranked by recent activity (top 5)
- Stats panel with trend and project widgets

## [0.2.0] - 2026-01-17

### Added

- Active sessions panel with project name, prompt preview
- Current tool indicator for active sessions
- Session data loading from ~/.claude/projects/
- Active session detection (file mtime within 60s)
- Auto-refresh every 5 seconds

## [0.1.0] - 2026-01-17

### Added

- Initial project skeleton
- Basic Textual app with status bar
- Quit with `q` key
- pytest infrastructure
- direnv auto-venv setup
