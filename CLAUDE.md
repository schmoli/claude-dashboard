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
- Tab navigation with 1-5 keys
- 5 tabs: Overview, Plugins, MCP Servers, Skills, Agents
- Plugins tab with installed plugins list
- MCP Servers tab with configured servers display
- Skills tab with skills grouped by plugin
- Agents tab with user, plugin, and built-in agents
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
