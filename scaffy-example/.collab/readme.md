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
