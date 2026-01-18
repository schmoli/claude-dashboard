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

## Parallel Development with Worktrees

Work on multiple issues simultaneously using git worktrees:

```bash
# Create worktree for issue #123
gh issue view 123 --json number,title,body
git fetch origin main
git worktree add -b toli/fix/bug-name .worktrees/123 origin/main
ln -s ../../.venv .worktrees/123/.venv

# Run background agent (simple tasks)
claude --dir .worktrees/123 --print "Read ISSUE.md, log to STATUS.md, implement, test, commit, PR" \
  2>&1 | tee .worktrees/123/agent.log &

# Monitor progress
tail -f .worktrees/123/STATUS.md  # agent checkpoints
tail -f .worktrees/123/agent.log  # full output

# Or guided session (complex tasks)
cd .worktrees/123 && claude

# Check status
cat .worktrees/123/STATUS.md
gh pr list --state open

# Cleanup after merge
git worktree remove .worktrees/123
```

See `CLAUDE.md` for full workflow details and ISSUE.md template.

## License

MIT
