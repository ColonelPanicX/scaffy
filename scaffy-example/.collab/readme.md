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
- `north-star.md` — The project's end goal, who it serves, non-goals, and principles. Stable;
  changes only with the user's approval.
- `project.yaml` — Machine-readable project metadata (name, date, governance mode, agents).
- `session-summaries/` — Session summaries from all agents (template in `templates/`).
  Naming:
  - First summary of the day: `MM.DD.YYYY-agentname-summary.md`
  - Additional same-day summaries: `MM.DD.YYYY-##-agentname-summary.md`
    (use zero-padded sequence like `02`, `03`, etc.)
- `chat-logs/` — Full session transcripts exported via `SAVE CHAT`.
  Naming: `MM.DD.YYYY-claude-chat.md` (or `MM.DD.YYYY-##-claude-chat.md` for multiple per day).
- `brainstorms/` — Thinking space for pre-ticket concepts and proposals.
- `project-plans/` — Structured plans bridging brainstormed ideas and kanban execution.
- `agent-bridge/` — Shared-file channels between agents of different types (one subdirectory
  per bridge). Empty until a bridge is opened.
- `audit/` — Analysis reports, planning documents, and progress tracking artifacts.
- `inbox/` — Drop zone for files that might be useful: notes, exports, screenshots, docs.
  Sort through it with your agent; it may stay empty.
- `prompts/` — Reusable agent prompts and supporting inputs.
  - `initial-prompt.md` — First-session onboarding prompt (paste on first launch).
  - `agent-profile.md` — Fill-in questionnaire for generating agent instruction files.
  - `agent-md-prompt.md` — Prompt to generate CLAUDE.md / AGENTS.md from the profile.
- `skills/` — The scaffy skill for each agent CLI (`claude/`, `codex/`, `gemini/`). Copy the one you
  use to where your CLI loads skills. Add project-specific skills here too.
- `playbooks/` — How-to guides and the reasoning behind project conventions.
  - `coding-playbook.md` — General coding standards and best practices.
  - `agent-bridge-playbook.md` — How two agents of different types coordinate through a bridge.
  - `git-guidelines.md` — Git governance modes, branching strategy, label taxonomy, platform notes.
  - `git-governance-<mode>.md` — Step-by-step git procedure for this project's governance mode
    (not created for mode `none`).
- `templates/` — Starting points for new files: session summary, brainstorm, brainstorm session,
  project plan, issue, and pull request.

## Inbox Guidance

`inbox/` is where you drop anything that might be useful to the project before you know
where it belongs: notes, exports, screenshots, specs, links, research.

- Drop files in as they come. No naming rules, no sorting first.
- When you're ready, ask your agent to go through it with you. It reads each item and
  proposes what to do with it; where things end up is up to the two of you.
- The agent moves, rewrites or deletes nothing in `inbox/` without your approval.

## North Star Guidance

`north-star.md` is the one short document that says where the project is headed and why. Every
plan, brainstorm, and task should be checkable against it.

Workflow:
- Draft it early, with an agent interviewing you (the scaffy skill: `north star`).
- Keep it short: one sentence of direction, then problem, audience, success, non-goals,
  principles, and the signals that the project is drifting.
- It changes rarely and deliberately. Each change gets a dated line in its **Revision Log**.
- `scaffy --upgrade` never overwrites it.

## Brainstorm Directory Guidance

Use `brainstorms/` for concepts that aren't ready to be formal tickets yet — brain dumps, half-formed
proposals, things worth thinking through before committing to a sprint.

Workflow:
- Create one file per idea cluster, named descriptively (e.g., `better-onboarding.md`).
- Use `templates/brainstorm-template.md` as a starting point.
- Workshop ideas with an agent: ask for honest feedback, capture the discussion in the
  **Discussion Log** section of the file so context isn't lost when the session closes.
- When an idea is ready to become a ticket, note it at the bottom of the file and graduate it
  to your issue tracker. Leave the file in place as a record.
- Ideas that don't go anywhere can be left as `parked` — they might be useful later.

Brainstorm sessions:
- For a topic with many possible answers, run a facilitated session (the scaffy skill:
  `brainstorm session <topic>`). The agent frames the question with you, collects ideas
  without judging them, groups them, helps you pick a shortlist, and writes it all up.
- Each session produces `<topic>-session-MM.DD.YYYY.md` from `templates/brainstorm-session-template.md`.
  The file is written after every phase, so an interrupted session can be resumed.
- Shortlisted ideas can be spun off into their own single-idea brainstorm files.

## Project Plans Directory Guidance

Use `project-plans/` for work that has moved past the "is this a good idea?" stage but isn't
ready to be sprint tasks yet. Plans define the goal, phases, and tasks before anything hits the board.

Workflow:
- Create one file per initiative, named descriptively (e.g., `auth-refactor.md`).
- Use `templates/project-plan-template.md` as a starting point.
- Work with an agent to fill out phases and surface risks. Capture decisions in the file itself.
- When a phase is approved for execution, promote its tasks to `kanban-board.md` and note the
  date at the bottom of the plan file.
- Plans that are complete or cancelled can be marked `archived` — leave them in place as a record.

## Agent Bridge Guidance

An agent bridge lets two agents of **different types** (say Claude and Codex) work on one
problem through shared files instead of you relaying messages. Agents of the same type use
their CLI's own messaging instead.

- Opened only when you ask (the scaffy skill: `bridge open <name>`).
- Each bridge is a subdirectory of `agent-bridge/` with `README.md`, `transcript.md` and
  `status.md`. Closed bridges are kept as a record.
- Agents never commit, push, or change code because of a bridge message without your approval.
- Full procedure: `playbooks/agent-bridge-playbook.md`.

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
