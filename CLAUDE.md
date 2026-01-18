# cdash - Claude Development Instructions

## Project Overview

Python + Textual TUI for monitoring Claude Code sessions.
Design doc: `docs/plans/2026-01-17-claude-dash-design.md`

## Agent Workflow (READ THIS FIRST)

Every loop iteration (fresh context):

1. Read this CLAUDE.md → find current iteration
2. Read design doc → get iteration spec
3. Run `pytest tests/ -v` → verify previous work passes
4. If tests fail → fix first, don't start new iteration
5. Implement current iteration (follow spec exactly)
6. Write/update tests
7. Run `pytest tests/ -v` → must pass
8. Commit with conventional commit format
9. Update "Current State" below → increment iteration
10. Commit the state update
11. **If current iteration was 8** → output: `<promise>ALL_ITERATIONS_COMPLETE</promise>`

## Quick Commands

```bash
# Run the app
python -m cdash

# Run tests (ALWAYS before committing)
pytest tests/ -v

# Format
ruff format src/

# Lint
ruff check src/
```

## Verification Loop

After any code change:
1. Run `pytest tests/ -v`
2. If tests fail, fix before proceeding
3. For UI changes, run visual tests and review SVG

## Current State

| Iteration | Name | Status |
|-----------|------|--------|
| 0 | Skeleton + TDD | ✓ |
| 1 | Active Sessions | ✓ |
| 2 | Stats & Trends | ✓ |
| 3 | Tool Breakdown | ✓ |
| 4 | Tab Infrastructure | ✓ |
| 5 | Plugins Tab | ✓ |
| 6 | MCP Servers Tab | ✓ |
| 7 | Skills Tab | ✓ |
| 8 | Agents Tab | ✓ |
| 9 | CI Tab | ✓ |

**Blocking issues:** None

### What's Working
- Basic Textual app skeleton
- Status bar with app name and active session count
- Quit with `q`
- pytest infrastructure
- direnv auto-venv setup
- Session data loading from ~/.claude/projects/
- Active session detection (file mtime within 60s)
- Active sessions panel with project name, prompt preview
- Current tool indicator for active sessions
- Auto-refresh every 10 seconds
- Today's message/tool counts in status bar
- Weekly trend sparkline
- Projects ranked by recent activity
- Tool breakdown with horizontal bar charts
- Tab navigation with 1-6 keys
- 6 tabs: Overview, Plugins, MCP Servers, Skills, Agents, CI
- Plugins tab with installed plugins list
- MCP Servers tab with configured servers display
- Skills tab with skills grouped by plugin
- Agents tab with user, plugin, and built-in agents
- CI tab with GitHub Actions monitoring for claude-code-action repos
- CI activity panel on Overview tab with today's run stats
- Settings persistence for discovered/hidden repos
- Session/tool data caching for performance

## Conventions

- Semantic Versioning (start at 0.1.0)
- Conventional Commits required (also on per title)
- Coco style branch naming: 'feat/feature-name' or 'fix/bug-description' or 'docs/plan-name'
- TDD: write test first when possible
- Keep changes small and focused
- Commit format:
  ```
  type(scope): description

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

## Iteration Checklist (copy for each iteration)

Before marking iteration complete:
- [ ] All spec items implemented
- [ ] Tests written and passing
- [ ] `pytest tests/ -v` passes
- [ ] Committed with conventional commit
- [ ] CLAUDE.md "Current State" updated
- [ ] CHANGELOG.md updated with new version and changes
- [ ] State update committed

## Ralph Loop Completion

When iteration 8 is complete and committed:
1. Verify all tests pass
2. Verify CLAUDE.md shows iteration 8 as ✓
3. Output exactly: `<promise>ALL_ITERATIONS_COMPLETE</promise>`

This stops the ralph-loop. Do NOT output the promise until iteration 8 is truly done.

## Textual Learnings

### Widget Types

- `Static` = leaf widget, renders content, no children
- `Vertical`/`Horizontal`/`Container` = layout widgets with children
- Don't extend `Static` and use `compose()` - use a container instead

### Bindings

- Format: `("key", "action_name", "Description")`
- Three elements only, not four
- Method: `action_{name}(self)`

### Testing

- Use `async with app.run_test() as pilot:` for tests
- `await pilot.press("q")` to simulate key presses
- `app.query_one(Widget)` to find widgets

## Parallel Development with Worktrees

Use git worktrees to develop multiple issues in parallel without context switching.

### Directory Structure

```
.worktrees/
  123/          # Issue #123 worktree
    ISSUE.md    # Generated task instructions
    .venv -> ../../.venv  # Symlinked venv
  456/          # Issue #456 worktree
```

### Creating a Worktree from Issue

```bash
# Fetch issue details
gh issue view 123 --json number,title,body

# Create worktree on fresh branch from origin/main
git fetch origin main
git worktree add -b toli/fix/session-detection .worktrees/123 origin/main

# Symlink venv (faster than recreating)
ln -s ../../.venv .worktrees/123/.venv

# Generate ISSUE.md with context (see template below)
```

### ISSUE.md Template

Write to `.worktrees/<num>/ISSUE.md`:

```markdown
# <type>(<scope>): <title from issue>

Issue: #<number>
Branch: toli/<type>/<slug>
URL: <issue url>

## Problem
<body from gh issue view>

## Instructions
1. Read `../../CLAUDE.md` for project conventions
2. `pytest tests/ -v` - baseline must pass
3. Implement fix
4. Write/update tests
5. `pytest tests/ -v` - must pass
6. Commit: `<type>(<scope>): description`
7. Create PR: `gh pr create --title "..." --body "Fixes #<number>"`
```

### Running Background Agent (Simple Tasks)

```bash
claude --dir .worktrees/123 --print "
Read ISSUE.md for your task.
Follow instructions in ../../CLAUDE.md.
Run pytest, implement fix, run pytest again.
Commit with conventional format.
Create PR with: gh pr create --title '...' --body 'Fixes #123'
" &
```

### Running Guided Session (Complex Tasks)

```bash
# Set up worktree as above, then:
echo "Worktree ready at .worktrees/456"
echo "Run: cd .worktrees/456 && claude"
```

### Checking Status

```bash
# List active worktrees
git worktree list

# Check PR status
gh pr list --state open

# View specific PR
gh pr view --web
```

### Cleanup After Merge

```bash
# Remove worktree and branch for merged PR
git worktree remove .worktrees/123
git branch -d toli/fix/session-detection

# Or prune all stale worktrees
git worktree prune
```

### Branch Naming

- `toli/fix/<slug>` - bug fixes
- `toli/feat/<slug>` - new features
- `toli/docs/<slug>` - documentation
- `toli/refactor/<slug>` - refactoring

### PR/Issue Titles

Use conventional commit format:
- `fix(sessions): detect active sessions on macOS`
- `feat(ci): add GitHub Actions monitoring`
