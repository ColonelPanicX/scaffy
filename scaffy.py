#!/usr/bin/env python3
"""
Self-contained initializer for multi-agent project scaffold.

Usage:
    python scaffy.py [--name NAME] [--path PATH] [--force] [--dry-run]
                     [--governance MODE] [--platform PLATFORM] [--license LICENSE]
                     [--init-git] [--description TEXT]
    python scaffy.py --upgrade [--path PATH] [--force] [--dry-run]
    python scaffy.py --save-chat [--path PATH] [--session-id UUID] [--cli {claude,codex,gemini}]
    python scaffy.py --list-chats [--path PATH] [--cli {claude,codex,gemini}]

If --name and --path are both provided, runs without interactive prompts.
Otherwise uses interactive menus for mode/target/governance selection.

Options:
  --name NAME          Project name (lowercase, hyphen-separated).
  --path PATH          Target directory where scaffold files will be installed.
                       For --upgrade: the project root (defaults to current directory).
  --force              Overwrite existing files.
  --dry-run            Show planned actions and exit without writing anything.
  --governance MODE    Governance mode: lightweight, standard, or strict. Default: standard.
  --platform PLATFORM  Git platform: github, gitlab, or none. Default: none.
  --license LICENSE    License to generate: mit, apache-2.0, gpl-3.0, agpl-3.0,
                       bsd-2-clause, bsd-3-clause, mpl-2.0, unlicense, or none. Default: none.
  --upgrade            Upgrade an existing .collab/ scaffold to the latest templates.
  --init-git           Run git init in the project root after scaffolding.
  --description TEXT   Short project description injected into context.md.

Conventions:
- Timezone: America/New_York. Dates use MM.DD.YYYY (no times).
- Names: lowercase, hyphen-separated.
"""

from __future__ import annotations

import sys
if sys.version_info < (3, 9):
    sys.exit("scaffy requires Python 3.9+")

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    TZ = ZoneInfo("America/New_York")
except KeyError:
    print(
        "Warning: timezone data not found. Dates will use UTC.\n"
        "On Windows, run `pip install tzdata` to fix this.",
        file=sys.stderr,
    )
    TZ = timezone.utc

__version__ = "1.9.0"

GOVERNANCE_MODES = ("none", "lightweight", "standard", "strict")
PLATFORM_MODES = ("github", "gitlab", "azure-devops", "none")
LICENSE_CHOICES = ("mit", "apache-2.0", "gpl-3.0", "agpl-3.0", "bsd-2-clause", "bsd-3-clause", "mpl-2.0", "unlicense", "none")


class BackSignal(Exception):
    """User typed 'b' — go back one step in the wizard."""


class QuitSignal(Exception):
    """User typed 'q' — quit the program."""


_ABORT = object()     # sentinel: user declined to proceed at confirm
_CONFIRMED = object() # sentinel: user confirmed at confirm


def now_tz() -> datetime:
    return datetime.now(tz=TZ)


# ---------------------------------------------------------------------------
# Templates — always written
# ---------------------------------------------------------------------------

TEMPLATE_FILES: dict[str, str] = {
    ".gitignore": """\
# AI Agent Directories (per-machine, not for version control)
.claude/
.codex/
.gemini/

# Collaboration Workspace (internal AI artifacts — not for version control)
.collab/

# OS Files
.DS_Store
Thumbs.db
*Zone.Identifier*

# Editor / IDE
.vscode/
.idea/
*.swp
*.swo

# Local environment secrets
.env
.env.*
!.env.example

# Logs
*.log

# Python (common even in mixed repos)
__pycache__/
*.py[cod]

# Node (very common even in non-node repos due to tooling)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Python tooling
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
""",

    ".collab/readme.md": """\
# Collaboration Workspace

Everything AI agents need lives inside this `.collab/` directory.

## About `.collab/`

This directory contains internal AI agent collaboration artifacts (session summaries,
kanban board, contracts, etc.).

**`.collab/` is intentionally excluded from version control** (listed in `.gitignore`).
It exists only on your local machine.

If you want to share `.collab/` contents with someone else, do so out-of-band
(e.g., zip the folder and send it directly). Do not force-add it to git.

## Quick Start

- All agents: read `collab-contract.md`, `kanban-board.md`, and `context.md` before acting.
- If the kanban board is empty, treat the project as newly initialized and wait for the user
  to describe goals before drafting plans or tasks.
- Start your first session by pasting the contents of `prompts/initial-prompt.md`.
- Use `OPEN SESSION` at the start of each working session to resume context quickly.
- Use `SAVE SESSION` mid-session to checkpoint progress without ending the session.
- Use `CLOSE SESSION` at the end of each session to save progress.
- Use `SAVE CHAT` to export the full session transcript to `chat-logs/`.
- Write session summaries to `session-summaries/` on close.
- Keep `kanban-board.md` current — it is the internal source of truth for task status.
- Use `brainstorms/` to workshop pre-ticket concepts. See `collab-contract.md` for agent behavior rules.

## Directory Structure

- `collab-contract.md` — Rules, conventions, and logging requirements.
- `kanban-board.md` — Task tracking (internal source of truth).
- `context.md` — Stable project facts: tech stack, key files, conventions, dependencies.
- `project.yaml` — Machine-readable project metadata (name, date, governance mode, agents).
- `session-summaries/` — Session summaries from all agents.
  Naming:
  - First summary of the day: `MM.DD.YYYY-agentname-summary.md`
  - Additional same-day summaries: `MM.DD.YYYY-##-agentname-summary.md`
    (use zero-padded sequence like `02`, `03`, etc.)
- `chat-logs/` — Full session transcripts exported via `SAVE CHAT`.
  Naming: `MM.DD.YYYY-claude-chat.md` (or `MM.DD.YYYY-##-claude-chat.md` for multiple per day).
- `brainstorms/` — Thinking space for pre-ticket concepts and proposals.
  - `brainstorm-template.md` — Starter template for new brainstorm files.
- `project-plans/` — Structured plans bridging brainstormed ideas and kanban execution.
  - `project-plan-template.md` — Starter template for new plan files.
- `audit/` — Analysis reports, planning documents, and progress tracking artifacts.
- `supporting-artifacts/` — Adjacent project materials: diagrams, research notes, specs,
  reference docs, exported data, and anything else that supports the work but isn't
  source code. Keep the project root clean — if it belongs to the project but isn't
  code, it probably belongs here.
- `prompts/` — Reusable agent prompts and supporting inputs.
  - `initial-prompt.md` — First-session onboarding prompt (paste on first launch).
  - `agent-profile.md` — Fill-in questionnaire for generating agent instruction files.
  - `agent-md-prompt.md` — Prompt to generate CLAUDE.md / AGENTS.md from the profile.
- `guides/` — Reference documents explaining the *why* behind project conventions.
  - `git-guidelines.md` — Git governance modes, branching strategy, label taxonomy, platform notes.
- `playbooks/` — Step-by-step procedures for common operations.
  - `coding-playbook.md` — General coding standards and best practices.
  - `git-governance-lightweight.md` / `git-governance-standard.md` / `git-governance-strict.md` — Execution playbooks per governance mode.
  - `templates/` — Fill-in-the-blank forms: `issue-template.md`, `pull-request-template.md`.

## Supporting Artifacts Guidance

Use `supporting-artifacts/` for anything adjacent to the project that isn't source code,
config, or documentation that belongs in the repo. The goal is to keep the project root
clean and consolidate everything the AI and user need in one place.

Examples of what belongs here:
- Architecture diagrams and wireframes
- Research notes, vendor comparisons, and technical spikes
- Specification drafts and design documents
- Reference material, exports, and sample data
- Scratch files and working notes from active sessions

Conventions:
- Filenames should be lowercase, hyphen-separated.
- Subdirectories are encouraged for organization (e.g., `diagrams/`, `specs/`, `research/`).
- Prefix date when time-sensitive: `MM.DD.YYYY-filename.md`

## Brainstorm Directory Guidance

Use `brainstorms/` for concepts that aren't ready to be formal tickets yet — brain dumps, half-formed
proposals, things worth thinking through before committing to a sprint.

Workflow:
- Create one file per idea cluster, named descriptively (e.g., `better-onboarding.md`).
- Use `brainstorm-template.md` as a starting point.
- Workshop ideas with an agent: ask for honest feedback, capture the discussion in the
  **Discussion Log** section of the file so context isn't lost when the session closes.
- When an idea is ready to become a ticket, note it at the bottom of the file and graduate it
  to your issue tracker. Leave the file in place as a record.
- Ideas that don't go anywhere can be left as `parked` — they might be useful later.

## Project Plans Directory Guidance

Use `project-plans/` for work that has moved past the "is this a good idea?" stage but isn't
ready to be sprint tasks yet. Plans define the goal, phases, and tasks before anything hits the board.

Workflow:
- Create one file per initiative, named descriptively (e.g., `auth-refactor.md`).
- Use `project-plan-template.md` as a starting point.
- Work with an agent to fill out phases and surface risks. Capture decisions in the file itself.
- When a phase is approved for execution, promote its tasks to `kanban-board.md` and note the
  date at the bottom of the plan file.
- Plans that are complete or cancelled can be marked `archived` — leave them in place as a record.

## Audit Directory Guidance

Use `audit/` for durable project artifacts that support traceability.

Intended contents:
- Analysis reports (technical assessments, gap analyses, code reviews)
- Planning documents (implementation plans, architecture decisions, remediation strategies)
- Progress tracking (milestone snapshots, completion metrics, status notes)

Conventions:
- Filenames should be lowercase, hyphen-separated.
- Prefix date when time-sensitive: `MM.DD.YYYY-report-name.md`
- Keep content factual and link to source files rather than duplicating large excerpts.

## Conventions

- Timezone: America/New_York. Dates use `MM.DD.YYYY` (no times).
- Filenames: lowercase, hyphen-separated.
- Avoid destructive commands unless explicitly approved.
""",

    ".collab/collab-contract.md": """\
# Collaboration Contract

- **Purpose**: Guarantee predictable multi-agent coordination, logging, and auditability.
  Agents are aware of one another and coordinate through shared artifacts in `.collab/`.
- **Timezone**: America/New_York. All dates use `MM.DD.YYYY` (no times).
- **Naming**: All files/dirs lowercase, hyphen-separated.
- **Task Board**: `.collab/kanban-board.md` is the single source of truth for task status.
  Read it plus the latest session summaries before acting.
  If the board is empty, treat the project as newly initialized and wait for user input.

---

## Permissions & Guardrails

These apply to **all agents**.

- **Destructive commands**:
  - Prohibited unless explicitly approved by the user.
  - Examples: `rm -rf`, `git reset --hard`, force pushes, mass file renames.

- **Network access**:
  - Only when allowed by environment.
  - If blocked, state clearly what you were trying to do and why.

- **MCP/tools**:
  - Use provided MCP servers and tools according to project rules.
  - Prefer safe, local tools like `rg` for search.
  - Avoid global installs or environment mutation unless explicitly required and approved.

- **Sub-agents**:
  - If available behind a CLI, treat them as extensions of the active agent,
    following these same rules.

---

## Session Summaries

- **Location**: `.collab/session-summaries/`
- **Filename**:
  - First summary of the day: `MM.DD.YYYY-agentname-summary.md`
  - Additional same-day summaries: `MM.DD.YYYY-##-agentname-summary.md`
    (use zero-padded sequence like `02`, `03`, etc.)
  - Examples: `02.18.2026-claude-summary.md`, `02.18.2026-02-claude-summary.md`
- **YAML front matter (required)**:

```yaml
---
date: MM.DD.YYYY
agent: <agent-name>
timezone: America/New_York
summary: "1-2 sentence outcome."
---
```

- **Body**: Short bullet log covering what was done, what changed, blockers, and next steps.
- Each agent writes their own summary. Write one for any session where work occurred.

---

## Session Protocols

### OPEN SESSION

When the user types exactly:

    OPEN SESSION

Immediately execute the Session Open Protocol — do not wait for additional instructions:

1. Find and read the most recent 1-2 session summaries in `.collab/session-summaries/`
   (sort by filename date, newest first).
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md` if it exists.
4. Deliver a concise session resume to the user covering:
   - What was accomplished last session
   - What is currently In Progress or Blocked on the board
   - What is up next
   - Any open questions or flags left from the last session

Do **not** re-read `collab-contract.md` — focus on current state, not process rules.

### SAVE SESSION

When the user types exactly:

    SAVE SESSION

Immediately execute the Session Save Protocol — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` using the same naming
   convention as CLOSE SESSION (always a new file — never overwrite an existing one):
   - `MM.DD.YYYY-agentname-summary.md` for the first summary that day.
   - `MM.DD.YYYY-##-agentname-summary.md` for additional same-day saves/closes
     (use zero-padded sequence like `02`, `03`, etc.).
   - Use the template at `.collab/session-summaries/session-summary-template.md`.
2. Update `.collab/kanban-board.md` to reflect current task state:
   - Move completed tasks to **Done**.
   - Update statuses of in-progress tasks.
   - Add newly discovered tasks to **Inbox** or **Backlog**.
3. Confirm the checkpoint was saved. **Do not end the session** — continue working.

> Use `SAVE SESSION` as a mid-session checkpoint. If the session is interrupted
> unexpectedly, the last save can be used to reconstruct context on next `OPEN SESSION`.

### CLOSE SESSION

When the user types exactly:

    CLOSE SESSION

Immediately execute the Session Close Protocol — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` using:
   - `MM.DD.YYYY-agentname-summary.md` for the first summary that day.
   - `MM.DD.YYYY-##-agentname-summary.md` for additional same-day summaries
     (use zero-padded sequence like `02`, `03`, etc.).
   - Use the template at `.collab/session-summaries/session-summary-template.md`.
2. Update `.collab/kanban-board.md` to reflect current task state:
   - Move completed tasks to **Done**.
   - Update statuses of in-progress tasks.
   - Add newly discovered tasks to **Inbox** or **Backlog**.
3. Confirm completion to the user.

### SAVE CHAT

When the user types exactly:

    SAVE CHAT

Immediately execute the Chat Save Protocol — do not wait for additional instructions:

1. Run from the project root:
   - If scaffy is on PATH: `scaffy --save-chat`
   - Otherwise: `python3 scaffy.py --save-chat`
   - scaffy auto-detects the running agent (Claude, Codex, Gemini). Override with `--cli {claude,codex,gemini}` if needed.
2. The tool saves the transcript to `.collab/chat-logs/` automatically.
3. Confirm the filename and path to the user.

---

## Kanban Board

- **File**: `.collab/kanban-board.md`
- **Purpose**: Human-readable task board; default source of truth for task status.
- **Sections**: Inbox, Backlog, Sprint Backlog, To Do, In Progress, Blocked, In Review, Done.
- **Format**: Markdown checkboxes (`- [ ]` / `- [x]`) with task ID, owner, priority, area, and type.
- **Updates**: User and agents can edit directly; keep statuses current.

> **External tracker rule:**
> By default, `kanban-board.md` is the source of truth.
> **If** this project is connected to an external tracker (e.g., GitHub Issues, GitHub Projects,
> Jira, Linear) **and** you have access to it, treat that tracker as the authoritative record —
> create, update, and close items there first.
> Regardless, **always keep `kanban-board.md` in sync** so it remains a useful internal
> snapshot for any agent or session that cannot reach the external tracker.

---

## Brainstorm Directory

- **Location**: `.collab/brainstorms/`
- **Purpose**: Persistent thinking space for ideas that aren't ready to become tickets.
  Use this directory to capture, workshop, and evolve ideas collaboratively before they
  enter the formal task pipeline.
- **One file per idea cluster** — name files descriptively (lowercase, hyphen-separated).
- **Use the template** at `.collab/brainstorms/brainstorm-template.md` as a starting point.
- **Nothing in `brainstorms/` is required to go anywhere.** Ideas can sit, evolve, or be parked
  indefinitely. The value is keeping them on paper so they aren't lost between sessions.

### Agent Behavior in `brainstorms/`

When the user points you at a file in `.collab/brainstorms/`:

1. Read the full file before responding.
2. Engage honestly — assess whether the idea has merit, identify gaps, ask clarifying questions.
3. Append a dated entry to the **Discussion Log** section summarizing the exchange and any
   key conclusions.
4. Update **Next Steps / Open Questions** to reflect the current state.
5. Update the `Status` field as the idea progresses:
   `drafting` → `workshopping` → `parked` or `graduated`
6. Do **not** create tickets, tasks, or kanban entries from an idea without explicit user approval.

When an idea graduates to a formal ticket:

- Add `Graduated → Issue #__ on [date]` at the bottom of the file.
- Leave the file in `brainstorms/` as a record — do not delete it.

---

## Project Plans Directory

- **Location**: `.collab/project-plans/`
- **Purpose**: Structured planning space between brainstorming and execution.
  Use this directory to define goals, phases, and tasks before they enter the kanban pipeline.
- **One file per plan** — name files descriptively (lowercase, hyphen-separated).
- **Use the template** at `.collab/project-plans/project-plan-template.md` as a starting point.

### Agent Behavior in `project-plans/`

When the user points you at a file in `.collab/project-plans/`:

1. Read the full file before responding.
2. Clarify the goal and phases — ask questions rather than assuming scope.
3. Do **not** promote tasks to the kanban board without explicit user approval.
4. Update the `Status` field as the plan progresses:
   `draft` → `active` → `complete` or `archived`

When a plan phase is approved for execution:

- Promote its tasks to `.collab/kanban-board.md`.
- Note it at the bottom of the plan file: `Phase [N] promoted to kanban on [date]`.
- Leave the plan file in place — it is the planning record.
""",

    ".collab/kanban-board.md": """\
# Kanban Board

<!--
Format:
- [ ] {ticket_prefix}-###: Description (@owner) [p?] [area:?] [type:?]
Examples:
- [ ] {ticket_prefix}-001: Draft project plan (@user) [p1] [area:planning] [type:doc]
- [ ] {ticket_prefix}-002: Implement first feature (@claude) [p2] [area:core] [type:feature]
-->

## Working Rules
- The board is the source of truth.
- Don't move items to **Done** unless there is a tangible artifact (merged code / written doc / completed checklist).
- Keep **In Progress** to ~3 items max (soft WIP limit).
- If blocked, move to **Blocked** and add a short reason.
- Track one active sprint at a time (optional). Move committed sprint work into **Sprint Backlog**.
- Only move items to **To Do** if they are in the active sprint scope.

## Active Sprint (optional)
- Sprint ID: `SPRINT-YYYYMMDD`
- Dates: `MM.DD.YYYY` -> `MM.DD.YYYY`
- Goal: _one sentence_
- Exit criteria: _what must be true at sprint end_

---

## Inbox (untriaged)

## Backlog (approved, not scheduled)

## Sprint Backlog (committed scope for active sprint)

## To Do (next up)

## In Progress (doing now)

## Blocked

## In Review (awaiting user/PR review)

## Done
""",

    ".collab/brainstorms/brainstorm-template.md": """\
# Idea Title

_Started: {date}_
_Status: drafting_

<!-- Status values: drafting | workshopping | parked | graduated -->

## The Idea

<!-- Brain dump here. No rules. Write freely. -->

## Discussion Log

<!-- Agent/human back-and-forth: summaries, assessments, key decisions.    -->
<!-- Date-stamp each entry so the evolution is traceable.                  -->

## Next Steps / Open Questions

<!-- What needs to happen before this becomes a ticket — or gets parked. -->

---
<!-- When graduated: Graduated → Issue #__ on [date] -->
""",

    ".collab/project-plans/project-plan-template.md": """\
# Plan Title

_Created: {date}_
_Status: draft_
_Linked issue: —_

<!-- Status values: draft | active | complete | archived -->

## Goal

<!-- What does success look like? One clear sentence. -->

## Background

<!-- Why this plan exists. Problem being solved, context needed. -->

## Phases

### Phase 1: [Name]

- [ ] Task description
- [ ] Task description

### Phase 2: [Name]

- [ ] Task description

## Risks & Dependencies

| Risk / Dependency | Impact | Mitigation |
|---|---|---|
| | | |

## Open Questions

<!-- Unresolved decisions that would block or change the plan. -->

---
<!-- When phases promoted: Phase [N] promoted to kanban on MM.DD.YYYY -->
<!-- When complete: Completed on MM.DD.YYYY -->
""",

    ".collab/prompts/agent-profile.md": """\
# Agent Profile

_Fill this out before generating your agent instructions file. Free text — write however feels
natural. Your AI agent will read this to produce a tailored CLAUDE.md, AGENTS.md, or equivalent._

_See `agent-md-prompt.md` (same directory) for the prompt to paste into your agent when ready._

---

## Project

What does this project do? What problem does it solve? Who is it for?

<!-- Write freely. One sentence or several paragraphs — whatever captures it. -->

## Tech Stack

What language(s), frameworks, and key libraries does this project use?
Anything unusual about the environment or toolchain?

<!-- Example: Python 3.11, FastAPI, PostgreSQL, deployed on AWS Lambda -->

## Key Commands

How do you build, run, test, and lint this project?

<!-- Example:
  Run:   python main.py
  Test:  pytest
  Lint:  ruff check .
  Build: docker build -t myapp .
-->

## Conventions

What naming conventions, file structure rules, or style preferences matter here?

<!-- Example: snake_case everywhere, feature branches off dev, no print() in library code -->

## Guardrails

What should the agent never do without asking you first?

<!-- Example: never push to main, never delete files, never install global packages -->

## About You (optional)

How experienced are you with this stack? How do you prefer to collaborate —
high-level direction, detailed review, something else?

<!-- This helps the agent calibrate its tone and how much it explains. -->
""",

    ".collab/prompts/agent-md-prompt.md": """\
# Agent Instructions Generator

_Paste this into your AI agent after filling out `agent-profile.md` (same directory)._

---

I've filled out `.collab/prompts/agent-profile.md` for this project.

Read it carefully and generate an agent instructions file in the project root.
Name it appropriately for the agent you are:

- Claude Code → `CLAUDE.md`
- OpenAI Codex / ChatGPT → `AGENTS.md`
- Gemini → `GEMINI.md`
- Other → use whatever instructions file your agent reads at session start

**Guidelines for the file you generate:**

- Keep it practical and concise — every line should matter in a working session
- Lead with a one-line project summary, then tech stack, then key commands
- Pull conventions and guardrails directly from the profile — don't invent details
- Format for skimmability: short sections, bullets, code blocks for commands
- If the profile is sparse or ambiguous on something important, ask before generating
""",

    ".collab/playbooks/coding-playbook.md": """\
---
title: Coding Playbook
description: General coding standards and best practices — a guiding hand, not a rulebook
---

# Coding Playbook

A reference for how to build software well. This is a starting point — project-level
conventions in `CLAUDE.md` or `.collab/context.md` take precedence over anything here.

> Not every project is a code project. Sections marked **[code]** apply only when the
> project produces runnable software.

---

## 1. Project Structure [code]

Separate concerns clearly from day one. A project that mixes business logic, CLI code,
config, and tests in one file is a project that's hard to extend, test, or hand off.

**Guiding principles:**

- **Core logic stays separate from interfaces.** A library shouldn't know whether it's
  being called by a CLI, a GUI, or a test.
- **One entry point.** Know exactly where execution starts.
- **Config and secrets never live next to source code.** They change per environment;
  source code should not.

**Common layout for a Python project:**

```
project-root/
  src/package/        # core library / business logic
    __init__.py
    __main__.py       # entry point: python -m package
  tests/
    unit/
    integration/
  config/             # runtime config (gitignored)
  .gitignore
  pyproject.toml
```

Adapt this to your language and framework. The principle — not the exact layout — is what matters.

---

## 2. Code Style [code]

Consistency beats preference. Pick a style and enforce it with tooling so it's never a
debate in code review.

### Naming

| Context | Convention |
|---------|-----------|
| Variables, functions | `snake_case` (Python) / `camelCase` (JS/TS/Java) |
| Classes | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` |
| Files and directories | `lowercase-hyphenated` or `snake_case` (match language norms) |

### Type Hints [Python]

Annotate all function signatures. Return types included.

```python
# Good
def get_user(user_id: str) -> dict[str, str]: ...

# Bad — no hints, no contract
def get_user(user_id): ...
```

### Imports

- Standard library → third-party → local (in that order)
- No wildcard imports (`from module import *`)
- Type-only imports under `if TYPE_CHECKING:` guard

### The single most important style rule

**No `print()` in library or core code.** Return structured results. Only the CLI or
presentation layer should produce output. This keeps core logic testable and reusable.

---

## 3. Configuration and Secrets

### Configuration

- Never hardcode values that belong in config (URLs, timeouts, feature flags).
- Load config once, at startup — not scattered throughout the codebase.
- Commit a `config.example` with placeholder values. Never commit the real config.

```python
# Good — one place, loaded once
config = load_config("config/config.json")

# Bad — scattered hardcodes
BASE_URL = "https://api.example.com"   # in three different files
```

### Secrets

**Never commit secrets.** Not in source files, not in config files, not in comments,
not in commit messages. Gitignored files have been accidentally staged before and will be again.

| Type | Examples | Where it lives |
|------|---------|----------------|
| Config | base URLs, feature flags, timeouts | `config/config.json` (gitignored) |
| Secrets | API keys, tokens, passwords | Environment variables or a secrets manager |

Load secrets from environment variables at runtime:

```python
import os
api_key = os.environ["MY_SERVICE_API_KEY"]  # raises KeyError if missing — that's correct
```

---

## 4. Error Handling

**Fail loudly at system boundaries. Handle gracefully inside loops.**

The goal is: when something goes wrong, the error message tells you exactly what failed
and why — not a vague crash three layers up.

```python
# Good — specific, logged, recoverable
try:
    result = fetch_resource(resource_id)
except ResourceNotFoundError as e:
    logger.warning("Resource %s not found — skipping", resource_id)
    return None

# Bad — silent swallow
try:
    result = fetch_resource(resource_id)
except Exception:
    pass

# Bad — bare except
try:
    result = fetch_resource(resource_id)
except:
    result = None
```

**Never use `except Exception: pass`.** If you're catching an exception, do something
intentional: log it, return a fallback, re-raise with context, or let it propagate.

---

## 5. Testing [code]

### Structure

```
tests/
  unit/          # fast, isolated, no external state
  integration/   # touches files, network, databases, or external services
```

### What to test

- Unit tests cover logic: functions, transformations, edge cases
- Integration tests cover boundaries: file I/O, API calls, database queries
- Don't test the framework — test your code

### The gate before merging

At minimum, the following must pass clean before any code merges:

```bash
lint-tool .          # e.g. ruff, eslint, flake8
formatter --check .  # e.g. black, prettier
type-checker .       # e.g. mypy, tsc
pytest -m "not slow" # or equivalent fast test suite
```

Define these in CI so they run automatically on every pull request.

---

## 6. Git Governance

### Branch naming

```
main          ← stable / production
dev           ← primary development (optional but recommended)
feat/<slug>   ← new feature
fix/<slug>    ← bug fix
chore/<slug>  ← maintenance (deps, config, docs)
```

Prefix with issue number when your tracker supports it: `feat/42-add-export`

### Commit messages

Imperative mood, present tense, lowercase. One line. Add a body if the why isn't obvious.

```
# Good
add s3 export for ec2 instances
fix null pointer in config loader
update dependencies to patch CVE-2026-1234

# Bad
Added s3 export
Fixed a bug
Updates
```

### Issue-first rule

For any team or structured project: open an issue before starting a branch.
Every PR references the issue it closes:

```
Closes #42
```

### CI baseline

Every code project gets a CI workflow that runs on push and pull request:

```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: [your install command]
      - name: Lint
        run: [your lint command]
      - name: Test
        run: [your test command]
```

This is the floor. Add type checking, coverage, security scanning on top of it.

---

## 7. Guardrails

These apply to both humans and AI agents working in the project.

### Never without explicit approval

| Action | Why |
|--------|-----|
| `rm -rf` or bulk file deletion | Irreversible |
| `git reset --hard` | Destroys uncommitted work |
| Force push to a shared branch | Rewrites history others depend on |
| Direct push to `main` | Bypasses review |
| Global package / environment changes | Affects everything outside the project |
| Architectural changes not covered by existing context | Needs a decision, not an assumption |

### Always required

- Secrets stay out of the repo — no exceptions
- New files fit the established project structure
- CI must pass before merge
- Breaking changes are documented, not silently shipped

---

## 8. Anti-Patterns

| Anti-Pattern | Why It's Wrong | Correct Approach |
|---|---|---|
| `print()` in library code | Breaks testability and reuse | Return results; print in the CLI layer |
| Hardcoded config values | Breaks portability | Read from config file or env vars |
| `except Exception: pass` | Silently hides bugs | Log and handle, or let it propagate |
| Loading config at import time | Causes side effects, makes testing hard | Load lazily or at startup in `main()` |
| Wildcard imports | Pollutes namespace, breaks tooling | Import explicitly |
| `git add .` blindly | May stage secrets, logs, build artifacts | Stage specific files by name |
| Secrets in config files | Even gitignored files get accidentally staged | Env vars or a secrets manager |
| Tests that test the framework | Wasted coverage | Test your logic, not third-party behavior |
| Comments that describe what the code does | Code should be self-documenting | Comment the *why*, not the *what* |
| Skipping the test on "just a small change" | Small changes cause regressions too | Run the fast suite before every commit |
| One giant file | Hard to read, test, and maintain | Split by responsibility when complexity grows |
| Abstractions built for one use | Premature generalization | Write it inline; extract when used 3+ times |
""",

    ".collab/context.md": """\
# Project Context

## What This Project Is

{description}

## Tech Stack

- Language:
- Framework:
- Key dependencies:

## Key Files and Entry Points

- Main entry:
- Config:
- Tests:

## Environment Notes

<!-- Dev environment setup, required credentials, local quirks -->

## External Dependencies

<!-- APIs, services, upstream systems this project relies on -->

## Conventions

<!-- Naming, style, file organization, commit format, anything an agent needs to know -->
""",

    ".collab/project.yaml": """\
project: {project_name}
created: {date}
timezone: America/New_York
governance_mode: {governance_mode}
platform: {platform}
license: {license}
ticket_prefix: {ticket_prefix}
""",


    ".collab/session-summaries/session-summary-template.md": """\
---
date: MM.DD.YYYY
agent: <agent-name>
timezone: America/New_York
summary: "1-2 sentence outcome of the session."
---

## What Happened

- Key accomplishments and decisions.
- Tests run (with results) or why not run.
- Blockers or risks.

## Next Steps

- Who owns the next action.
- Files touched (paths only).
""",

    ".collab/guides/git-guidelines.md": """\
---

# Git Platform Governance & AI Agent Operating Guidelines

**Version: v1.3.0 (Unified Template)**

---

## 1. Purpose and Scope

This document defines a baseline operating model for teams and AI agents working in a Git-backed project.
It includes a platform-agnostic core plus GitHub and GitLab implementation notes in one place.

Use it as a template, not a one-size-fits-all policy.

- For highly regulated or high-risk work, use stricter controls.
- For prototypes or early discovery, use lightweight controls.

If this document conflicts with repository settings (labels, protections, automation),
treat repository settings as current truth and open a governance issue to reconcile.

---

## 2. Governance Modes

Pick one mode for the repository (or per milestone):

### Strict Mode

Use when reliability, compliance, or auditability are critical.

- Work starts only from approved work items.
- Change request-only updates to protected branches.
- Required reviews and status checks.
- Structured labels and board hygiene enforced.

### Standard Mode (Recommended default)

Use for most active product development.

- Most work starts from work items.
- Change request workflow is expected for shared branches.
- Labeling and board updates are required for meaningful work.
- Small docs/chore changes can be streamlined.

**Solo maintainer exception:** If this project has a single maintainer, reviewer approval
is not required to merge. Feature/fix branches and PRs are still expected for non-trivial work —
the PR serves as a change record, not a review gate. Direct-to-main commits are acceptable
only for trivial fixes (typos, comment edits, minor config tweaks).

### Lightweight Mode

Use for prototypes, sandboxes, and early ideation.

- Work items are encouraged but not required for every small change.
- Minimal label policy.
- Faster iteration with fewer process gates.
- Upgrade to Standard/Strict before release hardening.

Record the active mode in README or project board notes.

---

## 3. Core Working Principle

Track work in a way that is visible and reviewable across tools.

Recommended default:

- Use work items (issues/tickets) as the planning source of truth.
- Link all non-trivial change requests (PR/MR) to a work item.
- Keep board status and labels current enough for handoff.

Minimum expectation in any mode:

- No unreviewed high-risk changes.
- No hidden work that bypasses team visibility.

---

## 4. Work Item Lifecycle

Recommended lifecycle:

`idea -> triaged work item -> assigned work -> change request -> merged -> closed`

For Standard/Strict mode, confirm before implementation starts:

1. Scope is clear and single-concern.
2. Priority and type are set.
3. Ownership is set.
4. Acceptance criteria are testable.

Approval authority should be defined by repository owners (maintainers or delegated leads).

If approval state is unclear for high-impact work, pause and ask.

---

## 5. Labels (Configurable Taxonomy)

Use labels to support planning, triage, and reporting.

Recommended composition in Standard/Strict mode:

- Exactly 1 Priority label
- Exactly 1 Type label
- 1+ Area/domain labels

Suggested defaults (customize per project):

### Priority

- `p0-critical`
- `p1-high`
- `p2-medium`
- `p3-low`

### Type

- `feature`
- `bug`
- `refactor`
- `docs`
- `test`
- `chore`

### Area (examples)

- `backend`
- `frontend`
- `infra`
- `ci-cd`
- `security`
- `performance`
- `documentation`

Label policy recommendation:

- Avoid near-duplicate labels.
- Prefer a small stable taxonomy.
- If a new label is needed, propose it in an issue first.

---

## 6. Branching and Merge Strategy

Branch strategy should match release model.

Common options:

- `main` only (trunk-based)
- `main` + `develop`
- release branches for stabilization windows

Recommended baseline:

- Use feature/fix branches for non-trivial work.
- Open change requests (PR/MR) into the primary integration branch.
- Require at least one reviewer in Standard/Strict mode.

Suggested branch names:

- `issue-<number>-<slug>`
- `feature/<slug>`
- `fix/<slug>`
- `refactor/<slug>`
- `chore/<slug>`

---

## 7. Pull Request Standards

Every change request (PR/MR) should include:

- What changed
- Why it changed
- How it was tested
- Linked work item(s)
- Risk notes (if relevant)

For higher-risk changes, include rollout and rollback notes.

Do not merge when:

- Required checks fail
- Review requirements are unmet
- Scope materially diverges from work item intent without updates

---

## 8. Project Board Usage

Board policy can be minimal or structured depending on mode.

Recommended columns:

- Inbox
- Backlog
- To Do
- In Progress
- Blocked
- In Review
- Done

If using sprints, add:

- Active Sprint metadata
- Sprint Backlog (committed scope)

Keep board updates lightweight but current enough for async coordination.

---

## 9. Exceptions and Fast Paths

Allow explicit exceptions for operational speed when needed.

Examples:

- Hotfixes
- Incident response
- Build-break recovery

When using a fast path:

1. Document why process was bypassed.
2. Link post-hoc tracking issue.
3. Follow up with normal governance cleanup.

---

## 10. Automation and Policy-as-Code

Where practical, enforce standards in platform configuration:

- Branch protection rules
- Required status checks
- CODEOWNERS
- Work item/change request templates
- Label sync automation

Keep automation aligned with the selected governance mode.

---

## 11. Platform Notes (GitHub and GitLab)

Use the core policy above as authoritative. Platform notes below define mechanics.

### GitHub Terms and Mechanics

- Work item: GitHub Issue
- Change request: Pull Request (PR)
- Recommended settings:
  - Protect primary branches (for example `main`)
  - Require pull request before merge
  - Require at least one approval (Standard/Strict mode)
  - Require status checks where CI exists
  - Restrict force pushes on protected branches
- Automation:
  - Use `Closes #<issue-number>` in PR descriptions for auto-close behavior
  - Configure templates in `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md`
  - Keep labels aligned to the core taxonomy (priority/type/area)
- Tracking:
  - If using GitHub Projects, keep item status synchronized with board columns

### GitLab Terms and Mechanics

- Work item: GitLab Issue
- Change request: Merge Request (MR)
- Recommended settings:
  - Protect primary branches (for example `main`)
  - Require merge request before merge (Standard/Strict mode)
  - Require at least one approval (Standard/Strict mode)
  - Require successful pipeline status where CI exists
  - Restrict force pushes on protected branches
- Automation:
  - Use `Closes #<issue-number>` in MR descriptions for auto-close behavior
  - Configure templates in `.gitlab/issue_templates/` and `.gitlab/merge_request_templates/`
  - Keep labels aligned to the core taxonomy (priority/type/area)
- Tracking:
  - If using GitLab Issue Boards, keep item status synchronized with board columns

In all cases, keep `.collab/kanban-board.md` synchronized as an internal fallback snapshot.

---

## 12. Review Cadence

Revisit this governance template at least quarterly or when:

- Team size changes materially
- Release process changes
- Compliance/risk posture changes
- Repeated workflow friction appears

Treat governance as maintainable system design, not static doctrine.

---

## 13. 5-Minute Adoption Checklist (New Repo)

Use this to bootstrap quickly without over-engineering.

1. Choose a governance mode:
- `Lightweight` for prototyping.
- `Standard` for normal team delivery.
- `Strict` for high-risk or compliance-heavy work.

2. Create a minimal label set:
- Priority: `p0-critical`, `p1-high`, `p2-medium`, `p3-low`
- Type: `feature`, `bug`, `refactor`, `docs`, `test`, `chore`
- Area: pick 4-8 project-relevant domains (for example `backend`, `frontend`, `infra`, `security`).

3. Configure branch protections on your primary branch:
- Require pull request before merge.
- Require at least one approval (Standard/Strict).
- Require status checks for CI where available.

4. Enable work item and change request templates:
- Use `.collab/playbooks/templates/issue-template.md` as your baseline.
- Use `.collab/playbooks/templates/pull-request-template.md` as your PR/MR template.
- Copy into your platform's template directory (`.github/`, `.gitlab/`, etc.).

5. Set up a basic board:
- Columns: `Inbox`, `Backlog`, `To Do`, `In Progress`, `Blocked`, `In Review`, `Done`.
- If sprint-based, also track `Active Sprint` metadata and `Sprint Backlog`.

6. Define ownership signals:
- Document who can approve/merge.
- Add CODEOWNERS for critical paths if your team is larger than one maintainer.

7. Run a lightweight governance check at end of first week:
- Are labels being used consistently?
- Are change requests linked to work items for non-trivial work?
- Are protections too strict or too loose for current velocity?

This checklist is intentionally minimal. Expand controls only where risk or team size justifies it.

---
""",

    ".collab/playbooks/templates/issue-template.md": """\
---

# Work Item Template (Platform-Agnostic)

> Use this template for non-trivial issues/work items.
> Teams can keep all sections for Standard/Strict governance, or trim sections for Lightweight mode.

---

## Title

Recommended format:

`[<area>] <imperative, outcome-based summary>`

Examples:

- `[backend] Add pagination to report endpoint`
- `[infra] Enable branch protection for main`
- `[docs] Document release workflow`

---

## Description

Describe the problem or goal clearly.

Include:

- Current behavior (if applicable)
- Desired behavior
- Why this matters (impact, risk, user value, technical debt)

---

## Proposed Solution

Describe the intended approach.

Include when useful:

- Components/files likely affected
- Architectural considerations
- Backward compatibility or migration concerns
- Security, performance, and operational considerations

If multiple approaches are viable, list tradeoffs and preferred option.

---

## Acceptance Criteria

Use specific, testable criteria.

Example format:

- [ ] API returns paginated results with stable ordering
- [ ] Validation errors return clear messages
- [ ] Existing behavior remains unchanged for unaffected endpoints
- [ ] Documentation updated for new usage

---

## Test Plan

Describe how the change will be validated.

Include as applicable:

- Unit tests
- Integration/end-to-end tests
- Manual verification steps
- Monitoring/observability checks

If tests are intentionally deferred, explain why and add a follow-up issue.

---

## Risks and Mitigations

Document notable risks:

- Functional regressions
- Security exposure
- Performance impact
- Deployment/rollback risk

Mitigation and rollback notes:

- _Add specific rollback path if relevant_

If none, state `None`.

---

## Definition of Done

Mark complete when applicable:

- [ ] Implementation finished
- [ ] Tests added/updated (or justified)
- [ ] Docs updated (if needed)
- [ ] PR opened and linked to this issue
- [ ] Review complete
- [ ] Merged into target branch

---

## Labels and Tracking (Optional but Recommended)

Suggested label composition (Standard/Strict mode):

- 1 Priority label (e.g., `p0-critical` ... `p3-low`)
- 1 Type label (e.g., `feature`, `bug`, `refactor`, `docs`, `test`, `chore`)
- 1+ Area labels (project-specific)

Also include as relevant:

- Milestone
- Project board item
- Assignee/owner

For Lightweight mode, apply only the labels your repo actively uses.

---
""",

    ".collab/playbooks/templates/pull-request-template.md": """\
---

# Change Request Template (Platform-Agnostic)

> Use this template for meaningful changes in pull requests (GitHub) or merge requests (GitLab).
> In Lightweight mode, keep sections brief; in Standard/Strict mode, complete all relevant sections.

---

## Summary

What changed, in plain language?

-

## Why

Why this change is needed (bug, feature, risk reduction, maintenance, etc.).

-

## Linked Work Item(s)

Reference related issue(s)/ticket(s):

- Closes #
- Related #

## Scope

What is included in this PR?

-

What is explicitly out of scope?

-

## Validation

How was this verified?

- [ ] Unit tests
- [ ] Integration/end-to-end tests
- [ ] Manual verification
- [ ] CI checks passed

Evidence (commands, screenshots, logs, links):

```text
# example
# pytest -q
# npm test
```

## Risk Assessment

Potential risks:

- Functional regression: low / medium / high
- Security impact: none / low / medium / high
- Performance impact: none / low / medium / high
- Operational/deployment risk: low / medium / high

Notes:

-

## Rollout and Rollback

Rollout plan:

-

Rollback plan:

-

## Documentation and Follow-ups

- [ ] Docs updated (if needed)
- [ ] Release notes entry (if needed)
- [ ] Follow-up issue(s) created (if needed)

Follow-up links:

- #

## Reviewer Checklist

- [ ] Scope matches linked work item intent
- [ ] Acceptance criteria are satisfied (or updated in issue)
- [ ] Test evidence is adequate for risk level
- [ ] No sensitive data or secrets introduced
- [ ] Rollback path is clear for high-impact changes

---
""",

    ".collab/playbooks/git-governance-lightweight.md": """\
---
title: Git Governance Playbook — Lightweight
description: Step-by-step procedures for prototypes, sandboxes, and early-stage projects
governance_mode: lightweight
---

# Git Governance Playbook — Lightweight

**When to use:** Prototypes, sandboxes, personal projects, early ideation.
**Reference:** `.collab/guides/git-guidelines.md` explains the *why* behind each mode.

> Upgrade to Standard before shipping to production or onboarding a second contributor.

---

## Starting Work

1. No issue required for small changes — commit directly to `main` or a short-lived branch.
2. For anything taking more than a session, create a branch: `feature/<slug>` or `fix/<slug>`.
3. Keep a rough record of intent in the commit message — that's your audit trail.

## Committing

- Commit early and often. No minimum quality gate.
- Use conventional commit format when practical: `feat:`, `fix:`, `chore:`, `docs:`.
- No required reviewer. Self-merge is fine.

## Opening a PR / MR

- Optional at this mode. Use when you want a change record or are unsure about a change.
- No required sections — a one-line summary is enough.

## Merging

- Merge when the work is done. No approval gate.
- Squash or merge commit — your preference.
- Delete the branch after merge if using feature branches.

## Hotfixes

- Commit directly to `main`. Document what broke and why in the commit message.

## When to Upgrade

Upgrade to Standard mode when:

- A second contributor joins.
- The project ships to a real user or production system.
- You find yourself losing track of what changed and why.

---
""",

    ".collab/playbooks/git-governance-standard.md": """\
---
title: Git Governance Playbook — Standard
description: Step-by-step procedures for active product development (recommended default)
governance_mode: standard
---

# Git Governance Playbook — Standard

**When to use:** Most active projects — team delivery, side products, anything shipping to users.
**Reference:** `.collab/guides/git-guidelines.md` explains the *why* behind each mode.

---

## Starting Work

1. Confirm a work item (issue/ticket) exists. Create one if not.
2. Assign yourself and move the item to **In Progress** on the board.
3. Create a branch from the primary integration branch:
   - `feature/<slug>` or `issue-<number>-<slug>`
   - Keep branches short-lived — one concern per branch.

## Committing

- Use conventional commit format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Each commit should be coherent and buildable.
- Reference issue numbers in commits when relevant: `fix: resolve race condition (#42)`.

## Opening a PR / MR

1. Use the template at `.collab/playbooks/templates/pull-request-template.md`.
2. Required sections: **Summary**, **Why**, **Linked Work Item(s)**, **Validation**.
3. Link to the work item with `Closes #<number>` for auto-close.
4. Keep scope tight — one concern per PR.

## Merging

- **Solo maintainer:** No reviewer required. PR serves as a change record. Merge when CI passes (if applicable).
- **Multi-contributor:** One approval required before merge.
- Do not merge if required checks fail.
- Delete the branch after merge.
- Move the work item to **Done** on the board.

## Hotfixes

1. Create a `fix/<slug>` branch directly from `main`.
2. Open a PR with a minimal description — note it is a hotfix.
3. Merge with expedited review (or self-merge if solo).
4. Create a post-hoc tracking issue if one doesn't exist.

## Blocked Work

- Move the work item to **Blocked** on the board with a brief reason.
- Unblock or reassign before end of sprint/week.

---
""",

    ".collab/playbooks/git-governance-strict.md": """\
---
title: Git Governance Playbook — Strict
description: Step-by-step procedures for compliance-sensitive or high-risk projects
governance_mode: strict
---

# Git Governance Playbook — Strict

**When to use:** Compliance requirements, auditable work, high-risk or high-visibility systems.
**Reference:** `.collab/guides/git-guidelines.md` explains the *why* behind each mode.

---

## Starting Work

1. Work item must exist, be approved, and have clear acceptance criteria before work begins.
2. Assign yourself and move to **In Progress**. Do not start without an approved item.
3. Create a branch:
   - `feature/<slug>`, `fix/<slug>`, or `issue-<number>-<slug>`.
   - No direct commits to protected branches (`main`, `develop`, release branches).
4. If scope is unclear, resolve it before writing code — not during review.

## Committing

- Conventional commit format required: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Each commit must be coherent, atomic, and buildable.
- Reference issue numbers in every non-trivial commit.
- No "WIP" commits on shared branches.

## Opening a PR / MR

1. Use the full template at `.collab/playbooks/templates/pull-request-template.md`.
2. All sections required: **Summary**, **Why**, **Linked Work Item(s)**, **Scope**, **Validation**, **Risk Assessment**, **Rollout and Rollback**.
3. Risk assessment must be completed — do not leave fields blank.
4. PR must pass all CI/CD checks before review is requested.
5. `Closes #<number>` required in description.

## Merging

1. Minimum two approvals required (or one if only two contributors exist).
2. All required status checks must pass.
3. Reviewer checklist in the PR template must be completed by at least one reviewer.
4. No force pushes to protected branches.
5. Delete branch after merge.
6. Update work item to **Done** and note any follow-up items.

## Exceptions and Fast Paths

If a process bypass is unavoidable (incident response, build-break):

1. Document the reason in the commit message or PR description.
2. Tag the PR/commit with an exception label.
3. Create a follow-up issue within 24 hours for governance cleanup.
4. Note the exception in the next review cadence.

Never skip exceptions silently — the audit trail must show the bypass and the reason.

## Hotfixes

1. Create `fix/<slug>` branch from `main` (or current release branch).
2. Open a PR immediately — do not wait for work to be complete to create the PR.
3. Use the PR template with at minimum: Summary, Risk Assessment, Rollback Plan.
4. Expedited review by one qualified reviewer. Post-hoc second review within 48 hours.
5. Create post-hoc issue documenting root cause and prevention plan.

## Governance Review

Review this playbook and the project's governance posture:

- At each sprint retrospective.
- When team composition changes.
- After any incident or near-miss.
- Before entering a compliance audit period.

---
""",
}


# ---------------------------------------------------------------------------
# License texts — written to LICENSE based on --license flag
# ---------------------------------------------------------------------------

_LICENSE_MIT = """\
MIT License

Copyright (c) <YEAR> <AUTHOR OR ORGANIZATION>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_LICENSE_APACHE2 = """\
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship made available under
      the License, as indicated by a copyright notice that is included in
      or attached to the work (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and derivative works thereof.

      "Contribution" shall mean, as submitted to the Licensor for inclusion
      in the Work by the copyright owner or by an individual or Legal Entity
      authorized to submit on behalf of the copyright owner. For the purposes
      of this definition, "submitted" means any form of electronic, verbal,
      or written communication sent to the Licensor or its representatives,
      including but not limited to communication on electronic mailing lists,
      source code control systems, and issue tracking systems that are managed
      by, or on behalf of, the Licensor for the purpose of discussing and
      improving the Work, but excluding communication that is conspicuously
      marked or designated in writing by the copyright owner as "Not a
      Contribution."

      "Contributor" shall mean Licensor and any Legal Entity on behalf of
      whom a Contribution has been received by the Licensor and included
      within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by the combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a cross-claim
      or counterclaim in a lawsuit) alleging that the Work or any
      Contribution embodied within the Work constitutes direct or contributory
      patent infringement, then any patent licenses granted to You under
      this License for that Work shall terminate as of the date such
      litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or Derivative
          Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, You must include a readable copy of the
          attribution notices contained within such NOTICE file, in
          at least one of the following places: within a NOTICE text
          file distributed as part of the Derivative Works; within
          the Source form or documentation, if provided along with the
          Derivative Works; or, within a display generated by the
          Derivative Works, if and wherever such third-party notices
          normally appear. The contents of the NOTICE file are for
          informational purposes only and do not modify the License.
          You may add Your own attribution notices within Derivative
          Works that You distribute, alongside or in addition to the
          NOTICE text from the Work, provided that such additional
          attribution notices cannot be construed as modifying the License.

      You may add Your own license statement for Your modifications and
      may provide additional grant of rights to use, copy, modify, merge,
      publish, distribute, sublicense, and/or sell copies of the
      Contribution, either on an "as is" basis or under different terms
      and conditions, provided that Your use, reproduction, and
      distribution of the Contribution otherwise complies with the
      conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or exemplary damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or all other
      commercial damages or losses), even if such Contributor has been
      advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may offer only
      conditions that are consistent with this License.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. Please also include the
      "NOTICE" file as described above.

   Copyright <YEAR> <AUTHOR OR ORGANIZATION>

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

_LICENSE_GPL3 = """\
                    GNU GENERAL PUBLIC LICENSE
                       Version 3, 29 June 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

                            Preamble

  The GNU General Public License is a free, copyleft license for
software and other kinds of works.

  For the complete license text, see:
  https://spdx.org/licenses/GPL-3.0-only.html

  To apply this license to your project, add the following notice.
  Replace <YEAR>, <AUTHOR OR ORGANIZATION>, and <PROGRAM NAME>:

    <PROGRAM NAME>
    Copyright (C) <YEAR>  <AUTHOR OR ORGANIZATION>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: GPL-3.0-only

NOTE: Replace this file with the full GPL-3.0 license text from:
      https://www.gnu.org/licenses/gpl-3.0.txt
"""

_LICENSE_AGPL3 = """\
                    GNU AFFERO GENERAL PUBLIC LICENSE
                       Version 3, 19 November 2007

 Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>
 Everyone is permitted to copy and distribute verbatim copies
 of this license document, but changing it is not allowed.

  For the complete license text, see:
  https://spdx.org/licenses/AGPL-3.0-only.html

  To apply this license to your project, add the following notice.
  Replace <YEAR>, <AUTHOR OR ORGANIZATION>, and <PROGRAM NAME>:

    <PROGRAM NAME>
    Copyright (C) <YEAR>  <AUTHOR OR ORGANIZATION>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

SPDX-License-Identifier: AGPL-3.0-only

NOTE: Replace this file with the full AGPL-3.0 license text from:
      https://www.gnu.org/licenses/agpl-3.0.txt
"""

_LICENSE_BSD2 = """\
BSD 2-Clause License

Copyright (c) <YEAR>, <AUTHOR OR ORGANIZATION>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

_LICENSE_BSD3 = """\
BSD 3-Clause License

Copyright (c) <YEAR>, <AUTHOR OR ORGANIZATION>

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

_LICENSE_MPL2 = """\
Mozilla Public License Version 2.0
==================================

  For the complete license text, see:
  https://spdx.org/licenses/MPL-2.0.html

  To apply this license to your project, replace <YEAR> and
  <AUTHOR OR ORGANIZATION> below, then replace this file with the
  full MPL-2.0 text from:
  https://www.mozilla.org/en-US/MPL/2.0/

Copyright (c) <YEAR> <AUTHOR OR ORGANIZATION>

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.

SPDX-License-Identifier: MPL-2.0

NOTE: Replace this file with the full MPL-2.0 license text from:
      https://www.mozilla.org/media/MPL/2.0/index.txt
"""

_LICENSE_UNLICENSE = """\
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>
"""

LICENSE_TEXTS: dict[str, str] = {
    "mit": _LICENSE_MIT,
    "apache-2.0": _LICENSE_APACHE2,
    "gpl-3.0": _LICENSE_GPL3,
    "agpl-3.0": _LICENSE_AGPL3,
    "bsd-2-clause": _LICENSE_BSD2,
    "bsd-3-clause": _LICENSE_BSD3,
    "mpl-2.0": _LICENSE_MPL2,
    "unlicense": _LICENSE_UNLICENSE,
}


# ---------------------------------------------------------------------------
# Platform files — written to .github/ or .gitlab/ based on --platform flag
# ---------------------------------------------------------------------------

_GITHUB_ISSUE_TEMPLATE = """\
---
name: Work Item
about: Feature, bug, task, or improvement
title: '[<area>] <imperative summary>'
labels: ''
assignees: ''
---

## Description

<!-- What is the problem or goal? Include current vs. desired behavior and why it matters. -->

-

## Proposed Solution

<!-- Intended approach. Note affected components, architectural considerations, and tradeoffs. -->

-

## Acceptance Criteria

- [ ]
- [ ]

## Test Plan

<!-- How will this be validated? Unit tests, integration tests, manual steps. -->

## Definition of Done

- [ ] Implementation finished
- [ ] Tests added/updated (or justified)
- [ ] Docs updated (if needed)
- [ ] PR opened and linked to this issue
- [ ] Review complete
- [ ] Merged into target branch
"""

_GITHUB_PR_TEMPLATE = """\
## Summary

<!-- What changed, in plain language? -->

-

## Why

<!-- Why this change is needed (bug fix, feature, risk reduction, maintenance). -->

-

## Linked Issue(s)

Closes #
Related #

## Validation

How was this verified?

- [ ] Unit tests
- [ ] Integration/end-to-end tests
- [ ] Manual verification
- [ ] CI checks passed

Evidence (commands, screenshots, logs, links):

```text
```

## Risk Assessment

- Functional regression: low / medium / high
- Security impact: none / low / medium / high
- Deployment risk: low / medium / high

## Reviewer Checklist

- [ ] Scope matches linked issue intent
- [ ] Acceptance criteria satisfied
- [ ] Test evidence adequate for risk level
- [ ] No sensitive data or secrets introduced
"""

_GITLAB_ISSUE_TEMPLATE = """\
## Description

<!-- What is the problem or goal? Include current vs. desired behavior and why it matters. -->

-

## Proposed Solution

<!-- Intended approach. Note affected components, architectural considerations, and tradeoffs. -->

-

## Acceptance Criteria

- [ ]
- [ ]

## Test Plan

<!-- How will this be validated? Unit tests, integration tests, manual steps. -->

## Definition of Done

- [ ] Implementation finished
- [ ] Tests added/updated (or justified)
- [ ] Docs updated (if needed)
- [ ] MR opened and linked to this issue
- [ ] Review complete
- [ ] Merged into target branch
"""

_GITLAB_MR_TEMPLATE = """\
## Summary

<!-- What changed, in plain language? -->

-

## Why

<!-- Why this change is needed (bug fix, feature, risk reduction, maintenance). -->

-

## Linked Issue(s)

Closes #
Related #

## Validation

How was this verified?

- [ ] Unit tests
- [ ] Integration/end-to-end tests
- [ ] Manual verification
- [ ] CI checks passed

Evidence (commands, screenshots, logs, links):

```text
```

## Risk Assessment

- Functional regression: low / medium / high
- Security impact: none / low / medium / high
- Deployment risk: low / medium / high

## Reviewer Checklist

- [ ] Scope matches linked issue intent
- [ ] Acceptance criteria satisfied
- [ ] Test evidence adequate for risk level
- [ ] No sensitive data or secrets introduced
"""

INITIAL_PROMPT_TEMPLATES: dict[str, str] = {
    "new": """\
This project has a `.collab/` collaboration workspace. Before doing anything:

1. Read everything in `.collab/`: start with `collab-contract.md`, then `kanban-board.md`,
   `context.md`, and any summaries in `session-summaries/`.
2. Commit to memory the session trigger phrases and their protocols from `collab-contract.md`:
   `OPEN SESSION`, `SAVE SESSION`, `CLOSE SESSION`, and `SAVE CHAT`.
3. The kanban board is empty — this is a new project. Wait for my direction before
   drafting plans or tasks.
""",
    "existing": """\
This project has a `.collab/` collaboration workspace. Before doing anything:

1. Read everything in `.collab/`: start with `collab-contract.md`, then `kanban-board.md`,
   `context.md`, and any summaries in `session-summaries/`.
2. Commit to memory the session trigger phrases and their protocols from `collab-contract.md`:
   `OPEN SESSION`, `SAVE SESSION`, `CLOSE SESSION`, and `SAVE CHAT`.
3. Do a brief, non-destructive recon of the repo: purpose, primary languages, entry points,
   build/test commands, and existing documentation. Do not restructure or rename anything.
4. If the kanban board is empty, add initial recon tasks to **Inbox** and wait for my approval
   before making any changes.

Your first responsibility is to understand the current state, not change it.
""",
}

_ADO_PR_TEMPLATE = """\
## Summary

<!-- What changed, in plain language? -->

-

## Why

<!-- Why this change is needed (bug fix, feature, risk reduction, maintenance). -->

-

## Linked Work Item(s)

AB#

## Validation

How was this verified?

- [ ] Unit tests
- [ ] Integration/end-to-end tests
- [ ] Manual verification
- [ ] CI/pipeline checks passed

Evidence (commands, screenshots, logs, links):

```text
```

## Risk Assessment

- Functional regression: low / medium / high
- Security impact: none / low / medium / high
- Deployment risk: low / medium / high

## Reviewer Checklist

- [ ] Scope matches linked work item intent
- [ ] Acceptance criteria satisfied
- [ ] Test evidence adequate for risk level
- [ ] No sensitive data or secrets introduced
"""

PLATFORM_FILES: dict[str, dict[str, str]] = {
    "github": {
        ".github/ISSUE_TEMPLATE/issue-template.md": _GITHUB_ISSUE_TEMPLATE,
        ".github/pull_request_template.md": _GITHUB_PR_TEMPLATE,
    },
    "gitlab": {
        ".gitlab/issue_templates/issue-template.md": _GITLAB_ISSUE_TEMPLATE,
        ".gitlab/merge_request_templates/merge-request-template.md": _GITLAB_MR_TEMPLATE,
    },
    "azure-devops": {
        ".azuredevops/pull_request_template.md": _ADO_PR_TEMPLATE,
    },
    "none": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WINDOWS_RESERVED_NAMES = frozenset({
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
})
INVALID_FOLDER_CHARS = re.compile(r'[\\/:*?"<>|]')


def valid_project_name(name: str) -> bool:
    if not name or not name.strip():
        return False
    if INVALID_FOLDER_CHARS.search(name):
        return False
    if name.upper() in WINDOWS_RESERVED_NAMES:
        return False
    if name.endswith(" ") or name.endswith("."):
        return False
    return True


def suggest_project_name_from_target(target_root: Path) -> str:
    candidate = INVALID_FOLDER_CHARS.sub("-", target_root.name).strip(". ")
    if valid_project_name(candidate):
        return candidate
    return "my-project"


def prompt_nav(prompt_text: str) -> str:
    """Input wrapper that raises BackSignal on 'b' and QuitSignal on 'q'."""
    try:
        value = input(prompt_text).strip()
    except EOFError:
        raise QuitSignal
    if value.lower() == "q":
        raise QuitSignal
    if value.lower() == "b":
        raise BackSignal
    return value


def prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        try:
            value = input(prompt).strip()
        except EOFError:
            raise QuitSignal
        low = value.lower()
        if low == "q":
            raise QuitSignal
        if low == "b":
            raise BackSignal
        if value in valid:
            return value
        print(f"  Invalid. Enter one of: {', '.join(sorted(valid))}.")


def prompt_for_mode() -> str:
    print("\nWhat are you initializing?")
    print("  [1] New project")
    print("  [2] Existing project  (add .collab/ to a project that already exists)")
    print("  [3] Upgrade existing scaffold  (add new files to an existing .collab/)")
    print("  " + "─" * 52)
    print("  [q] Quit")
    choices = {"1": "new", "2": "existing", "3": "upgrade"}
    choice = prompt_choice("Select [1-3]: ", set(choices))
    return choices[choice]


def prompt_for_target_root() -> Path:
    cwd = Path.cwd().resolve()
    print("\nWhere should it be installed?")
    print(f"  [1] Current directory  ({cwd})")
    print("  [2] Another directory")
    print("  " + "─" * 40)
    print("  [b] Back   [q] Quit")
    choice = prompt_choice("Select [1-2]: ", {"1", "2"})

    if choice == "1":
        return cwd

    print("\nEnter the full path to your target directory.")
    print("  Tip: supports ~, relative paths, or absolute paths.")
    print("  Type [b] to go back, [q] to quit.")
    while True:
        raw = prompt_nav("Path: ")
        if not raw:
            print("  Path cannot be empty.")
            continue
        target = Path(raw).expanduser().resolve()
        if not target.exists():
            print(f"  Directory not found: {target}")
            print("  Check the path or create the directory first, then try again.")
            continue
        if not target.is_dir():
            print(f"  That path exists but is a file, not a directory: {target}")
            continue
        print(f"  Resolved: {target}")
        return target


def prompt_for_new_project_name(default_name: str) -> str:
    print("\nProject name")
    print(f"  Press Enter to use the suggested name.")
    print("  " + "─" * 48)
    print("  [b] Back   [q] Quit")
    while True:
        name = prompt_nav(f"Name [{default_name}]: ")
        if not name:
            return default_name
        if not valid_project_name(name):
            print(
                '  Invalid name. Cannot contain \\ / : * ? " < > |\n'
                "  or be a Windows reserved name (CON, NUL, etc.)."
            )
            continue
        return name


def prompt_for_governance() -> str:
    print("\nGovernance mode  (controls how strict the workflow rules are):")
    print("  [1] None        — no rules at all, blank slate")
    print("  [2] Lightweight — minimal process, good for solo/prototype work")
    print("  [3] Standard    — balanced workflow, recommended for most projects")
    print("  [4] Strict      — full process gates, for compliance or team work")
    print("  " + "─" * 52)
    print("  [b] Back   [q] Quit   (Enter = Standard)")
    choices = {"1": "none", "2": "lightweight", "3": "standard", "4": "strict"}
    while True:
        value = prompt_nav("Select [1-4]: ").strip()
        if not value:
            return "standard"
        if value in choices:
            return choices[value]
        print("  Invalid. Enter 1, 2, 3, or 4 — or press Enter for Standard.")


def prompt_for_platform() -> str:
    print("\nGit platform  (generates issue/PR templates for your platform):")
    print("  [1] GitHub")
    print("  [2] GitLab")
    print("  [3] Azure DevOps")
    print("  [4] None / not using one")
    print("  " + "─" * 44)
    print("  [b] Back   [q] Quit   (Enter = None)")
    choices = {"1": "github", "2": "gitlab", "3": "azure-devops", "4": "none"}
    while True:
        value = prompt_nav("Select [1-4]: ").strip()
        if not value:
            return "none"
        if value in choices:
            return choices[value]
        print("  Invalid. Enter 1, 2, 3, or 4 — or press Enter to skip.")


def prompt_for_license() -> str:
    print("\nLicense  (adds a LICENSE file to your project root):")
    print("  [1] MIT          — permissive, short, very common")
    print("  [2] Apache-2.0   — permissive, includes patent grant")
    print("  [3] GPL-3.0      — copyleft, strong share-alike")
    print("  [4] AGPL-3.0     — copyleft, network use also triggers share-alike")
    print("  [5] BSD-2-Clause — permissive, minimal")
    print("  [6] BSD-3-Clause — permissive, adds no-endorsement clause")
    print("  [7] MPL-2.0      — weak copyleft, file-level only")
    print("  [8] Unlicense    — public domain, no restrictions")
    print("  [9] None         — skip LICENSE file")
    print("  " + "─" * 44)
    print("  [b] Back   [q] Quit   (Enter = None)")
    choices = {
        "1": "mit",
        "2": "apache-2.0",
        "3": "gpl-3.0",
        "4": "agpl-3.0",
        "5": "bsd-2-clause",
        "6": "bsd-3-clause",
        "7": "mpl-2.0",
        "8": "unlicense",
        "9": "none",
    }
    while True:
        value = prompt_nav("Select [1-9]: ").strip()
        if not value:
            return "none"
        if value in choices:
            return choices[value]
        print("  Invalid. Enter 1–9 or press Enter to skip.")


def prompt_for_description() -> str:
    print("\nProject description  (optional, one sentence):")
    print("  This gets injected into your context.md so agents know what the project is.")
    print("  " + "─" * 56)
    print("  [b] Back   [q] Quit   (Enter = skip)")
    value = prompt_nav("Description: ").strip()
    return value


def prompt_for_ticket_prefix() -> str:
    print("\nTask ID prefix  (3-5 alphanumeric characters, e.g. SCAF, PROD):")
    print("  Used in the kanban board: PREFIX-001, PREFIX-002, etc.")
    print("  Unique prefixes help distinguish tasks across multiple projects.")
    print("  " + "─" * 56)
    print("  [b] Back   [q] Quit   (Enter = use TASK)")
    while True:
        raw = prompt_nav("Prefix [TASK]: ").strip().upper()
        if raw in ("B", "Q"):
            raise BackSignal() if raw == "B" else QuitSignal()
        if raw == "":
            return "TASK"
        if raw.isalnum() and 3 <= len(raw) <= 5:
            return raw
        print("  Must be 3–5 alphanumeric characters (letters and numbers only).")


# ---------------------------------------------------------------------------
# Interactive wizard
# ---------------------------------------------------------------------------

_WIZARD_ORDER = ["mode", "target", "name", "governance", "platform", "license", "description", "ticket_prefix", "confirm"]


def _wizard_should_skip(step: str, collected: dict) -> bool:
    if step == "name" and collected.get("mode") != "new":
        return True
    if step == "license" and collected.get("platform", "none") == "none":
        return True
    return False


def _next_wizard_step(current: str, collected: dict) -> str | None:
    idx = _WIZARD_ORDER.index(current) + 1
    while idx < len(_WIZARD_ORDER):
        candidate = _WIZARD_ORDER[idx]
        if not _wizard_should_skip(candidate, collected):
            return candidate
        idx += 1
    return None


def _wizard_run_step(step: str, collected: dict, args: argparse.Namespace) -> object:
    if step == "mode":
        return prompt_for_mode()
    if step == "target":
        return prompt_for_target_root()
    if step == "name":
        default = suggest_project_name_from_target(collected["target"])
        return prompt_for_new_project_name(default)
    if step == "governance":
        return prompt_for_governance()
    if step == "platform":
        return prompt_for_platform()
    if step == "license":
        return prompt_for_license()
    if step == "description":
        return prompt_for_description()
    if step == "ticket_prefix":
        return prompt_for_ticket_prefix()
    if step == "confirm":
        return _wizard_confirm(collected, args)
    raise ValueError(f"Unknown wizard step: {step}")


def _wizard_confirm(collected: dict, args: argparse.Namespace) -> object:
    mode = collected["mode"]
    target = collected["target"]
    if mode == "new":
        name = collected["name"]
        target_root = (target / name).resolve()
    else:
        target_root = target
        name = suggest_project_name_from_target(target_root)

    timestamp = now_tz().strftime("%m.%d.%Y")

    print("\n╔══════════════════════════════════╗")
    print("║             Summary              ║")
    print("╚══════════════════════════════════╝")
    print(f"  Mode:        {'New project' if mode == 'new' else 'Existing project'}")
    print(f"  Target:      {target_root}")
    if mode == "new":
        print(f"  Name:        {name}")
    print(f"  Governance:  {collected['governance']}")
    print(f"  Platform:    {collected['platform']}")
    print(f"  License:     {collected.get('license', 'none')}")
    desc = collected.get("description", "")
    if desc:
        print(f"  Description: {desc}")
    print(f"  Task prefix: {collected.get('ticket_prefix', 'TASK')}")
    print(f"  Date:        {timestamp} (America/New_York)")
    if target_root.exists() and not args.force:
        print("\n  Note: Target already exists. Existing files will be skipped.")
        print("  Run with --force to overwrite them.")

    if args.dry_run:
        return _CONFIRMED  # skip prompt — main() will show planned actions

    print("\n  [b] Back   [q] Quit")
    while True:
        raw = prompt_nav("Proceed? [y/N]: ").lower()
        if raw == "y":
            return _CONFIRMED
        if raw in ("n", ""):
            return _ABORT
        print("  Please enter y to proceed or N to cancel.")


def _print_header() -> None:
    print("\n╔════════════════════════════════════════╗")
    print("║                scaffy                  ║")
    print("║  Multi-agent project workspace setup   ║")
    print("╚════════════════════════════════════════╝")
    print("\nSets up a .collab/ workspace for AI-assisted projects.")
    print("At any prompt: type  b  to go back,  q  to quit.\n")


def _run_interactive_wizard(args: argparse.Namespace) -> dict | None:
    """Drive the step-by-step interactive wizard. Returns collected values or None if aborted."""
    _print_header()

    collected: dict = {}
    visited: list[str] = []
    step: str | None = "mode"

    while step is not None:
        if _wizard_should_skip(step, collected):
            step = _next_wizard_step(step, collected)
            continue

        try:
            value = _wizard_run_step(step, collected, args)

            if value is _ABORT:
                print("Aborted.")
                return None

            if step != "confirm":
                collected[step] = value
            visited.append(step)

            # Upgrade only needs mode + target — return early
            if step == "target" and collected.get("mode") == "upgrade":
                return collected

            if value is _CONFIRMED:
                return collected

            step = _next_wizard_step(step, collected)

        except BackSignal:
            if not visited:
                print("\n  (Already at the first step — nothing to go back to.)\n")
                # step unchanged — re-run the same step
            else:
                prev = visited.pop()
                collected.pop(prev, None)
                step = prev

        except QuitSignal:
            print("\nAborted.")
            return None

    return collected


def render_template(
    content: str,
    *,
    project_name: str,
    description: str,
    governance_mode: str,
    platform: str,
    license_id: str,
    date: str,
    ticket_prefix: str = "TASK",
) -> str:
    description_rendered = description if description else "<!-- Add a brief description of this project -->"
    replacements = {
        "{project_name}": project_name,
        "{description}": description_rendered,
        "{governance_mode}": governance_mode,
        "{platform}": platform,
        "{license}": license_id,
        "{date}": date,
        "{ticket_prefix}": ticket_prefix,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


# ---------------------------------------------------------------------------
# Save-chat — Claude Code session transcript export
# ---------------------------------------------------------------------------

_CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
_CODEX_STATE_DB = Path.home() / ".codex" / "state_5.sqlite"
_GEMINI_TMP_DIR = Path.home() / ".gemini" / "tmp"


def _detect_agent() -> str | None:
    """Detect which AI agent CLI is currently running scaffy. Returns None if unknown."""
    env = os.environ
    if env.get("CLAUDECODE") or env.get("AI_AGENT", "").startswith("claude"):
        return "claude"
    if env.get("GEMINI_CLI") == "1":
        return "gemini"
    # Codex sets no env vars — walk parent process tree (Linux/macOS)
    try:
        pid = os.getppid()
        visited: set[int] = set()
        while pid and pid > 1 and pid not in visited:
            visited.add(pid)
            comm = Path(f"/proc/{pid}/comm")
            if comm.exists() and "codex" in comm.read_text().lower():
                return "codex"
            status = Path(f"/proc/{pid}/status")
            if not status.exists():
                break
            for line in status.read_text().splitlines():
                if line.startswith("PPid:"):
                    pid = int(line.split()[1])
                    break
            else:
                break
    except (OSError, ValueError):
        pass
    return None


def _find_claude_project_dir(cwd: Path) -> Path | None:
    slug = str(cwd).replace("/", "-")
    candidate = _CLAUDE_PROJECTS_DIR / slug
    return candidate if candidate.is_dir() else None


def _load_jsonl(jsonl_path: Path) -> list[dict]:
    entries: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def _render_chat_content(content) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return str(content)
    parts: list[str] = []
    for block in content:
        btype = block.get("type", "")
        if btype == "text":
            text = block.get("text", "").strip()
            if text:
                parts.append(text)
        elif btype == "tool_result":
            tool_id = block.get("tool_use_id", "?")
            inner = block.get("content", "")
            is_error = block.get("is_error", False)
            label = "TOOL RESULT (error)" if is_error else "TOOL RESULT"
            if isinstance(inner, str):
                result_text = inner.strip()
            elif isinstance(inner, list):
                texts: list[str] = []
                for ib in inner:
                    if ib.get("type") == "text":
                        texts.append(ib.get("text", "").strip())
                    elif ib.get("type") == "tool_reference":
                        texts.append(f"[tool_reference: {ib.get('tool_name', '?')}]")
                result_text = "\n".join(texts)
            else:
                result_text = str(inner)
            parts.append(f"> **{label}** `{tool_id[:8]}`\n>\n> ```\n{result_text}\n```")
        # skip "thinking" blocks — content is encrypted/opaque
    return "\n\n".join(parts)


def _render_tool_use(block: dict) -> str:
    name = block.get("name", "?")
    inp = block.get("input", {})
    return f"**Tool:** `{name}`\n```json\n{json.dumps(inp, indent=2)}\n```"


def _session_to_markdown(entries: list[dict], session_id: str) -> str:
    lines: list[str] = [
        "# Claude Code Session Transcript",
        f"\n**Session:** `{session_id}`",
    ]
    for e in entries:
        if e.get("type") in ("user", "assistant") and e.get("timestamp"):
            ts = e["timestamp"]
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(TZ)
            lines.append(f"**Date:** {dt.strftime('%m.%d.%Y %H:%M %Z')}")
            break
    lines.append("\n---\n")

    for entry in entries:
        etype = entry.get("type")
        sidechain_note = " *(sub-agent)*" if entry.get("isSidechain") else ""

        if etype == "user":
            rendered = _render_chat_content(entry["message"].get("content", ""))
            if rendered:
                lines.append(f"## User{sidechain_note}\n")
                lines.append(rendered)
                lines.append("")

        elif etype == "assistant":
            content = entry["message"].get("content", [])
            if not isinstance(content, list):
                continue
            text_blocks: list[str] = []
            tool_blocks: list[dict] = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    text = block.get("text", "").strip()
                    if text:
                        text_blocks.append(text)
                elif btype == "tool_use":
                    tool_blocks.append(block)
            if text_blocks or tool_blocks:
                lines.append(f"## Assistant{sidechain_note}\n")
                for t in text_blocks:
                    lines.append(t)
                    lines.append("")
                for tb in tool_blocks:
                    lines.append(_render_tool_use(tb))
                    lines.append("")

    return "\n".join(lines)


def save_chat(target_root: Path, session_id: str | None = None, list_sessions: bool = False) -> None:
    """Export the current (or specified) Claude Code session to .collab/chat-logs/."""
    project_dir = _find_claude_project_dir(target_root)
    if project_dir is None:
        slug = str(target_root).replace("/", "-")
        print(f"Error: No Claude project dir found for {target_root}", file=sys.stderr)
        print(f"Expected: {_CLAUDE_PROJECTS_DIR / slug}", file=sys.stderr)
        sys.exit(1)

    if list_sessions:
        files = sorted(project_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        print(f"Recent sessions in {project_dir}:\n")
        for f in files[:10]:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=TZ).strftime("%m.%d.%Y %H:%M")
            size_kb = f.stat().st_size // 1024
            print(f"  {f.stem[:8]}...  {mtime}  {size_kb} KB")
        print("\nTo save a specific session: scaffy --save-chat --session-id <prefix>")
        return

    if session_id:
        matches = list(project_dir.glob(f"{session_id}*.jsonl"))
        if not matches:
            print(f"Error: No session matching '{session_id}' in {project_dir}", file=sys.stderr)
            sys.exit(1)
        jsonl_path = sorted(matches, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    else:
        files = sorted(project_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            print("Error: No sessions found.", file=sys.stderr)
            sys.exit(1)
        jsonl_path = files[0]

    sid = jsonl_path.stem
    entries = _load_jsonl(jsonl_path)
    md = _session_to_markdown(entries, sid)

    chat_logs_dir = target_root / ".collab" / "chat-logs"
    chat_logs_dir.mkdir(parents=True, exist_ok=True)

    today = now_tz().strftime("%m.%d.%Y")
    out_path = chat_logs_dir / f"{today}-claude-chat.md"
    if out_path.exists():
        seq = 2
        while True:
            candidate = chat_logs_dir / f"{today}-{seq:02d}-claude-chat.md"
            if not candidate.exists():
                out_path = candidate
                break
            seq += 1

    out_path.write_text(md, encoding="utf-8")
    print(f"Saved: {out_path}  ({len(md):,} chars, {len(entries)} entries)")


def _load_codex_sessions(state_db: Path = _CODEX_STATE_DB) -> list[dict]:
    """Return Codex sessions from state_5.sqlite, newest first."""
    if not state_db.exists():
        return []
    conn = sqlite3.connect(state_db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        select id, rollout_path, cwd, title, created_at_ms, updated_at_ms,
               model, cli_version, first_user_message
        from threads
        where rollout_path is not null and rollout_path != ''
        order by updated_at_ms desc, created_at_ms desc, id desc
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _codex_iso_from_ms(value: int | None) -> str:
    if value is None:
        return "unknown"
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).astimezone(TZ).strftime("%m.%d.%Y %H:%M %Z")


def _codex_flatten_content(content: list[dict]) -> str:
    parts: list[str] = []
    for item in content:
        t = item.get("type")
        if t in ("input_text", "output_text"):
            parts.append(str(item.get("text", "")))
        else:
            parts.append(json.dumps(item, ensure_ascii=False, indent=2))
    return "\n".join(p for p in parts if p).strip()


def _codex_rollout_to_markdown(session: dict, events: list[dict], max_output_chars: int = 6000) -> str:
    lines: list[str] = [
        "# Codex Session Transcript",
        f"\n**Session:** `{session['id']}`",
        f"**Started:** {_codex_iso_from_ms(session.get('created_at_ms'))}",
        f"**Ended:** {_codex_iso_from_ms(session.get('updated_at_ms'))}",
        f"**Model:** `{session.get('model') or 'unknown'}`",
        f"**Working directory:** `{session.get('cwd') or 'unknown'}`",
        "\n---\n",
    ]

    for event in events:
        event_type = event.get("type")
        payload = event.get("payload", {})

        if event_type != "response_item":
            continue

        ptype = payload.get("type")

        if ptype == "message":
            role = payload.get("role", "unknown")
            if role in ("system", "developer"):
                continue
            text = _codex_flatten_content(payload.get("content", []))
            if not text:
                continue
            label = role.capitalize()
            if payload.get("phase") and role == "assistant":
                label = f"{label} ({payload['phase']})"
            lines.extend([f"## {label}\n", text, ""])

        elif ptype in ("function_call", "custom_tool_call"):
            tool_name = payload.get("name", "unknown")
            raw_input = payload.get("arguments") if ptype == "function_call" else payload.get("input")
            if isinstance(raw_input, str):
                try:
                    raw_input = json.dumps(json.loads(raw_input), indent=2)
                except json.JSONDecodeError:
                    pass
            elif raw_input is not None:
                raw_input = json.dumps(raw_input, indent=2)
            lines.extend([f"### Tool Call: `{tool_name}`\n", f"```json\n{raw_input or '(no input)'}\n```", ""])

        elif ptype in ("function_call_output", "custom_tool_call_output"):
            output = payload.get("output", "")
            if isinstance(output, str):
                try:
                    loaded = json.loads(output)
                    if not isinstance(loaded, str):
                        output = json.dumps(loaded, indent=2)
                except json.JSONDecodeError:
                    pass
            else:
                output = json.dumps(output, indent=2)
            if len(output) > max_output_chars:
                omitted = len(output) - max_output_chars
                output = f"{output[:max_output_chars].rstrip()}\n\n... [truncated {omitted} chars]"
            lines.extend(["### Tool Output\n", f"```\n{output}\n```", ""])

    return "\n".join(lines)


def save_chat_codex(target_root: Path, session_id: str | None = None, list_sessions: bool = False) -> None:
    """Export the most recent (or specified) Codex session to .collab/chat-logs/."""
    if not _CODEX_STATE_DB.exists():
        print(f"Error: Codex state DB not found: {_CODEX_STATE_DB}", file=sys.stderr)
        print("Is Codex CLI installed and has it been run at least once?", file=sys.stderr)
        sys.exit(1)

    sessions = _load_codex_sessions()

    if list_sessions:
        if not sessions:
            print("No Codex sessions found.")
            return
        print(f"Recent Codex sessions ({_CODEX_STATE_DB}):\n")
        for s in sessions[:10]:
            preview = (s.get("first_user_message") or "")[:80]
            print(f"  {s['id']}  {_codex_iso_from_ms(s.get('created_at_ms'))}  {preview}")
        print("\nTo save a specific session: scaffy --save-chat --session-id <prefix>")
        return

    if not sessions:
        print("Error: No Codex sessions found.", file=sys.stderr)
        sys.exit(1)

    if session_id:
        matches = [s for s in sessions if s["id"].startswith(session_id)]
        if not matches:
            print(f"Error: No Codex session matching '{session_id}'", file=sys.stderr)
            sys.exit(1)
        record = matches[0]
    else:
        record = sessions[0]

    rollout_path = Path(record["rollout_path"])
    if not rollout_path.exists():
        print(f"Error: Rollout file not found: {rollout_path}", file=sys.stderr)
        sys.exit(1)

    events = _load_jsonl(rollout_path)
    md = _codex_rollout_to_markdown(record, events)

    chat_logs_dir = target_root / ".collab" / "chat-logs"
    chat_logs_dir.mkdir(parents=True, exist_ok=True)

    today = now_tz().strftime("%m.%d.%Y")
    out_path = chat_logs_dir / f"{today}-codex-chat.md"
    if out_path.exists():
        seq = 2
        while True:
            candidate = chat_logs_dir / f"{today}-{seq:02d}-codex-chat.md"
            if not candidate.exists():
                out_path = candidate
                break
            seq += 1

    out_path.write_text(md, encoding="utf-8")
    print(f"Saved: {out_path}  ({len(md):,} chars, {len(events)} events)")


def _find_gemini_session_files(cwd: Path) -> list[Path]:
    """Return Gemini session JSONL files for cwd's project, newest first.
    Checks both hash-based and name-based project dirs (Gemini changed formats)."""
    if not _GEMINI_TMP_DIR.exists():
        return []
    project_hash = hashlib.sha256(str(cwd).encode()).hexdigest()
    candidates: list[Path] = []
    for d in _GEMINI_TMP_DIR.iterdir():
        if not d.is_dir():
            continue
        if d.name in (project_hash, cwd.name):
            candidates.extend(d.glob("chats/*.jsonl"))
    return sorted(candidates, key=lambda f: f.stat().st_mtime, reverse=True)


def _all_gemini_session_files() -> list[Path]:
    """Return all Gemini session JSONL files across all projects, newest first."""
    if not _GEMINI_TMP_DIR.exists():
        return []
    return sorted(
        _GEMINI_TMP_DIR.glob("*/chats/*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )


def _gemini_session_to_markdown(events: list[dict], source: str) -> str:
    sid, started = "unknown", "unknown"
    for e in events:
        if "sessionId" in e and "projectHash" in e:
            sid = e.get("sessionId", "unknown")
            started = e.get("startTime", "unknown")
            break
    lines: list[str] = [
        "# Gemini Session Transcript",
        f"\n**Session:** `{sid}`",
        f"**Started:** {started}",
        f"**Source:** `{source}`",
        "\n---\n",
    ]
    for e in events:
        etype = e.get("type")
        if etype == "user":
            text = "".join(c.get("text", "") for c in e.get("content", []) if "text" in c).strip()
            if text:
                lines.extend(["## User\n", text, ""])
        elif etype == "gemini":
            content = e.get("content", "")
            if content:
                lines.extend(["## Gemini\n", content, ""])
            for tool in e.get("toolCalls", []):
                name = tool.get("name", "unknown")
                args = tool.get("args", {})
                lines.extend([f"### Tool Call: `{name}`\n", f"```json\n{json.dumps(args, indent=2)}\n```", ""])
    return "\n".join(lines)


def save_chat_gemini(target_root: Path, session_id: str | None = None, list_sessions: bool = False) -> None:
    """Export the most recent (or specified) Gemini session to .collab/chat-logs/."""
    if not _GEMINI_TMP_DIR.exists():
        print(f"Error: Gemini tmp dir not found: {_GEMINI_TMP_DIR}", file=sys.stderr)
        print("Is Gemini CLI installed and has it been run at least once?", file=sys.stderr)
        sys.exit(1)

    if list_sessions:
        all_files = _all_gemini_session_files()
        if not all_files:
            print("No Gemini sessions found.")
            return
        print(f"Recent Gemini sessions ({_GEMINI_TMP_DIR}):\n")
        for f in all_files[:10]:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=TZ).strftime("%m.%d.%Y %H:%M %Z")
            preview = ""
            try:
                for line in f.open():
                    try:
                        e = json.loads(line)
                        if e.get("type") == "user":
                            preview = "".join(c.get("text", "") for c in e.get("content", []))[:80]
                            break
                    except json.JSONDecodeError:
                        pass
            except OSError:
                pass
            print(f"  {f.stem[:36]}  {mtime}  {preview}")
        print("\nTo save a specific session: scaffy --save-chat --session-id <prefix>")
        return

    if session_id:
        all_files = _all_gemini_session_files()
        matches = [f for f in all_files if session_id in f.stem]
        if not matches:
            print(f"Error: No Gemini session matching '{session_id}'", file=sys.stderr)
            sys.exit(1)
        jsonl_path = matches[0]
    else:
        project_files = _find_gemini_session_files(target_root)
        all_files = _all_gemini_session_files()
        candidates = project_files or all_files
        if not candidates:
            print("Error: No Gemini sessions found.", file=sys.stderr)
            sys.exit(1)
        jsonl_path = candidates[0]

    events = _load_jsonl(jsonl_path)
    md = _gemini_session_to_markdown(events, str(jsonl_path))

    chat_logs_dir = target_root / ".collab" / "chat-logs"
    chat_logs_dir.mkdir(parents=True, exist_ok=True)

    today = now_tz().strftime("%m.%d.%Y")
    out_path = chat_logs_dir / f"{today}-gemini-chat.md"
    if out_path.exists():
        seq = 2
        while True:
            candidate = chat_logs_dir / f"{today}-{seq:02d}-gemini-chat.md"
            if not candidate.exists():
                out_path = candidate
                break
            seq += 1

    out_path.write_text(md, encoding="utf-8")
    print(f"Saved: {out_path}  ({len(md):,} chars, {len(events)} events)")


def safe_write(dest: Path, content: str, force: bool) -> None:
    if dest.exists() and not force:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    if dest.suffix in {".sh", ".py"}:
        try:
            dest.chmod(0o755)
        except OSError:
            pass


def ensure_required_directories(target_root: Path, mode: str) -> None:
    required_dirs = [
        target_root / ".collab" / "brainstorms",
        target_root / ".collab" / "audit",
        target_root / ".collab" / "chat-logs",
        target_root / ".collab" / "guides",
        target_root / ".collab" / "project-plans",
        target_root / ".collab" / "session-summaries",
        target_root / ".collab" / "skills",
        target_root / ".collab" / "supporting-artifacts",
        target_root / ".collab" / "prompts",
        target_root / ".collab" / "playbooks",
        target_root / ".collab" / "playbooks" / "templates",
    ]
    for path in required_dirs:
        path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def _parse_project_yaml(yaml_path: Path) -> dict[str, str]:
    """Minimal YAML parser for project.yaml (key: value, one per line)."""
    data: dict[str, str] = {}
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return data


def _migrate_git_management(collab_dir: Path, dry_run: bool) -> list[str]:
    """Move .collab/git-management/ files to guides/ and playbooks/templates/. Returns log lines."""
    git_mgmt_dir = collab_dir / "git-management"
    log: list[str] = []

    if not git_mgmt_dir.exists():
        return log

    moves = [
        (git_mgmt_dir / "git-guidelines.md",      collab_dir / "guides" / "git-guidelines.md"),
        (git_mgmt_dir / "issue-template.md",       collab_dir / "playbooks" / "templates" / "issue-template.md"),
        (git_mgmt_dir / "pull-request-template.md", collab_dir / "playbooks" / "templates" / "pull-request-template.md"),
    ]

    for src, dst in moves:
        if src.exists() and not dst.exists():
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                src.rename(dst)
            log.append(f"  rename .collab/git-management/{src.name} → {dst.relative_to(collab_dir.parent)}")

    # Remove git-management/ if now empty
    if not dry_run and git_mgmt_dir.exists():
        remaining = list(git_mgmt_dir.iterdir())
        if not remaining:
            git_mgmt_dir.rmdir()
            log.append("  rmdir  .collab/git-management/ (empty after migration)")
        else:
            log.append(f"  note   .collab/git-management/ not removed — {len(remaining)} file(s) remain")

    return log


def _migrate_ideas_to_brainstorms(collab_dir: Path, dry_run: bool) -> list[str]:
    """Rename .collab/ideas/ or .collab/brainstorm/ → .collab/brainstorms/ if present. Returns log lines."""
    ideas_dir = collab_dir / "ideas"
    brainstorm_dir = collab_dir / "brainstorm"
    brainstorms_dir = collab_dir / "brainstorms"
    log: list[str] = []

    # Migrate ideas/ → brainstorms/ (legacy v1 scaffolds)
    if ideas_dir.exists() and not brainstorms_dir.exists():
        old_template = ideas_dir / "idea-template.md"
        new_template = ideas_dir / "brainstorm-template.md"
        if not dry_run:
            if old_template.exists() and not new_template.exists():
                old_template.rename(new_template)
            ideas_dir.rename(brainstorms_dir)
        log.append("  rename .collab/ideas/ → .collab/brainstorms/")
        if old_template.exists() or dry_run:
            log.append("  rename .collab/brainstorms/idea-template.md → brainstorm-template.md")
        return log

    # Migrate brainstorm/ → brainstorms/ (v1.5–v1.8 scaffolds)
    if brainstorm_dir.exists() and not brainstorms_dir.exists():
        if not dry_run:
            brainstorm_dir.rename(brainstorms_dir)
        log.append("  rename .collab/brainstorm/ → .collab/brainstorms/")
        return log

    return log


def upgrade_scaffold(target_root: Path, force: bool, dry_run: bool) -> None:
    """Upgrade an existing .collab/ scaffold to the latest templates."""
    collab_dir = target_root / ".collab"
    yaml_path = collab_dir / "project.yaml"

    if not collab_dir.is_dir():
        print(f"Error: No .collab/ directory found in {target_root}")
        print("Use 'scaffy' without --upgrade to create a new scaffold.")
        return

    if not yaml_path.is_file():
        print(f"Error: No project.yaml found in {collab_dir}")
        print("Cannot determine original scaffold settings. Aborting.")
        return

    meta = _parse_project_yaml(yaml_path)
    project_name = meta.get("project", target_root.name)
    governance_mode = meta.get("governance_mode", "standard")
    platform = meta.get("platform", "none")
    license_id = meta.get("license", "none")
    ticket_prefix = meta.get("ticket_prefix", "TASK")

    timestamp = meta.get("created", now_tz().strftime("%m.%d.%Y"))
    description = ""

    render_kwargs = dict(
        project_name=project_name,
        description=description,
        governance_mode=governance_mode,
        platform=platform,
        license_id=license_id,
        date=timestamp,
        ticket_prefix=ticket_prefix,
    )

    # Determine the mode based on whether .collab/ was a new or existing project.
    # For upgrade purposes, we always treat it as existing (project already has files).
    mode = "existing"

    # Build the full file manifest that scaffy would generate today
    files_to_check: dict[Path, str] = {}

    for rel_path, content in TEMPLATE_FILES.items():
        rendered = render_template(content, **render_kwargs)
        if rel_path == ".gitignore":
            # During upgrade, never touch an existing .gitignore
            gitignore_dest = target_root / ".gitignore"
            if gitignore_dest.exists():
                files_to_check[collab_dir / ".gitignore.template"] = rendered
            else:
                files_to_check[gitignore_dest] = rendered
        else:
            files_to_check[target_root / rel_path] = rendered

    # Initial prompt
    prompt_content = render_template(INITIAL_PROMPT_TEMPLATES[mode], **render_kwargs)
    files_to_check[collab_dir / "prompts" / "initial-prompt.md"] = prompt_content

    # Platform files
    for rel_path, content in PLATFORM_FILES.get(platform, {}).items():
        files_to_check[target_root / rel_path] = content

    # License
    if license_id != "none":
        files_to_check[target_root / "LICENSE"] = LICENSE_TEXTS[license_id]

    # Directories
    required_dirs = [
        collab_dir / "brainstorms",
        collab_dir / "audit",
        collab_dir / "guides",
        collab_dir / "project-plans",
        collab_dir / "session-summaries",
        collab_dir / "skills",
        collab_dir / "supporting-artifacts",
        collab_dir / "prompts",
        collab_dir / "playbooks",
        collab_dir / "playbooks" / "templates",
    ]

    # Execute
    added_dirs: list[str] = []
    added_files: list[str] = []
    skipped_files: list[str] = []
    updated_files: list[str] = []

    print(f"\nUpgrading scaffold in: {target_root}")
    print(f"  Settings from project.yaml: governance={governance_mode}, "
          f"platform={platform}, license={license_id}")
    print()

    migrated = _migrate_git_management(collab_dir, dry_run)
    migrated += _migrate_ideas_to_brainstorms(collab_dir, dry_run)

    for d in required_dirs:
        if not d.exists():
            if dry_run:
                added_dirs.append(f"  mkdir  {d.relative_to(target_root)}/")
            else:
                d.mkdir(parents=True, exist_ok=True)
                added_dirs.append(f"  mkdir  {d.relative_to(target_root)}/")

    for dest, content in files_to_check.items():
        rel = dest.relative_to(target_root) if dest.is_relative_to(target_root) else dest
        if dest.exists():
            if force:
                if dry_run:
                    updated_files.append(f"  update {rel}")
                else:
                    dest.write_text(content, encoding="utf-8")
                    updated_files.append(f"  update {rel}")
            else:
                skipped_files.append(f"  skip   {rel}")
        else:
            if dry_run:
                added_files.append(f"  add    {rel}")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
                added_files.append(f"  add    {rel}")

    # Report
    if migrated:
        print("Migrated:")
        print("\n".join(migrated))
    if added_dirs:
        print("New directories:")
        print("\n".join(added_dirs))
    if added_files:
        print("New files:")
        print("\n".join(added_files))
    if updated_files:
        print("Updated files (--force):")
        print("\n".join(updated_files))
    if skipped_files:
        print("Skipped (already exist):")
        print("\n".join(skipped_files))

    if not migrated and not added_dirs and not added_files and not updated_files:
        print("Everything is up to date. Nothing to do.")
    elif dry_run:
        print("\nDry run complete. No files written.")
    else:
        total = len(migrated) + len(added_dirs) + len(added_files) + len(updated_files)
        print(f"\nUpgrade complete. {total} item(s) added/updated/migrated.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize a multi-agent project scaffold.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--name", metavar="NAME", help="Project name (any valid folder name).")
    parser.add_argument("--path", metavar="PATH", help="Target directory where scaffold files will be installed.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--dry-run", action="store_true", help="Show planned actions without writing.")
    parser.add_argument(
        "--governance",
        metavar="MODE",
        choices=GOVERNANCE_MODES,
        default=None,
        help="Governance mode: lightweight, standard, or strict.",
    )
    parser.add_argument(
        "--platform",
        metavar="PLATFORM",
        choices=PLATFORM_MODES,
        default=None,
        help="Git platform: github, gitlab, azure-devops, or none. Default: none.",
    )
    parser.add_argument(
        "--license",
        metavar="LICENSE",
        choices=LICENSE_CHOICES,
        default=None,
        help=(
            "License to generate: mit, apache-2.0, gpl-3.0, agpl-3.0, "
            "bsd-2-clause, bsd-3-clause, mpl-2.0, unlicense, or none. Default: none."
        ),
    )
    parser.add_argument("--upgrade", action="store_true",
                        help="Upgrade an existing .collab/ scaffold to the latest templates.")
    parser.add_argument("--save-chat", action="store_true",
                        help="Export the current agent session to .collab/chat-logs/. Use --cli to specify the agent.")
    parser.add_argument("--session-id", metavar="UUID",
                        help="Session UUID prefix to export (--save-chat only). Default: most recent.")
    parser.add_argument("--list-chats", action="store_true",
                        help="List recent agent sessions (--save-chat mode). Use --cli to specify the agent.")
    parser.add_argument("--cli", choices=["claude", "codex", "gemini"], default=None,
                        help="Agent CLI to export sessions from (--save-chat mode). Auto-detected if omitted.")
    parser.add_argument("--init-git", action="store_true", help="Run git init in the project root after scaffolding.")
    parser.add_argument("--description", metavar="TEXT", default="", help="Short project description.")
    parser.add_argument("--ticket-prefix", metavar="PREFIX", default="", help="Task ID prefix (3-5 alphanumeric chars, e.g. SCAF). Default: TASK.")
    args = parser.parse_args()

    # --- Save-chat mode ---
    if args.save_chat or args.list_chats:
        target = Path(args.path).expanduser().resolve() if args.path else Path.cwd()
        cli = args.cli or _detect_agent()
        if cli is None:
            print("Could not auto-detect agent. Which CLI are you using?")
            print("  1) claude")
            print("  2) codex")
            print("  3) gemini")
            choice = input("Enter 1/2/3 or name: ").strip().lower()
            cli = {"1": "claude", "2": "codex", "3": "gemini"}.get(choice, choice)
            if cli not in ("claude", "codex", "gemini"):
                print(f"Unknown agent '{cli}'. Use --cli {{claude,codex,gemini}}.", file=sys.stderr)
                sys.exit(1)
        if cli == "codex":
            save_chat_codex(target, session_id=args.session_id, list_sessions=args.list_chats)
        elif cli == "gemini":
            save_chat_gemini(target, session_id=args.session_id, list_sessions=args.list_chats)
        else:
            save_chat(target, session_id=args.session_id, list_sessions=args.list_chats)
        return

    # --- Upgrade mode ---
    if args.upgrade:
        target = Path(args.path).expanduser().resolve() if args.path else Path.cwd()
        upgrade_scaffold(target, force=args.force, dry_run=args.dry_run)
        return

    if args.name and not valid_project_name(args.name):
        parser.error(
            'Invalid --name. Cannot contain \\ / : * ? " < > | '
            "or be a Windows reserved name (CON, NUL, etc.)."
        )

    fully_scripted = bool(args.name and args.path)

    if fully_scripted:
        mode = "new"
        project_name = args.name
        target_root = (Path(args.path).expanduser().resolve() / project_name).resolve()
        governance_mode = args.governance or "standard"
        platform = args.platform or "none"
        license_id = args.license or "none"
        description = args.description
        raw_prefix = (args.ticket_prefix or "").strip().upper()
        ticket_prefix = raw_prefix if (raw_prefix.isalnum() and 3 <= len(raw_prefix) <= 5) else "TASK"
    else:
        result = _run_interactive_wizard(args)
        if result is None:
            return

        mode = result["mode"]
        if mode == "upgrade":
            upgrade_scaffold(result["target"], force=args.force, dry_run=args.dry_run)
            return

        selected_root = result["target"]
        if mode == "new":
            project_name = result["name"]
            target_root = (selected_root / project_name).resolve()
        else:
            target_root = selected_root
            project_name = suggest_project_name_from_target(target_root)

        governance_mode = result["governance"]
        platform = result["platform"]
        license_id = result.get("license", "none")
        description = result.get("description", "")
        ticket_prefix = result.get("ticket_prefix", "TASK")

    # .gitignore fallback
    gitignore_dest = target_root / ".gitignore"
    if gitignore_dest.exists() and not args.force:
        effective_gitignore_dest = target_root / ".collab" / ".gitignore.template"
    else:
        effective_gitignore_dest = gitignore_dest

    timestamp = now_tz().strftime("%m.%d.%Y")

    render_kwargs = dict(
        project_name=project_name,
        description=description,
        governance_mode=governance_mode,
        platform=platform,
        license_id=license_id,
        date=timestamp,
        ticket_prefix=ticket_prefix,
    )

    # Scripted mode: print summary here (interactive mode shows summary in wizard confirm step)
    if fully_scripted:
        print("\nSummary")
        print("-------")
        print(f"Mode:       {'New project' if mode == 'new' else 'Existing project'}")
        print(f"Target:     {target_root}")
        if mode == "new":
            print(f"Name:       {project_name}")
        print(f"Governance: {governance_mode}")
        print(f"Platform:   {platform}")
        print(f"License:    {license_id}")
        print(f"Prefix:     {ticket_prefix}")
        print(f"Date:       {timestamp} (America/New_York)")
        if target_root.exists() and not args.dry_run and not args.force:
            print("Notice: Target exists. Existing files will be skipped. Use --force to overwrite.")

    if args.dry_run:
        def _dry_action(dest: Path) -> str:
            if dest.exists():
                return "overwrite" if args.force else "skip     "
            return "write    "

        print("\nPlanned actions:")
        for rel_path in TEMPLATE_FILES:
            dest = effective_gitignore_dest if rel_path == ".gitignore" else target_root / rel_path
            print(f"  {_dry_action(dest)} {dest}")
        dest = target_root / ".collab/prompts/initial-prompt.md"
        print(f"  {_dry_action(dest)} {dest}")
        for rel_path in PLATFORM_FILES.get(platform, {}):
            dest = target_root / rel_path
            print(f"  {_dry_action(dest)} {dest}")
        if license_id != "none":
            dest = target_root / "LICENSE"
            print(f"  {_dry_action(dest)} {dest}")
        if args.init_git:
            print(f"  git init  {target_root}")
        if not args.force and target_root.exists():
            print("\nNote: 'skip' entries already exist and will not be changed. Use --force to overwrite.")
        print("\nDry run complete. No files written.")
        return

    target_root.mkdir(parents=True, exist_ok=True)
    ensure_required_directories(target_root, mode)

    for rel_path, content in TEMPLATE_FILES.items():
        rendered = render_template(content, **render_kwargs)
        if rel_path == ".gitignore":
            safe_write(effective_gitignore_dest, rendered, args.force)
        else:
            safe_write(target_root / rel_path, rendered, args.force)

    prompt_content = render_template(INITIAL_PROMPT_TEMPLATES[mode], **render_kwargs)
    safe_write(target_root / ".collab/prompts/initial-prompt.md", prompt_content, args.force)

    for rel_path, content in PLATFORM_FILES.get(platform, {}).items():
        safe_write(target_root / rel_path, content, args.force)

    if license_id != "none":
        safe_write(target_root / "LICENSE", LICENSE_TEXTS[license_id], args.force)

    if args.init_git:
        print(f"\nRunning git init in {target_root} ...")
        result = subprocess.run(["git", "init"], cwd=target_root, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
        else:
            print(f"  git init failed: {result.stderr.strip()}")

    if mode == "existing":
        print(f"""
┌─ Brainstorms Directory ──────────────────────────────────────────────────────┐
│                                                                              │
│  .collab/brainstorms/ is ready.                                              │
│                                                                              │
│  If you have ideas already in your head or written down somewhere else,      │
│  now is a great time to move them in. Use the template to get started:       │
│                                                                              │
│    .collab/brainstorms/brainstorm-template.md                                │
│                                                                              │
│  One file per idea. No rules. Workshop them with your agent when ready.      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘""")

    indented_prompt = "\n".join("  " + line for line in prompt_content.strip().splitlines())
    print(f"""
Done. Scaffold installed at: {target_root}

Next steps:
  cd {target_root}
  Launch your agent (e.g., claude, codex, gemini)

First session — paste this to start:
  ─────────────────────────────────────────────────────────────
{indented_prompt}
  ─────────────────────────────────────────────────────────────

  Also saved to: .collab/prompts/initial-prompt.md

Tip: Start future sessions with OPEN SESSION to resume where you left off.
     Use SAVE SESSION mid-session to checkpoint without ending.
     End sessions with CLOSE SESSION to save your progress.
     Use SAVE CHAT to export the full session transcript to .collab/chat-logs/.
     Put project-adjacent materials (diagrams, specs, research) in .collab/supporting-artifacts/.
""")


if __name__ == "__main__":
    main()
