#!/usr/bin/env python3
"""
Self-contained initializer for multi-agent project scaffold.

Usage:
    python scaffy.py [--name NAME] [--path PATH] [--force] [--dry-run]
                     [--governance MODE] [--platform PLATFORM] [--license LICENSE]
                     [--init-git] [--description TEXT]
    python scaffy.py --upgrade [--path PATH] [--force] [--dry-run]

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
import re
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")
GOVERNANCE_MODES = ("none", "lightweight", "standard", "strict")
PLATFORM_MODES = ("github", "gitlab", "azure-devops", "none")
LICENSE_CHOICES = ("mit", "apache-2.0", "gpl-3.0", "agpl-3.0", "bsd-2-clause", "bsd-3-clause", "mpl-2.0", "unlicense", "none")


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
- Start your first session by pasting the contents of `initial-prompt.md`.
- Use `OPEN SESSION` at the start of each working session to resume context quickly.
- Use `SAVE SESSION` mid-session to checkpoint progress without ending the session.
- Use `CLOSE SESSION` at the end of each session to save progress.
- Write session summaries to `session-summaries/` on close.
- Keep `kanban-board.md` current — it is the internal source of truth for task status.
- Use `ideas/` to workshop pre-ticket concepts. See `collab-contract.md` for agent behavior rules.

## Directory Structure

- `collab-contract.md` — Rules, conventions, and logging requirements.
- `kanban-board.md` — Task tracking (internal source of truth).
- `context.md` — Stable project facts: tech stack, key files, conventions, dependencies.
- `project.yaml` — Machine-readable project metadata (name, date, governance mode, agents).
- `initial-prompt.md` — Consolidated first-session prompt (paste on first launch).
- `session-summaries/` — Session summaries from all agents.
  Naming:
  - First summary of the day: `MM.DD.YYYY-agentname-summary.md`
  - Additional same-day summaries: `MM.DD.YYYY-##-agentname-summary.md`
    (use zero-padded sequence like `02`, `03`, etc.)
- `ideas/` — Idea incubator: persistent thinking space for pre-ticket concepts and proposals.
  - `idea-template.md` — Starter template for new idea files.
- `audit/` — Analysis reports, planning documents, and progress tracking artifacts.
- `supporting-artifacts/` — Adjacent project materials: diagrams, research notes, specs,
  reference docs, exported data, and anything else that supports the work but isn't
  source code. Keep the project root clean — if it belongs to the project but isn't
  code, it probably belongs here.
- `git-management/` — Optional VCS platform governance templates.
  Includes: `git-guidelines.md`, `issue-template.md`, `pull-request-template.md`

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

## Ideas Directory Guidance

Use `ideas/` for concepts that aren't ready to be formal tickets yet — brain dumps, half-formed
proposals, things worth thinking through before committing to a sprint.

Workflow:
- Create one file per idea cluster, named descriptively (e.g., `better-onboarding.md`).
- Use `idea-template.md` as a starting point.
- Workshop ideas with an agent: ask for honest feedback, capture the discussion in the
  **Discussion Log** section of the file so context isn't lost when the session closes.
- When an idea is ready to become a ticket, note it at the bottom of the file and graduate it
  to your issue tracker. Leave the file in place as a record.
- Ideas that don't go anywhere can be left as `parked` — they might be useful later.

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

## Ideas Directory

- **Location**: `.collab/ideas/`
- **Purpose**: Persistent thinking space for ideas that aren't ready to become tickets.
  Use this directory to capture, workshop, and evolve ideas collaboratively before they
  enter the formal task pipeline.
- **One file per idea cluster** — name files descriptively (lowercase, hyphen-separated).
- **Use the template** at `.collab/ideas/idea-template.md` as a starting point.
- **Nothing in `ideas/` is required to go anywhere.** Ideas can sit, evolve, or be parked
  indefinitely. The value is keeping them on paper so they aren't lost between sessions.

### Agent Behavior in `ideas/`

When the user points you at a file in `.collab/ideas/`:

1. Read the full file before responding.
2. Engage honestly — assess whether the idea has merit, identify gaps, ask clarifying questions.
3. Append a dated entry to the **Discussion Log** section summarizing the exchange and any
   key conclusions.
4. Update **Next Steps / Open Questions** to reflect the current state.
5. Update the `Status` field as the idea progresses:
   `drafting` → `workshopping` → `parked` or `graduated`
6. Do **not** create tickets, tasks, or kanban entries from an idea without explicit user approval.

When an idea graduates to a formal ticket:

- Add `Graduated → GitHub Issue #__ on MM.DD.YYYY` at the bottom of the file.
- Leave the file in `ideas/` as a record — do not delete it.
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

    ".collab/ideas/idea-template.md": """\
# Idea Title

_Started: {date}_
_Status: drafting_

<!-- Status values: drafting | workshopping | parked | graduated -->

## The Idea

<!-- Brain dump here. No rules. Write freely. -->

## Discussion Log

<!-- Agent/human back-and-forth: summaries, assessments, key decisions.    -->
<!-- Date-stamp each entry: _MM.DD.YYYY_ — so the evolution is traceable. -->

## Next Steps / Open Questions

<!-- What needs to happen before this becomes a ticket — or gets parked. -->

---
<!-- When graduated: Graduated → GitHub Issue #__ on MM.DD.YYYY -->
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
   `OPEN SESSION`, `SAVE SESSION`, and `CLOSE SESSION`.
3. The kanban board is empty — this is a new project. Wait for my direction before
   drafting plans or tasks.
""",
    "existing": """\
This project has a `.collab/` collaboration workspace. Before doing anything:

1. Read everything in `.collab/`: start with `collab-contract.md`, then `kanban-board.md`,
   `context.md`, and any summaries in `session-summaries/`.
2. Commit to memory the session trigger phrases and their protocols from `collab-contract.md`:
   `OPEN SESSION`, `SAVE SESSION`, and `CLOSE SESSION`.
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
    print("  3) Upgrade existing scaffold")
    choices = {"1": "new", "2": "existing", "3": "upgrade"}
    choice = prompt_choice("Select [1-3]: ", set(choices))
    return choices[choice]


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
                'Invalid name. Folder names cannot contain \\ / : * ? " < > | '
                "or be Windows reserved names (CON, PRN, NUL, etc.)."
            )
            continue
        return name


def prompt_for_governance() -> str:
    print("\nGovernance mode:")
    print("  1) None        — no governance rules or process structure")
    print("  2) Lightweight — minimal process, fast iteration (prototypes, solo work)")
    print("  3) Standard    — balanced workflow, recommended for most projects")
    print("  4) Strict      — full process gates, for compliance/regulated work")
    choices = {"1": "none", "2": "lightweight", "3": "standard", "4": "strict"}
    while True:
        try:
            value = input("Select [1-4, Enter for standard]: ").strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if not value:
            return "standard"
        if value in choices:
            return choices[value]
        print("Invalid. Enter 1, 2, 3, or 4.")


def prompt_for_platform() -> str:
    print("\nGit platform:")
    print("  1) GitHub")
    print("  2) GitLab")
    print("  3) Azure DevOps")
    print("  4) None / other")
    choices = {"1": "github", "2": "gitlab", "3": "azure-devops", "4": "none"}
    while True:
        try:
            value = input("Select [1-4, Enter to skip]: ").strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if not value:
            return "none"
        if value in choices:
            return choices[value]
        print("Invalid. Enter 1, 2, 3, or 4.")


def prompt_for_license() -> str:
    print("\nLicense:")
    print("  1) MIT             — permissive, short, very common")
    print("  2) Apache-2.0      — permissive, patent grant included")
    print("  3) GPL-3.0         — copyleft, strong")
    print("  4) AGPL-3.0        — copyleft, network use triggers share-alike")
    print("  5) BSD-2-Clause    — permissive, minimal")
    print("  6) BSD-3-Clause    — permissive, no-endorsement clause")
    print("  7) MPL-2.0         — weak copyleft, file-level")
    print("  8) Unlicense       — public domain dedication")
    print("  9) None            — skip LICENSE file")
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
        try:
            value = input("Select [1-9, Enter to skip]: ").strip()
        except EOFError:
            raise SystemExit("No input provided; exiting.")
        if not value:
            return "none"
        if value in choices:
            return choices[value]
        print("Invalid. Enter 1–9 or press Enter to skip.")


def prompt_for_description() -> str:
    print("\nProject description (optional):")
    print("  A short sentence injected into context.md.")
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
    platform: str,
    license_id: str,
    date: str,
) -> str:
    description_rendered = description if description else "<!-- Add a brief description of this project -->"
    replacements = {
        "{project_name}": project_name,
        "{description}": description_rendered,
        "{governance_mode}": governance_mode,
        "{platform}": platform,
        "{license}": license_id,
        "{date}": date,
    }
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    return content


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
        target_root / ".collab" / "ideas",
        target_root / ".collab" / "audit",
        target_root / ".collab" / "git-management",
        target_root / ".collab" / "session-summaries",
        target_root / ".collab" / "supporting-artifacts",
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

    timestamp = meta.get("created", now_tz().strftime("%m.%d.%Y"))
    description = ""

    render_kwargs = dict(
        project_name=project_name,
        description=description,
        governance_mode=governance_mode,
        platform=platform,
        license_id=license_id,
        date=timestamp,
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
    files_to_check[collab_dir / "initial-prompt.md"] = prompt_content

    # Platform files
    for rel_path, content in PLATFORM_FILES.get(platform, {}).items():
        files_to_check[target_root / rel_path] = content

    # License
    if license_id != "none":
        files_to_check[target_root / "LICENSE"] = LICENSE_TEXTS[license_id]

    # Directories
    required_dirs = [
        collab_dir / "ideas",
        collab_dir / "audit",
        collab_dir / "git-management",
        collab_dir / "session-summaries",
        collab_dir / "supporting-artifacts",
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

    if not added_dirs and not added_files and not updated_files:
        print("Everything is up to date. Nothing to do.")
    elif dry_run:
        print("\nDry run complete. No files written.")
    else:
        total = len(added_dirs) + len(added_files) + len(updated_files)
        print(f"\nUpgrade complete. {total} item(s) added/updated.")


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
    parser.add_argument("--init-git", action="store_true", help="Run git init in the project root after scaffolding.")
    parser.add_argument("--description", metavar="TEXT", default="", help="Short project description.")
    args = parser.parse_args()

    # --- Upgrade mode ---
    if args.upgrade:
        target = Path(args.path).expanduser().resolve() if args.path else Path.cwd()
        upgrade_scaffold(target, force=args.force, dry_run=args.dry_run)
        return

    if args.name and not valid_project_name(args.name):
        parser.error(
            'Invalid --name. Folder names cannot contain \\ / : * ? " < > | '
            "or be Windows reserved names (CON, PRN, NUL, etc.)."
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
    else:
        print("Project Initialize")
        print("------------------")
        print("Sets up a .collab/ collaboration scaffold for multi-agent projects.")

        mode = "new" if args.name else prompt_for_mode()
        selected_root = Path(args.path).expanduser().resolve() if args.path else prompt_for_target_root()

        if mode == "upgrade":
            upgrade_scaffold(selected_root, force=args.force, dry_run=args.dry_run)
            return

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
        platform = args.platform or prompt_for_platform()
        license_id = args.license or ("none" if platform == "none" else prompt_for_license())
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
        platform=platform,
        license_id=license_id,
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
    print(f"Platform:   {platform}")
    print(f"License:    {license_id}")
    print(f"Date:       {timestamp} (America/New_York)")
    if target_root.exists() and not args.force:
        print("Notice: Target exists. Existing files will be skipped unless --force is used.")

    if args.dry_run:
        print("\nPlanned actions:")
        for rel_path in TEMPLATE_FILES:
            if rel_path == ".gitignore":
                print(f"  write {effective_gitignore_dest}")
            else:
                print(f"  write {target_root / rel_path}")
        print(f"  write {target_root / '.collab/initial-prompt.md'}")
        for rel_path in PLATFORM_FILES.get(platform, {}):
            print(f"  write {target_root / rel_path}")
        if license_id != "none":
            print(f"  write {target_root / 'LICENSE'}")
        if args.init_git:
            print(f"  git init {target_root}")
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
    ensure_required_directories(target_root, mode)

    for rel_path, content in TEMPLATE_FILES.items():
        rendered = render_template(content, **render_kwargs)
        if rel_path == ".gitignore":
            safe_write(effective_gitignore_dest, rendered, args.force)
        else:
            safe_write(target_root / rel_path, rendered, args.force)

    prompt_content = render_template(INITIAL_PROMPT_TEMPLATES[mode], **render_kwargs)
    safe_write(target_root / ".collab/initial-prompt.md", prompt_content, args.force)

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
┌─ Ideas Directory ────────────────────────────────────────────────────────────┐
│                                                                              │
│  .collab/ideas/ is ready.                                                    │
│                                                                              │
│  If you have ideas already in your head or written down somewhere else,      │
│  now is a great time to move them in. Use the template to get started:       │
│                                                                              │
│    .collab/ideas/idea-template.md                                            │
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

  Also saved to: .collab/initial-prompt.md

Tip: Start future sessions with OPEN SESSION to resume where you left off.
     Use SAVE SESSION mid-session to checkpoint without ending.
     End sessions with CLOSE SESSION to save your progress.
     Put project-adjacent materials (diagrams, specs, research) in .collab/supporting-artifacts/.
""")


if __name__ == "__main__":
    main()
