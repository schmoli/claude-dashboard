# claude-dash - Claude Code Dashboard Design

> **Status:** Draft - Ready for review
> **Created:** 2026-01-17
> **Author:** Brainstormed with Claude

## Vision

Keyboard-driven TUI for monitoring Claude Code sessions, usage, and configuration. Single-pane-of-glass for all Claude activity on your machine.

**Inspiration:** pdash (Proximia K8s dashboard) - same tech stack, interaction model, and development practices.

## Tech Stack

- **Python 3.11+ / Textual** - Proven stack, agent-friendly
- **pytest** - TDD from iteration 0
- **direnv** - Auto-activate virtualenv on cd
- **Semantic Versioning** - Start at 0.1.0
- **Conventional Commits** - Required for all commits

## Target Users

| User | Needs |
|------|-------|
| Power users | Monitor multiple sessions, see what's running |
| Developers | Track usage patterns, find old sessions |
| Plugin authors | View installed plugins, skills, agents |

---

## Architecture

### Data Sources

All data lives in `~/.claude/`:

| Source | Path | Contains |
|--------|------|----------|
| Sessions | `projects/<project>/sessions-index.json` | Session metadata per project |
| Session logs | `projects/<project>/<uuid>.jsonl` | Full conversation history |
| Stats | `stats-cache.json` | Daily aggregates (msgs, sessions, tools) |
| History | `history.jsonl` | Command history across all sessions |
| Plugins | `plugins/cache/<source>/<name>/<ver>/` | Installed plugins |
| Skills | `plugins/cache/**/skills/*.md` | Skill definitions |
| Agents | `agents/*.md` + `plugins/cache/**/agents/*.md` | Agent definitions |
| MCP | `settings.json` → mcpServers | MCP server configs |
| Debug | `debug/latest` → current session log | Real-time activity |

### Active Session Detection (Multi-Signal)

```python
def detect_active_sessions():
    """Robust detection using multiple signals."""
    signals = []

    # 1. Process detection
    # ps aux | grep claude → running CLI processes with TTY

    # 2. File mtime
    # Session .jsonl modified in last 60s = active

    # 3. Debug symlink
    # ~/.claude/debug/latest → current session UUID

    # 4. Subagent detection
    # <session>/subagents/*.jsonl for parallel agents

    return merge_signals(signals)
```

### High-Level Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ claude-dash │ 3 active │ 847 msgs today │ 142 tool calls       │
├─────────────────────────────────────────────────────────────────┤
│ [Overview] [Plugins] [MCP Servers] [Skills] [Agents]           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                      < tab content >                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ q:quit  1-5:tabs  /:filter  ?:help                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tab Specifications

### Overview Tab (MVP)

Primary real-time monitoring view.

```
┌─────────────────────────────────────────────────────────────────┐
│ ACTIVE SESSIONS                          │ TODAY               │
│ ● dev-dashboard  "brainstorm clau..." │⚙ Bash │ ████████░░ 847  │
│ ● ios-app        "implement auth..."  │📖 Read │ msgs            │
│ ○ keycloak       idle 2h              │        │ ███░░░░░░░ 142  │
│                                          │        │ tools           │
├──────────────────────────────────────────┼─────────────────────┤
│ PROJECTS (by recent activity)            │ WEEKLY TREND        │
│ dev-dashboard    382 msgs │ 12 sessions  │ M T W T F S S       │
│ ios-app          201 msgs │  4 sessions  │ █ █ ▄ █ ▄ ░ ░       │
│ keycloak          89 msgs │  2 sessions  │                     │
│ fido-auth         45 msgs │  1 session   │                     │
├──────────────────────────────────────────┼─────────────────────┤
│ TOOL BREAKDOWN (today)                   │                     │
│ Bash ████████████ 52   Read ██████ 34    │                     │
│ Edit ████ 28           Grep ███ 18       │                     │
│ Write ██ 10            Other █ 8         │                     │
└─────────────────────────────────────────────────────────────────┘
```

**Data refresh:** 5s for active sessions, 30s for aggregates.

### Plugins Tab

```
┌─────────────────────────────────────────────────────────────────┐
│ INSTALLED PLUGINS                                               │
│                                                                 │
│ superpowers          4.0.3   github.com/obra/superpowers        │
│   └─ 12 skills, 1 agent                                         │
│                                                                 │
│ feature-dev          1.0.0   claude-code-plugins                │
│   └─ 3 skills, 3 agents                                         │
│                                                                 │
│ code-review          1.0.0   local (./plugins/code-review)      │
│   └─ 1 skill                                                    │
│                                                                 │
│ swift-lsp            1.0.0   local                              │
│   └─ MCP server only                                            │
└─────────────────────────────────────────────────────────────────┘
```

### MCP Servers Tab

```
┌─────────────────────────────────────────────────────────────────┐
│ MCP SERVERS                                                     │
│                                                                 │
│ ● filesystem     running   stdio   /usr/local/bin/mcp-fs       │
│ ● github         running   stdio   gh-mcp                       │
│ ○ database       stopped   stdio   pg-mcp --host localhost      │
│ ⚠ slack          error     stdio   slack-mcp (auth failed)     │
│                                                                 │
│ Enter: view config   r: restart   s: stop                       │
└─────────────────────────────────────────────────────────────────┘
```

### Skills Tab

```
┌─────────────────────────────────────────────────────────────────┐
│ SKILLS                                    │ DETAIL              │
│                                           │                     │
│ ▼ superpowers (12)                        │ brainstorming       │
│   ● brainstorming                         │ ─────────────────── │
│   ○ test-driven-development               │ Turn ideas into     │
│   ○ systematic-debugging                  │ designs through     │
│   ○ writing-plans                         │ collaborative       │
│   ○ ...                                   │ dialogue.           │
│                                           │                     │
│ ▶ feature-dev (3)                         │ Trigger: /brainstorm│
│ ▶ code-review (1)                         │                     │
│                                           │                     │
│ j/k:navigate  Enter:expand  /:filter      │                     │
└─────────────────────────────────────────────────────────────────┘
```

### Agents Tab

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENTS                                                          │
│                                                                 │
│ User Agents (~/.claude/agents/)                                 │
│   macos-installer              haiku                            │
│                                                                 │
│ Plugin Agents                                                   │
│   superpowers:code-reviewer    inherit                          │
│   feature-dev:code-reviewer    sonnet                           │
│   feature-dev:code-explorer    sonnet                           │
│   feature-dev:code-architect   sonnet                           │
│                                                                 │
│ Built-in Agents                                                 │
│   Bash                         inherit                          │
│   general-purpose              sonnet                           │
│   Explore                      haiku                            │
│   Plan                         inherit                          │
│   claude-code-guide            haiku                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features by Iteration

### Iteration 0: Skeleton + TDD [Foundation]

- [ ] Project structure (pyproject.toml, src layout)
- [ ] direnv setup (.envrc, auto-venv)
- [ ] pytest infrastructure with first test
- [ ] Basic Textual app that launches
- [ ] Status bar with app name
- [ ] Quit with `q`
- [ ] CLAUDE.md with verification workflow

**Ship criteria:**
- `cd claude-dash` auto-activates venv (direnv)
- `pytest tests/ -v` passes (app starts, quits cleanly)
- Can run `python -m cdash`, see status bar, quit with q

**Test (tests/test_app.py):**
```python
async def test_app_starts():
    """App launches without crash."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        assert app.query_one(StatusBar)

async def test_quit():
    """q key quits."""
    app = ClaudeDashApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        assert app.return_code == 0
```

### Iteration 1: Overview - Active Sessions

- [ ] Read sessions-index.json from all projects
- [ ] Detect active sessions (process + mtime signals)
- [ ] Display active sessions list with project, prompt preview
- [ ] Show current activity indicator (tool being used)
- [ ] Auto-refresh every 5s

**Ship criteria:** See your active Claude sessions with live status.

### Iteration 2: Overview - Stats & Trends

- [ ] Parse stats-cache.json for daily aggregates
- [ ] Display today's message/tool counts
- [ ] Weekly trend sparkline
- [ ] Projects ranked by recent activity

**Ship criteria:** At-a-glance usage stats on overview.

### Iteration 3: Overview - Tool Breakdown

- [ ] Parse session JSONL for tool call types
- [ ] Aggregate tool usage for today
- [ ] Horizontal bar chart visualization

**Ship criteria:** See which tools you're using most.

### Iteration 4: Tab Infrastructure

- [ ] Tab widget with keyboard navigation (1-5, Tab)
- [ ] Placeholder content for each tab
- [ ] Preserve state when switching tabs

**Ship criteria:** Can navigate between all 5 tabs.

### Iteration 5: Plugins Tab

- [ ] Scan plugins/cache/ for installed plugins
- [ ] Parse plugin metadata (version, source)
- [ ] Count skills/agents per plugin
- [ ] Display in list format

**Ship criteria:** See all installed plugins with details.

### Iteration 6: MCP Servers Tab

- [ ] Read mcpServers from settings.json
- [ ] Check server process status
- [ ] Display with health indicators
- [ ] Actions: restart, stop (stretch)

**Ship criteria:** See MCP server configs and status.

### Iteration 7: Skills Tab

- [ ] Scan all plugins for skills/*.md
- [ ] Parse skill frontmatter (name, description, trigger)
- [ ] Collapsible tree by plugin
- [ ] Detail panel on select

**Ship criteria:** Browse and search available skills.

### Iteration 8: Agents Tab

- [ ] Scan user agents (~/.claude/agents/)
- [ ] Scan plugin agents
- [ ] Hardcode built-in agents list
- [ ] Display with model info

**Ship criteria:** See all available agents.

### Iteration 9+: Polish

- [ ] Command palette (?)
- [ ] Fuzzy search/filter (/)
- [ ] Session drill-down (Enter on session)
- [ ] Keyboard help overlay
- [ ] Config file support (cdash.yaml)

---

## Project Setup

### Directory Structure

```
claude-dash/
├── .envrc                  # direnv: auto-activate venv
├── .gitignore
├── .python-version         # 3.11+
├── pyproject.toml
├── CHANGELOG.md
├── CLAUDE.md               # Agent instructions
├── README.md
├── docs/
│   └── plans/
│       └── 2026-01-17-claude-dash-design.md
├── src/
│   └── cdash/
│       ├── __init__.py
│       ├── __main__.py     # Entry point
│       ├── app.py          # Main Textual app
│       ├── components/     # Reusable widgets
│       ├── screens/        # Tab screens
│       └── data/           # Data loading/parsing
└── tests/
    ├── conftest.py
    ├── test_app.py
    └── test_data.py
```

### .envrc (direnv)

```bash
# Auto-create and activate venv
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# Install deps if needed
if [ ! -f .venv/.installed ]; then
    pip install -e ".[dev]"
    touch .venv/.installed
fi
```

### pyproject.toml

```toml
[project]
name = "claude-dash"
version = "0.1.0"
description = "TUI dashboard for monitoring Claude Code sessions"
requires-python = ">=3.11"
dependencies = [
    "textual>=0.47.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
]

[project.scripts]
cdash = "cdash.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"
```

---

## Verification Workflow

### Agent Feedback Loop

```bash
# Quick verification (~1 second) - run after any change
pytest tests/ -v

# Visual verification (when UI changes)
pytest tests/test_visual.py -v -s
# Then read the SVG screenshot
```

**When to run:**
- After editing any Python file
- Before committing
- After fixing a bug

### Before Commit Checklist

```
[ ] pytest tests/ -v passes
[ ] Code runs without errors
[ ] Changes match commit message
[ ] No unintended files staged
[ ] Commit follows conventional format
```

---

## Commit Convention

### Format

```
type(scope): short description

- bullet points for details if needed

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Types

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change (no new feature/fix) |
| `docs` | Documentation only |
| `test` | Adding/fixing tests |
| `chore` | Build, tooling, deps |

### Scopes

`app`, `overview`, `plugins`, `mcp`, `skills`, `agents`, `data`, `ui`

---

## CLAUDE.md Template

```markdown
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

\`\`\`bash
# Run the app
python -m cdash

# Run tests (ALWAYS before committing)
pytest tests/ -v

# Format
ruff format src/

# Lint
ruff check src/
\`\`\`

## Verification Loop

After any code change:
1. Run `pytest tests/ -v`
2. If tests fail, fix before proceeding
3. For UI changes, run visual tests and review SVG

## Current State

**Completed iterations:** (none)
**Current iteration:** 0
**Blocking issues:** None

### What's Working

(Nothing yet - iteration 0 not started)

### Next Session Starting Point

1. Read design doc: `docs/plans/2026-01-17-claude-dash-design.md`
2. Implement Iteration 0: Skeleton + TDD
3. Update this section when done

## Conventions

- Semantic Versioning (start at 0.1.0)
- Conventional Commits required
- TDD: write test first when possible
- Keep changes small and focused
- Commit format:
  \`\`\`
  type(scope): description

  Co-Authored-By: Claude <noreply@anthropic.com>
  \`\`\`

## Iteration Checklist (copy for each iteration)

Before marking iteration complete:
- [ ] All spec items implemented
- [ ] Tests written and passing
- [ ] `pytest tests/ -v` passes
- [ ] Committed with conventional commit
- [ ] CLAUDE.md "Current State" updated
- [ ] State update committed
```

---

## Agent Execution Protocol

### Overview

This project is designed for autonomous agent execution. Each iteration can be completed in a single fresh context session (cloud or local). The agent reads state, executes one iteration, commits, and updates state for the next agent.

### State Tracking

**Source of truth:** `CLAUDE.md` contains:
```markdown
## Current State

**Completed iterations:** 0, 1, 2
**Current iteration:** 3
**Blocking issues:** None (or description)
```

### Agent Startup Workflow

When an agent starts a session:

```
1. Read CLAUDE.md → get current iteration number
2. Read docs/plans/2026-01-17-claude-dash-design.md → get iteration spec
3. Verify previous iteration works: pytest tests/ -v
4. If tests fail → fix first, don't proceed to new iteration
5. Implement current iteration following spec
6. Write tests for new functionality
7. Run pytest tests/ -v → must pass
8. Commit with conventional format
9. Update CLAUDE.md: increment "Current iteration", add to "Completed"
10. Commit the state update
```

### Iteration Completion Criteria

An iteration is COMPLETE when:
- [ ] All checklist items from design doc are done
- [ ] New tests written and passing
- [ ] `pytest tests/ -v` passes (all tests, not just new)
- [ ] Committed with proper conventional commit message
- [ ] CLAUDE.md updated with new state
- [ ] State update committed

### Agent Prompt Template

Use this prompt to kick off an iteration (cloud session, ralph loop, etc.):

```
You are continuing development on claude-dash.

1. Read CLAUDE.md to find current iteration
2. Read docs/plans/2026-01-17-claude-dash-design.md for iteration spec
3. Verify tests pass first
4. Implement the current iteration
5. Write tests, ensure all pass
6. Commit with conventional commit
7. Update CLAUDE.md state and commit

Work autonomously. If blocked, document in CLAUDE.md "Blocking issues" and commit.
```

### Ralph Loop Integration

For ralph loop, the iteration-at-a-time model works well:

```bash
# Start ralph loop with iteration focus
/ralph-loop

# Agent will:
# - Check current state
# - Complete one iteration
# - Loop back for next iteration (or stop if blocked)
```

### Cloud Session Handoff

For cloud sessions that complete and you return to:

1. Agent completes iteration, commits, updates CLAUDE.md
2. You return, pull latest: `git pull --rebase`
3. Run `pytest tests/ -v` to verify
4. Start new cloud session for next iteration (or continue locally)

### Recovery from Failed State

If an agent leaves things broken:

```bash
# Check what happened
git log --oneline -5
git status

# If mid-iteration with failing tests
git stash  # or git reset --hard HEAD

# Update CLAUDE.md to reflect actual state
# Add to "Blocking issues" if needed
```

### Iteration Boundaries

Each iteration is designed to be:
- **Completable in ~30-60 min** of agent work
- **Independently testable** - has its own ship criteria
- **Atomic** - either fully done or not done

This prevents half-finished states and makes handoff clean.

---

## Research Notes

### Similar Tools to Investigate

Before implementation, research these for inspiration:

1. **Claude Code's built-in /stats** - What does it show? Can we replicate?
2. **Aider's session tracking** - How do other AI coding tools track usage?
3. **btop/htop** - Layout inspiration for real-time monitoring
4. **lazygit/lazydocker** - TUI interaction patterns

### Questions for Research Phase

- [ ] Does Claude Code expose any undocumented APIs?
- [ ] Can we detect MCP server health programmatically?
- [ ] Is there a way to get token counts from session files?
- [ ] Are there other files in ~/.claude we haven't explored?

---

## Open Questions

- Should we support watching multiple ~/.claude dirs (e.g., for testing)?
- Add session search/history tab later?
- Include Claude.app desktop sessions or CLI only?

---

## Revision Log

| Date | Change |
|------|--------|
| 2026-01-17 | Initial design from brainstorming session |
