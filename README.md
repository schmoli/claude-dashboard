# claude-dashboard

TUI dashboard for monitoring Claude Code sessions, plugins, and usage.

## Features

- Real-time session monitoring
- Usage trends and statistics
- Plugin/skill/agent catalog
- MCP server status

## Installation

```bash
# Clone and cd
git clone https://github.com/schmoli/claude-dashboard.git
cd claude-dashboard

# direnv will auto-setup venv (or manually):
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
cdash
```

## Development

```bash
# Run tests
pytest tests/ -v

# Format
ruff format src/

# Lint
ruff check src/
```

## License

MIT
