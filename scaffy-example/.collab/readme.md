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
- `git-management/` — Optional VCS platform governance templates.
  Includes: `git-guidelines.md`, `issue-template.md`, `pull-request-template.md`

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
