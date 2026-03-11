#!/usr/bin/env python3
"""
Self-contained initializer for multi-agent project scaffold.

Usage:
    python scaffy.py [--name NAME] [--path PATH] [--force] [--dry-run]
                     [--governance MODE] [--agent AGENT [...]] [--init-git]
                     [--description TEXT]

If --name and --path are both provided, runs without interactive prompts.
Otherwise uses interactive menus for mode/target/governance selection.

Options:
  --name NAME          Project name (lowercase, hyphen-separated).
  --path PATH          Target directory where scaffold files will be installed.
  --force              Overwrite existing files.
  --dry-run            Show planned actions and exit without writing anything.
  --governance MODE    Governance mode: lightweight, standard, or strict. Default: standard.
  --agent AGENT        Agent(s) to generate root instruction files for: claude, codex,
                       gemini, or all. Can be specified multiple times. Default: all.
  --init-git           Run git init in the project root after scaffolding.
  --description TEXT   Short project description injected into context.md and agent files.

Conventions:
- Timezone: America/New_York. Dates use MM.DD.YYYY (no times).
- Names: lowercase, hyphen-separated.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")
GOVERNANCE_MODES = ("lightweight", "standard", "strict")
AGENT_NAMES = ("claude", "codex", "gemini")


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
- Start sessions by using the relevant sequence from `initial-prompts/`:
  - `initial-prompts/new-project/` for brand-new repos
  - `initial-prompts/existing-project/` for retrofitted repos
  - `initial-prompts/agents/` for agent-specific supplements
- Use `OPEN SESSION` at the start of each working session to resume context quickly.
- Use `CLOSE SESSION` at the end of each session to save progress.
- Write session summaries to `session-summaries/` on close.
- Keep `kanban-board.md` current — it is the internal source of truth for task status.

## Directory Structure

- `collab-contract.md` — Rules, conventions, and logging requirements.
- `kanban-board.md` — Task tracking (internal source of truth).
- `context.md` — Stable project facts: tech stack, key files, conventions, dependencies.
- `project.yaml` — Machine-readable project metadata (name, date, governance mode, agents).
- `initial-prompts/` — Onboarding prompt sequences for first and subsequent sessions.
  - `new-project/00-onboard.md` — First-session cold start for new projects.
  - `new-project/01-context-build.md` — Memory/context initialization after onboarding.
  - `existing-project/00-onboard.md` — First-session cold start for existing projects.
  - `existing-project/01-context-build.md` — Memory/context initialization after onboarding.
  - `agents/claude.md` — Claude Code-specific supplement.
  - `agents/codex.md` — Codex-specific supplement.
  - `agents/gemini.md` — Gemini-specific supplement.
- `session-summaries/` — Session summaries from all agents.
  Naming:
  - First summary of the day: `MM.DD.YYYY-agentname-summary.md`
  - Additional same-day summaries: `MM.DD.YYYY-##-agentname-summary.md`
    (use zero-padded sequence like `02`, `03`, etc.)
- `audit/` — Analysis reports, planning documents, and progress tracking artifacts.
- `git-management/` — Optional VCS platform governance templates.
  Includes: `git-guidelines.md`, `issue-template.md`, `pull-request-template.md`

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
""",

    ".collab/kanban-board.md": """\
# Kanban Board

<!--
Format:
- [ ] TASK-###: Description (@owner) [p?] [area:?] [type:?]
Examples:
- [ ] TASK-001: Draft project plan (@user) [p1] [area:planning] [type:doc]
- [ ] TASK-002: Implement exporter refactor (@claude) [p2] [area:exporters] [type:feature]
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
agents:
{agents_yaml}
""",

    ".collab/initial-prompts/new-project/00-onboard.md": """\
# First Session — New Project

Paste the block below when starting your first agent session in this project.

---

You are working in a newly initialized project with a structured `.collab/` collaboration
directory. Before doing anything:

1. Read `.collab/collab-contract.md` for rules, naming conventions, and logging requirements.
2. Read `.collab/kanban-board.md` for current task status.
3. Read `.collab/context.md` for stable project facts (fill in what you can from context).
4. Check `.collab/session-summaries/` for any prior session summaries.
5. The kanban board is empty — this is a newly initialized project. Wait for the user to
   describe goals before drafting plans or tasks.

If your agent type has a supplement in `.collab/initial-prompts/agents/`, read it now.

---

## Session Protocols

### OPEN SESSION

When the user types exactly:

    OPEN SESSION

Immediately execute the Session Open Protocol:

1. Read the most recent 1-2 session summaries in `.collab/session-summaries/`.
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md`.
4. Deliver a concise session resume:
   - What was accomplished last session
   - What is currently In Progress or Blocked
   - What is up next
   - Any open questions or flags from the last session

Do not re-read `collab-contract.md`. Focus on current state, not process rules.

### CLOSE SESSION

When the user types exactly:

    CLOSE SESSION

Immediately execute the Session Close Protocol:

1. Write a session summary to `.collab/session-summaries/`:
   - First of the day: `MM.DD.YYYY-agentname-summary.md`
   - Additional same-day: `MM.DD.YYYY-##-agentname-summary.md` (zero-padded: `02`, `03`, …)
   - Use the template at `.collab/session-summaries/session-summary-template.md`
2. Update `.collab/kanban-board.md`:
   - Move completed tasks to **Done**
   - Update in-progress task statuses
   - Add newly discovered tasks to **Inbox** or **Backlog**
3. Confirm completion to the user.
""",

    ".collab/initial-prompts/new-project/01-context-build.md": """\
# Context Build — Paste After First Onboarding

Use this prompt immediately after `00-onboard.md` to seed memory and context
before the first real work session begins.

---

Now that you have oriented to the project structure:

1. Read `.collab/context.md`. Note any fields that are empty or incomplete.

2. Initialize your project memory with the following stable facts (use whatever
   persistent memory mechanism your agent supports):
   - Project name and one-sentence description
   - Tech stack: languages, frameworks, key dependencies
   - Key file paths: entry points, config files, test directories
   - Naming and style conventions
   - Hard constraints or guardrails (e.g., "never commit credentials")

3. Report back to the user:
   - What you saved to memory
   - Which fields in `context.md` are empty and should be filled in before work begins

Do not start any work tasks until this step is complete.
""",

    ".collab/initial-prompts/existing-project/00-onboard.md": """\
# First Session — Existing Project

Paste the block below when starting your first agent session in an existing project
that has been retrofitted with a `.collab/` collaboration directory.

---

You are working in an **existing project**. This project may already contain code,
configuration, history, and decisions made before this structure was in place.

Before doing anything:

1. Read `.collab/collab-contract.md` for rules, naming conventions, and logging requirements.
2. Read `.collab/kanban-board.md` for current task status.
3. Read `.collab/context.md` for stable project facts (if it exists and has content).
4. Check `.collab/session-summaries/` for any prior session summaries.
5. Perform a brief, non-destructive reconnaissance of the repository:
   - Identify the apparent purpose of the project.
   - Identify primary languages, frameworks, and entry points.
   - Identify build/test commands if discoverable.
   - Note any existing documentation (README, docs/, etc.).
6. Do **not** restructure, refactor, rename, or reorganize anything unless explicitly instructed.
7. If the kanban board is empty, treat this as a retrofit scenario:
   - Add initial tasks to **Inbox** or **Backlog**: repo mapping, architecture understanding,
     build/test validation.
   - Wait for user approval before making structural changes.

Your first responsibility is to **understand and document the current state**, not change it.

If your agent type has a supplement in `.collab/initial-prompts/agents/`, read it now.

---

## Session Protocols

### OPEN SESSION

When the user types exactly:

    OPEN SESSION

Immediately execute the Session Open Protocol:

1. Read the most recent 1-2 session summaries in `.collab/session-summaries/`.
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md`.
4. Deliver a concise session resume:
   - What was accomplished last session
   - What is currently In Progress or Blocked
   - What is up next
   - Any open questions or flags from the last session

Do not re-read `collab-contract.md`. Focus on current state, not process rules.

### CLOSE SESSION

When the user types exactly:

    CLOSE SESSION

Immediately execute the Session Close Protocol:

1. Write a session summary to `.collab/session-summaries/`:
   - First of the day: `MM.DD.YYYY-agentname-summary.md`
   - Additional same-day: `MM.DD.YYYY-##-agentname-summary.md` (zero-padded: `02`, `03`, …)
   - Use the template at `.collab/session-summaries/session-summary-template.md`
2. Update `.collab/kanban-board.md`:
   - Move completed tasks to **Done**
   - Update in-progress task statuses
   - Add newly discovered tasks to **Inbox** or **Backlog**
3. Confirm completion to the user.
""",

    ".collab/initial-prompts/existing-project/01-context-build.md": """\
# Context Build — Paste After First Onboarding

Use this prompt immediately after `00-onboard.md` to seed memory and document
the current project state before any work begins.

---

Now that you have completed your initial reconnaissance:

1. Read `.collab/context.md`. Note any fields that are empty or out of date.

2. Using what you discovered during reconnaissance, fill in or verify:
   - What this project is and what it does
   - Tech stack: languages, frameworks, key dependencies
   - Key file paths: entry points, config files, test directories
   - Naming and style conventions already in use
   - Any constraints or guardrails apparent from the codebase

3. Initialize your project memory with these stable facts (use whatever persistent
   memory mechanism your agent supports).

4. Report back to the user:
   - What you saved to memory
   - What you updated or could not determine in `context.md`
   - Any immediate risks or concerns observed during reconnaissance

Do not start any work tasks until this step is complete.
""",

    ".collab/initial-prompts/agents/claude.md": """\
# Claude Code — Agent Supplement

Read this in addition to the standard onboarding prompt for your session type
(`initial-prompts/new-project/00-onboard.md` or `existing-project/00-onboard.md`).

---

## Claude Code-Specific Setup

1. **`CLAUDE.md`** — If a `CLAUDE.md` exists at the project root, it is your primary
   project instruction file and takes precedence over generic guidance. Read it before
   or alongside `collab-contract.md`.

2. **Project memory** — Claude Code supports persistent memory. On your first session,
   use your memory tools to store stable project facts:
   - Project name and one-sentence purpose
   - Tech stack and key dependencies
   - Key file paths and entry points
   - Naming conventions and hard guardrails
   On subsequent sessions, `OPEN SESSION` is your fast-path to current state — memory
   gives you the stable foundation so you do not need to re-read everything from scratch.

3. **MCP servers** — If `.claude/` settings reference MCP servers, confirm they are
   available before starting work that depends on them. If a server is unavailable,
   report it to the user before proceeding.

4. **Hooks** — Claude Code hooks may run automatically on tool calls. If a hook blocks
   an action, investigate the cause before retrying. Do not use `--no-verify` or other
   bypass flags without explicit user approval.
""",

    ".collab/initial-prompts/agents/codex.md": """\
# Codex — Agent Supplement

Read this in addition to the standard onboarding prompt for your session type
(`initial-prompts/new-project/00-onboard.md` or `existing-project/00-onboard.md`).

---

## Codex-Specific Setup

1. **`AGENTS.md`** — If an `AGENTS.md` exists at the project root, it is your primary
   project instruction file. Read it before or alongside `collab-contract.md`.

2. **Memory** — Codex does not have a built-in persistent memory system. Rely on
   session summaries in `.collab/session-summaries/` and `.collab/context.md` to
   reconstruct project context at the start of each session. Keep both up to date.

3. **Handoff board** — If a `.collab/handoff-board.yaml` exists, check it for
   cross-agent task assignments before acting. Do not modify files owned by other agents
   without explicit instruction.

4. **Session hygiene** — Because you have no memory persistence, your session summaries
   are especially important. Write detailed `## What Happened` and `## Next Steps`
   sections so the next agent (or your own next session) can resume without ambiguity.
""",

    ".collab/initial-prompts/agents/gemini.md": """\
# Gemini — Agent Supplement

Read this in addition to the standard onboarding prompt for your session type
(`initial-prompts/new-project/00-onboard.md` or `existing-project/00-onboard.md`).

---

## Gemini-Specific Setup

1. **`GEMINI.md`** — If a `GEMINI.md` exists at the project root, it is your primary
   project instruction file. Read it before or alongside `collab-contract.md`.

2. **Memory** — Rely on session summaries in `.collab/session-summaries/` and
   `.collab/context.md` to reconstruct project context at the start of each session.

3. **Tool use** — Follow the permissions and guardrails in `collab-contract.md` for all
   function/tool calls. Prefer safe, local tools (e.g., file reads, grep) over network
   calls unless explicitly required.

4. **Session hygiene** — Write thorough session summaries at close so subsequent agents
   or sessions can resume with full context.
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

    ".collab/git-management/git-guidelines.md": """\
---

# Git Platform Governance & AI Agent Operating Guidelines

**Version: v1.2.0 (Unified Template)**

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
- Use `issue-template.md` from this directory as your baseline.
- Add a PR/MR template with summary, test evidence, and linked work item.

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

    ".collab/git-management/issue-template.md": """\
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

    ".collab/git-management/pull-request-template.md": """\
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
}


# ---------------------------------------------------------------------------
# Agent root files — written to project root, conditioned on --agent flag
# ---------------------------------------------------------------------------

AGENT_ROOT_FILES: dict[str, tuple[str, str]] = {
    "claude": (
        "CLAUDE.md",
        """\
# {project_name}

## Project Overview

{description}

## Tech Stack

<!-- Languages, frameworks, key dependencies -->

## Key Commands

<!-- Build, test, lint, run commands -->

## Conventions

<!-- Naming conventions, code style, file organization -->

## Collaboration

This project uses a `.collab/` workspace for multi-agent coordination.
Before acting in any session:

- Read `.collab/collab-contract.md` — rules and logging requirements
- Read `.collab/kanban-board.md` — current task state
- Read `.collab/context.md` — stable project facts

Use `OPEN SESSION` at the start of each working session to resume context.
Use `CLOSE SESSION` at the end to save progress.
""",
    ),
    "codex": (
        "AGENTS.md",
        """\
# {project_name} — Agent Guidelines

## Project Overview

{description}

## Tech Stack

<!-- Languages, frameworks, key dependencies -->

## Key Commands

<!-- Build, test, lint, run commands -->

## Conventions

<!-- Naming conventions, code style, file organization -->

## Collaboration

This project uses a `.collab/` workspace for multi-agent coordination.
Before acting in any session:

- Read `.collab/collab-contract.md` — rules and logging requirements
- Read `.collab/kanban-board.md` — current task state
- Read `.collab/context.md` — stable project facts

Use `OPEN SESSION` at the start of each working session to resume context.
Use `CLOSE SESSION` at the end to save progress.
""",
    ),
    "gemini": (
        "GEMINI.md",
        """\
# {project_name} — Gemini Instructions

## Project Overview

{description}

## Tech Stack

<!-- Languages, frameworks, key dependencies -->

## Key Commands

<!-- Build, test, lint, run commands -->

## Conventions

<!-- Naming conventions, code style, file organization -->

## Collaboration

This project uses a `.collab/` workspace for multi-agent coordination.
Before acting in any session:

- Read `.collab/collab-contract.md` — rules and logging requirements
- Read `.collab/kanban-board.md` — current task state
- Read `.collab/context.md` — stable project facts

Use `OPEN SESSION` at the start of each working session to resume context.
Use `CLOSE SESSION` at the end to save progress.
""",
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_project_name(name: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name))


def suggest_project_name_from_target(target_root: Path) -> str:
    candidate = target_root.name.strip().lower()
    candidate = re.sub(r"[^a-z0-9-]+", "-", candidate)
    candidate = re.sub(r"-{2,}", "-", candidate).strip("-")
    if valid_project_name(candidate):
        return candidate
    return "my-project"


def prompt_choice(prompt: str, valid: set[str]) -> str:
    while True:
        try:
            value = input(prompt).strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if value in valid:
            return value
        print(f"Invalid selection. Please enter one of: {', '.join(sorted(valid))}.")


def prompt_for_mode() -> str:
    print("\nWhat are you initializing?")
    print("  1) New project")
    print("  2) Existing project")
    choice = prompt_choice("Select [1-2]: ", {"1", "2"})
    return "new" if choice == "1" else "existing"


def prompt_for_target_root() -> Path:
    cwd = Path.cwd().resolve()
    print("\nWhere should it be installed?")
    print(f"  1) Current directory ({cwd})")
    print("  2) Another directory")
    choice = prompt_choice("Select [1-2]: ", {"1", "2"})

    if choice == "1":
        return cwd

    print("\nEnter target directory path:")
    print("  (supports ~, relative, or absolute path)")
    while True:
        try:
            raw = input("Path: ").strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if not raw:
            print("Path cannot be empty.")
            continue
        target = Path(raw).expanduser().resolve()
        if not target.exists():
            print(f"Target directory does not exist: {target}")
            print("Choose another path or create the directory first.")
            continue
        if not target.is_dir():
            print(f"Target path is not a directory: {target}")
            continue
        print(f"  Resolved: {target}")
        return target


def prompt_for_new_project_name(default_name: str) -> str:
    while True:
        try:
            name = input(f"Project name [{default_name}]: ").strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if not name:
            return default_name
        if not valid_project_name(name):
            print(
                "Invalid name. Use lowercase letters, numbers, and hyphens only; "
                "must start/end with alphanumeric. Example: my-project-1"
            )
            continue
        return name


def prompt_for_governance() -> str:
    print("\nGovernance mode:")
    print("  1) Lightweight — minimal process, fast iteration (prototypes, solo work)")
    print("  2) Standard    — balanced workflow, recommended for most projects")
    print("  3) Strict      — full process gates, for compliance/regulated work")
    choices = {"1": "lightweight", "2": "standard", "3": "strict"}
    while True:
        try:
            value = input("Select [1-3, Enter for standard]: ").strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if not value:
            return "standard"
        if value in choices:
            return choices[value]
        print("Invalid. Enter 1, 2, or 3.")


def prompt_for_description() -> str:
    print("\nProject description (optional):")
    print("  A short sentence injected into context.md and agent instruction files.")
    try:
        value = input("Description [Enter to skip]: ").strip()
    except EOFError:
        raise SystemExit("No input provided; exiting.")
    return value


def render_template(
    content: str,
    *,
    project_name: str,
    description: str,
    governance_mode: str,
    agents: list[str],
    date: str,
) -> str:
    description_rendered = description if description else "<!-- Add a brief description of this project -->"
    agents_yaml = "\n".join(f"  - {a}" for a in agents)
    replacements = {
        "{project_name}": project_name,
        "{description}": description_rendered,
        "{governance_mode}": governance_mode,
        "{agents_yaml}": agents_yaml,
        "{date}": date,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


def safe_write(dest: Path, content: str, force: bool) -> None:
    if dest.exists() and not force:
        print(f"  skip (exists): {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    if dest.suffix in {".sh", ".py"}:
        try:
            dest.chmod(0o755)
        except OSError:
            pass
    print(f"  write: {dest}")


def ensure_required_directories(target_root: Path) -> None:
    required_dirs = [
        target_root / ".collab" / "audit",
        target_root / ".collab" / "initial-prompts" / "new-project",
        target_root / ".collab" / "initial-prompts" / "existing-project",
        target_root / ".collab" / "initial-prompts" / "agents",
        target_root / ".collab" / "git-management",
        target_root / ".collab" / "session-summaries",
    ]
    for path in required_dirs:
        path.mkdir(parents=True, exist_ok=True)
        print(f"  mkdir: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize a multi-agent project scaffold.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--name", metavar="NAME", help="Project name (lowercase, hyphen-separated).")
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
        "--agent",
        metavar="AGENT",
        choices=(*AGENT_NAMES, "all"),
        action="append",
        dest="agents",
        default=None,
        help="Agent(s) to generate root instruction files for. Can repeat. Default: all.",
    )
    parser.add_argument("--init-git", action="store_true", help="Run git init in the project root after scaffolding.")
    parser.add_argument("--description", metavar="TEXT", default="", help="Short project description.")
    args = parser.parse_args()

    if args.name and not valid_project_name(args.name):
        parser.error(
            "Invalid --name. Use lowercase letters, numbers, and hyphens only; "
            "must start/end with alphanumeric. Example: my-project-1"
        )

    # Resolve selected agents
    raw_agents = args.agents or ["all"]
    if "all" in raw_agents:
        selected_agents = list(AGENT_NAMES)
    else:
        selected_agents = list(dict.fromkeys(raw_agents))  # deduplicate, preserve order

    fully_scripted = bool(args.name and args.path)

    if fully_scripted:
        mode = "new"
        project_name = args.name
        target_root = (Path(args.path).expanduser().resolve() / project_name).resolve()
        governance_mode = args.governance or "standard"
        description = args.description
    else:
        print("Project Initialize")
        print("------------------")
        print("Sets up a .collab/ collaboration scaffold for multi-agent projects.")

        mode = "new" if args.name else prompt_for_mode()
        selected_root = Path(args.path).expanduser().resolve() if args.path else prompt_for_target_root()

        if mode == "new":
            default_name = suggest_project_name_from_target(selected_root)
            print("\nNew project details")
            print("-------------------")
            project_name = args.name or prompt_for_new_project_name(default_name)
            target_root = (selected_root / project_name).resolve()
        else:
            target_root = selected_root
            project_name = suggest_project_name_from_target(target_root)

        governance_mode = args.governance or prompt_for_governance()
        description = args.description or prompt_for_description()

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
        agents=selected_agents,
        date=timestamp,
    )

    # Summary
    print("\nSummary")
    print("-------")
    print(f"Mode:       {'New project' if mode == 'new' else 'Existing project'}")
    print(f"Target:     {target_root}")
    if mode == "new":
        print(f"Name:       {project_name}")
    print(f"Governance: {governance_mode}")
    print(f"Agents:     {', '.join(selected_agents)}")
    print(f"Date:       {timestamp} (America/New_York)")
    if target_root.exists() and not args.force:
        print("Notice: Target exists. Existing files will be skipped unless --force is used.")

    print("\nPlanned actions:")
    for rel_path in TEMPLATE_FILES:
        if rel_path == ".gitignore":
            print(f"  write {effective_gitignore_dest}")
        else:
            print(f"  write {target_root / rel_path}")
    for agent in selected_agents:
        filename, _ = AGENT_ROOT_FILES[agent]
        print(f"  write {target_root / filename}")
    if args.init_git:
        print(f"  git init {target_root}")

    if args.dry_run:
        print("\nDry run complete. No files written.")
        return

    if not fully_scripted:
        try:
            confirm = input("\nProceed? [y/N]: ").strip().lower()
        except EOFError:
            confirm = "n"
        if confirm != "y":
            print("Aborted.")
            return

    target_root.mkdir(parents=True, exist_ok=True)
    ensure_required_directories(target_root)

    for rel_path, content in TEMPLATE_FILES.items():
        rendered = render_template(content, **render_kwargs)
        if rel_path == ".gitignore":
            safe_write(effective_gitignore_dest, rendered, args.force)
        else:
            safe_write(target_root / rel_path, rendered, args.force)

    for agent in selected_agents:
        filename, content = AGENT_ROOT_FILES[agent]
        rendered = render_template(content, **render_kwargs)
        safe_write(target_root / filename, rendered, args.force)

    if args.init_git:
        print(f"\nRunning git init in {target_root} ...")
        result = subprocess.run(["git", "init"], cwd=target_root, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
        else:
            print(f"  git init failed: {result.stderr.strip()}")

    prompt_file = "new-project" if mode == "new" else "existing-project"
    print(f"""
Done. Scaffold installed at: {target_root}

Next steps:
  cd {target_root}
  Launch your agent (e.g., claude, codex, gemini)

First session — paste this to start:
  ─────────────────────────────────────────────────────────────
  Read .collab/collab-contract.md, kanban-board.md, and context.md.
  {'This is a new project — wait for me to describe goals.' if mode == 'new' else 'This is an existing project — perform reconnaissance before acting.'}
  See .collab/initial-prompts/{prompt_file}/ for the full onboarding sequence.
  ─────────────────────────────────────────────────────────────

Then paste .collab/initial-prompts/{prompt_file}/01-context-build.md to seed memory.

Tip: Start future sessions with OPEN SESSION to resume where you left off.
     End sessions with CLOSE SESSION to save your progress.
""")


if __name__ == "__main__":
    main()
