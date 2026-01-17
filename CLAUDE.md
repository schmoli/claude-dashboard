# cdash - Claude Development Instructions

## Project Overview

Python + Textual TUI for monitoring Claude Code sessions.
Design doc: `docs/plans/2026-01-17-claude-dash-design.md`

## Agent Workflow (READ THIS FIRST)

If you are an agent starting a fresh session:

1. Check "Current State" below for which iteration to work on
2. Read the design doc for that iteration's spec
3. Run `pytest tests/ -v` to verify previous work
4. Implement the iteration (follow spec exactly)
5. Write/update tests
6. Commit with conventional commit format
7. Update "Current State" below and commit

**IMPORTANT:** One iteration per session. Update state before ending.

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

**Completed iterations:** 0, 1
**Current iteration:** 2
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
- Auto-refresh every 5 seconds

### Next Session Starting Point

1. Read design doc: `docs/plans/2026-01-17-claude-dash-design.md`
2. Implement Iteration 2: Overview - Stats & Trends
3. Update this section when done

## Conventions

- Semantic Versioning (start at 0.1.0)
- Conventional Commits required
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
- [ ] State update committed

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
