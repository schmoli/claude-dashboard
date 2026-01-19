# Session Card Redesign - Multi-Line Action History

> **Status:** Design proposal
> **Created:** 2026-01-19
> **Goal:** Richer session cards showing recent command history

## Problem Statement

The current session card is ultra-compact (2 lines):
```
● project@branch ACT ⏱5m 12/48 ⚙Read
"prompt preview..."
```

This only shows the **current** tool being executed. Users want to see:
- What's happening **now**
- What **just happened** (previous 2 commands)
- Better use of available vertical space

## Design Options

### Option A: Action History Timeline (Recommended)

Expand each card to show the last 3 tool executions with context:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ● claude-dashboard@main                          ACT  ⏱2h  140m/116t   │
│   "Implement the following plan: # Plan: Enrich Header Layout..."      │
│ ─────────────────────────────────────────────────────────────────────── │
│   ⚙ Bash   cd /Users/toli/code/schmoli/claude-dashb...                 │
│   ⚙ Read   /home/user/claude-dashboard/src/cdash/components/sessions.py│
│   ⚙ Edit   /home/user/claude-dashboard/CLAUDE.md                       │
└─────────────────────────────────────────────────────────────────────────┘
```

**Layout (5-6 lines per card):**
- Line 1: Header - status, project, branch, badge, duration, stats
- Line 2: Prompt preview (full width)
- Line 3: Separator
- Lines 4-6: Recent tools with context (newest first)

**Pros:**
- Shows momentum/progress
- Context for each tool (file path, command)
- Natural reading order (newest action visible first)

**Cons:**
- Takes more vertical space (but we have room)

---

### Option B: Compact Inline History

Keep 3-line format but show tool history inline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ● claude-dashboard@main  ACT  ⏱2h  140m/116t                           │
│   "Implement the following plan: # Plan: Enrich Header..."             │
│   ⚙ Bash → Read → Edit                                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Minimal space increase
- Quick glance at tool sequence

**Cons:**
- No context (what files? what commands?)
- Hard to see patterns

---

### Option C: Tool Details on Hover/Focus

Keep compact card, show expanded details when focused:

```
# Unfocused:
│ ● claude-dashboard@main  ACT  ⏱2h  140m/116t  ⚙Bash                    │
│   "Implement the following plan..."                                     │

# Focused (Enter or arrow key):
│ ● claude-dashboard@main  ACT  ⏱2h  140m/116t                           │
│   "Implement the following plan: # Plan: Enrich Header Layout..."      │
│ ─────────────────────────────────────────────────────────────────────── │
│   ⚙ Bash   cd /Users/toli/code/schmoli/claude-dashb...                 │
│   ⚙ Read   /home/user/claude-dashboard/src/cdash/components/sessions.py│
│   ⚙ Edit   /home/user/claude-dashboard/CLAUDE.md                       │
│ ─────────────────────────────────────────────────────────────────────── │
│   Enter: open session   Esc: collapse                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Best of both worlds
- Interactive exploration
- Keeps overview clean when multiple sessions

**Cons:**
- More complex to implement
- Requires user interaction to see details

---

## Recommended Design: Option A

Given the screenshot shows a single session taking minimal space on a large display, Option A provides the best balance:

### Visual Mockup

**Current (cramped):**
```
│ ● worktrees@main                                  ACT  ⏱3h  140m/116t  │
```

**Expanded header options:**

**Option H1: Full labels with breathing room**
```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● ACTIVE   claude-dashboard  main         3 hours   140 msgs • 116 tools│
├─────────────────────────────────────────────────────────────────────────┤
│   "Implement the following plan: # Plan: Enrich Header Layout ## G..." │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   ⚙ Bash    cd /Users/toli/code/schmoli/claude-dashb...        now    │
│   📖 Read    src/cdash/components/sessions.py                    2m    │
│   ✏️ Edit    CLAUDE.md                                            5m    │
╰─────────────────────────────────────────────────────────────────────────╯
```

**Option H2: Two-line header with host stats**
```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● ACTIVE   claude-dashboard                                             │
│   main • 3 hours • 140 messages • 116 tools           CPU 12%  MEM 2.1G │
├─────────────────────────────────────────────────────────────────────────┤
│   "Implement the following plan: # Plan: Enrich Header Layout ## G..." │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   ⚙ Bash    cd /Users/toli/code/schmoli/claude-dashb...        now    │
│   📖 Read    src/cdash/components/sessions.py                    2m    │
│   ✏️ Edit    CLAUDE.md                                            5m    │
╰─────────────────────────────────────────────────────────────────────────╯
```

**Option H3: Structured with visual hierarchy**
```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● claude-dashboard                                              ACTIVE  │
│   branch: main   duration: 3 hours   messages: 140   tools: 116        │
├─────────────────────────────────────────────────────────────────────────┤
│   "Implement the following plan: # Plan: Enrich Header Layout ## G..." │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   ⚙ Bash    cd /Users/toli/code/schmoli/claude-dashb...        now    │
│   📖 Read    src/cdash/components/sessions.py                    2m    │
│   ✏️ Edit    CLAUDE.md                                            5m    │
╰─────────────────────────────────────────────────────────────────────────╯
```

**Option H4: Clean minimal with full project path visibility**
```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● ACTIVE                                                                │
│   claude-dashboard (main)                      3h 12m • 140m • 116t     │
│   ~/code/schmoli/claude-dashboard                                       │
├─────────────────────────────────────────────────────────────────────────┤
│   "Implement the following plan: # Plan: Enrich Header Layout ## G..." │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   ⚙ Bash    cd /Users/toli/code/schmoli/claude-dashb...        now    │
│   📖 Read    src/cdash/components/sessions.py                    2m    │
│   ✏️ Edit    CLAUDE.md                                            5m    │
╰─────────────────────────────────────────────────────────────────────────╯
```

**Option H5: Rich two-line header with GitHub + context usage (RECOMMENDED)**
```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● claude-dashboard                       schmoli/claude-dashboard  ACTIVE│
│   ~/code/schmoli/claude-dashboard        main • 3h 12m   ████████░░ 82% │
├─────────────────────────────────────────────────────────────────────────┤
│   "Implement the following plan: # Plan: Enrich Header Layout ## G..." │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   ⚙ Bash    cd /Users/toli/code/schmoli/claude-dashb...        now    │
│   📖 Read    src/cdash/components/sessions.py                    2m    │
│   ✏️ Edit    CLAUDE.md                                            5m    │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   140 messages • 116 tools                                              │
╰─────────────────────────────────────────────────────────────────────────╯
```

**H5 Breakdown:**
```
Line 1: ● claude-dashboard                       schmoli/claude-dashboard  ACTIVE
        │ └─ project name (full)                 └─ GitHub repo            └─ status
        └─ status indicator

Line 2:   ~/code/schmoli/claude-dashboard        main • 3h 12m   ████████░░ 82%
          └─ full path                           │      │        └─ context bar + %
                                                 │      └─ duration
                                                 └─ branch
```

**Alternative H5 layouts:**

**H5a: Context bar with token count**
```
│ ● claude-dashboard                       schmoli/claude-dashboard  ACTIVE│
│   main • 3h 12m • 140m • 116t            ████████░░ 164k/200k tokens    │
```

**H5b: Percentage emphasis**
```
│ ● claude-dashboard                       schmoli/claude-dashboard  ACTIVE│
│   ~/code/schmoli/claude-dashboard  main   3h 12m   Context: 82% ████████░│
```

**H5c: Compact stats row**
```
│ ● claude-dashboard                       schmoli/claude-dashboard  ACTIVE│
│   main  3h  140m  116t  ████████░░ 82%   ~/code/schmoli/claude-dashboard│
```

### Context Size Tracking

**How to estimate context usage:**
- Count total characters in session JSONL
- Estimate tokens: `chars / 4` (rough average)
- Calculate percentage: `estimated_tokens / 200_000 * 100`
- Display as progress bar + percentage

**Visual options for context bar:**
```
████████░░ 82%           # 10-char bar + percentage
████████████████░░░░ 80% # 20-char bar (more granular)
▓▓▓▓▓▓▓▓░░ 164k/200k     # With token counts
Context: 82% [████████░░] # Labeled
```

**Color coding:**
- Green (`$success`): < 50%
- Yellow (`$warning`): 50-80%
- Red (`$error`): > 80%

### GitHub Repo Detection

**How to detect GitHub repo:**
1. Check for `.git/config` in project path
2. Parse remote URL: `git config --get remote.origin.url`
3. Extract `owner/repo` from:
   - `git@github.com:owner/repo.git`
   - `https://github.com/owner/repo.git`
4. Cache result per project path

**Display options:**
```
schmoli/claude-dashboard     # owner/repo
github.com/schmoli/claude-   # with domain (truncated)
 schmoli/claude-dashboard   # with GitHub icon
```

### Header Element Expansion

| Current | Expanded | Notes |
|---------|----------|-------|
| `●` | `● ACTIVE` | Status as word |
| `worktrees` | `claude-dashboard` | Full project name |
| `@main` | `main` or `branch: main` | Separate or labeled |
| `ACT` | `ACTIVE` / `IDLE 2m` | Full word + idle duration |
| `⏱3h` | `3 hours` or `duration: 3h` | Readable or labeled |
| `140m/116t` | `140 msgs • 116 tools` | Full words, separator |

### Recommended: Option H6e

**H6e** - GitHub/project as title, branch prominent, stats in footer:

```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● schmoli/claude-dashboard                                       ACTIVE │
│   claude/redesign-sessions-card-HUk0Z                   3h   ██████░░ 82%│
├─────────────────────────────────────────────────────────────────────────┤
│   "Implement the following plan: # Plan: Enrich Header Layout ## G..." │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   ⚙ Bash    cd /Users/toli/code/schmoli/claude-dashb...        now    │
│   📖 Read    src/cdash/components/sessions.py                    2m    │
│   ✏️ Edit    CLAUDE.md                                            5m    │
│ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
│   140 msgs • 116 tools                        ~/code/schmoli/claude-da…│
╰─────────────────────────────────────────────────────────────────────────╯
```

**Fallback when no GitHub repo (uses project name instead):**
```
╭─────────────────────────────────────────────────────────────────────────╮
│ ● my-local-project                                               ACTIVE │
│   feature/long-branch-name-here                         3h   ██████░░ 82%│
├─────────────────────────────────────────────────────────────────────────┤
```

**H6e Breakdown:**
```
Line 1: ● schmoli/claude-dashboard                                 ACTIVE
        │ └─ GitHub repo (or project name if no repo)              └─ status
        └─ status indicator

Line 2:   claude/redesign-sessions-card-HUk0Z             3h   ██████░░ 82%
          └─ branch (up to ~40 chars)                     │    └─ context bar
                                                          └─ duration

Footer:   140 msgs • 116 tools                  ~/code/schmoli/claude-da…
          └─ message & tool counts              └─ path (truncated from right)
```

**Why H6e:**
- **Title priority:** GitHub repo supersedes project name (identifies codebase in forks/worktrees)
- **Branch prominence:** ~40 chars for long feature branch names
- **Context bar:** Critical for knowing when approaching 200k limit
- **Stats in footer:** Keeps header clean, groups related info with path
- **Path in footer:** Available but de-prioritized (truncated if needed)

### Data Requirements

The `Session` dataclass already has:
- `recent_tools: list[str]` - last 5 tools used
- `project_path: str` - full path to project

We need to enhance to store:
```python
@dataclass
class ToolCall:
    """A single tool invocation with context."""
    tool_name: str          # "Bash", "Read", "Edit", etc.
    context: str            # file path, command, or pattern
    timestamp: datetime     # when it was called

@dataclass
class Session:
    # ... existing fields ...

    # Tool history (enhanced)
    recent_tool_calls: list[ToolCall]  # Last N tool calls with context

    # GitHub integration (new)
    github_repo: str | None           # "owner/repo" extracted from git remote

    # Context tracking (new)
    context_chars: int                # Total characters in session JSONL
    context_tokens_estimate: int      # chars / 4 (rough estimate)
    context_percentage: float         # tokens / 200_000 * 100
```

### New Data: GitHub Repo

```python
def get_github_repo(project_path: str) -> str | None:
    """Extract owner/repo from git remote."""
    git_config = Path(project_path) / ".git" / "config"
    if not git_config.exists():
        return None

    # Parse [remote "origin"] url = ...
    # Handle: git@github.com:owner/repo.git
    #         https://github.com/owner/repo.git

    import re
    config_text = git_config.read_text()

    # SSH format
    match = re.search(r'git@github\.com:([^/]+)/([^.]+)\.git', config_text)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    # HTTPS format
    match = re.search(r'github\.com/([^/]+)/([^.]+)\.git', config_text)
    if match:
        return f"{match.group(1)}/{match.group(2)}"

    return None
```

### New Data: Context Size

```python
def estimate_context_size(session_path: Path) -> tuple[int, int, float]:
    """Estimate context usage from session JSONL size."""
    if not session_path.exists():
        return 0, 0, 0.0

    # Get total characters (file size is close enough)
    chars = session_path.stat().st_size

    # Rough token estimate (4 chars per token average)
    tokens = chars // 4

    # Percentage of 200k context window
    percentage = min(100.0, (tokens / 200_000) * 100)

    return chars, tokens, percentage
```

### Tool Context Extraction

| Tool | Context to Display |
|------|-------------------|
| Bash | Command (first 60 chars) |
| Read | File path (relative if possible) |
| Edit | File path |
| Write | File path |
| Grep | Pattern + path |
| Glob | Pattern |
| Task | Description |
| WebFetch | URL |
| WebSearch | Query |

### Tool Icons (Optional Enhancement)

```
⚙  Bash      (gear - executing)
📖 Read      (book - reading)
✏️  Edit      (pencil - editing)
📝 Write     (document - writing)
🔍 Grep      (magnifier - searching)
📁 Glob      (folder - finding files)
🤖 Task      (robot - agent)
🌐 WebFetch  (globe - web)
🔎 WebSearch (search - web search)
```

### CSS Styling

```css
SessionCard {
    height: auto;
    min-height: 5;
    max-height: 8;
    padding: 0 1;
    background: $surface;
    border-left: thick $surface;
    margin-bottom: 1;
}

SessionCard.active {
    border-left: thick $success;
}

SessionCard.idle {
    border-left: thick $warning;
}

.session-header {
    height: 1;
}

.session-prompt {
    height: 1;
    color: $text-muted;
}

.session-divider {
    height: 1;
    color: $text-muted;
}

.tool-history {
    height: auto;
    max-height: 3;
}

.tool-entry {
    height: 1;
}

.tool-name {
    width: 10;
    color: $primary;
}

.tool-context {
    color: $text;
}

.tool-age {
    width: 6;
    text-align: right;
    color: $text-muted;
}
```

### Relative Time Display

Show tool recency:
- `now` - within last 10 seconds
- `30s` - seconds ago
- `2m` - minutes ago
- `1h` - hours ago

---

## Implementation Plan

### Phase 1: Data Layer
1. Add `ToolCall` dataclass with name, context, timestamp
2. Update `parse_session_file()` to extract last 3 tool calls with context
3. Add `recent_tool_calls` to `Session` dataclass

### Phase 2: Widget Update
1. Modify `SessionCard` to use new 5-6 line layout
2. Add `_render_tool_history()` method
3. Update CSS for new structure

### Phase 3: Polish
1. Add tool icons (optional)
2. Tune truncation lengths for different terminal widths
3. Add focus expansion (Option C as enhancement)

---

## Alternatives Considered

### Stacked Tool Badges
```
● project@main  ACT  ⏱2h  [Bash][Read][Edit]
```
**Rejected:** No context, just names

### Activity Sparkline
```
● project@main  ACT  ▁▂▅█▇▅▂▁  12/48
```
**Rejected:** Shows activity frequency, not what's happening

### Full Log Stream
```
│ 14:32:05  Bash: cd /path/to/project
│ 14:32:08  Read: src/app.py
│ 14:32:12  Edit: src/app.py:45
```
**Rejected:** Too verbose, better for dedicated session detail view

---

## Questions

1. **How many tools to show?** Recommend 3 (current + 2 previous)
2. **Relative paths?** Yes, relative to project root when possible
3. **Truncation?** 50-60 chars for context, with `...`
4. **Time format?** Relative (now, 2m, 5m) not absolute

---

## Revision Log

| Date | Change |
|------|--------|
| 2026-01-19 | Initial design from user request |
