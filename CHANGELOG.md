# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
