---
name: scaffy
description: Use this skill when the user wants to bootstrap a new project workspace, initialize a .collab/ directory, scaffold a multi-agent collaboration setup, set up a new project with scaffy, or run session protocols (initialize/open/save/close/save-chat/brainstorm/project-plan) for an existing scaffy project.
---

# scaffy — .collab/ Workspace Bootstrapper

Route based on the user's request:

- `open session` → **Session Open Protocol**
- `save session` → **Session Save Protocol**
- `close session` → **Session Close Protocol**
- `initialize` → **Initialize Protocol**
- `save chat` → **Chat Save Protocol**
- `brainstorm` or `brainstorm <title>` → **Brainstorm Protocol**
- `project plan` or `project plan <title>` → **Project Plan Protocol**
- anything else (project name, path, flags, or empty) → **Scaffold a new project**

---

## Initialize Protocol

Execute immediately — do not wait for additional instructions.

This is the first-session onboarding for a project with a `.collab/` workspace. Use this instead of `open session` when the agent has never worked in this project before.

1. **Read the workspace** — read the full `.collab/` directory:
   - `collab-contract.md` — rules, session protocols, guardrails
   - `kanban-board.md` — current task state
   - `context.md` — project facts (if it exists)
   - Any summaries in `session-summaries/`
2. **Commit session protocols to memory** — note the trigger phrases and their behaviors from `collab-contract.md`: `OPEN SESSION`, `SAVE SESSION`, `CLOSE SESSION`.
3. **Repo recon** — do a brief, non-destructive survey of the repository:
   - Project purpose and what problem it solves
   - Primary languages and frameworks
   - Entry points (main scripts, CLI commands, server start)
   - Build, test, and lint commands
   - Existing documentation
   - Do **not** restructure, rename, or modify anything.
4. **Seed the kanban** — if the kanban board is empty, add initial recon tasks to **Inbox** (e.g. populate context.md, map key files, validate build commands). Wait for user approval before acting on them.
5. **Report findings** — deliver a concise summary of what you found: project purpose, stack, entry points, commands, and any gaps or questions. Your first responsibility is to understand the current state, not change it.

---

## Session Open Protocol

Execute immediately — do not wait for additional instructions:

1. Find and read the most recent 1–2 session summaries in `.collab/session-summaries/` (sort by filename date, newest first; skip `session-summary-template.md`).
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md` if it exists.
4. Deliver a concise session resume covering:
   - What was accomplished last session
   - What is currently In Progress or Blocked on the board
   - What is up next
   - Any open questions or flags left from the last session

Do not re-read `collab-contract.md` — focus on current state, not process rules.

---

## Session Save Protocol

Execute immediately — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` (always a new file — never overwrite):
   - First summary that day: `MM.DD.YYYY-codex-summary.md`
   - Additional same-day saves: `MM.DD.YYYY-02-codex-summary.md`, `MM.DD.YYYY-03-codex-summary.md`, etc.
   - Use the template at `.collab/session-summaries/session-summary-template.md`.
2. Update `.collab/kanban-board.md` to reflect current task state.
3. Confirm the checkpoint was saved. Do not end the session — continue working.

---

## Session Close Protocol

Execute immediately — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` using the same naming convention as Save (always a new file).
2. Update `.collab/kanban-board.md` to reflect current task state.
3. Confirm completion to the user.

---

## Chat Save Protocol

Execute immediately — do not wait for additional instructions:

1. Run from the project root:
   - If scaffy is on PATH: `scaffy --save-chat --cli codex`
2. The tool saves the transcript to `.collab/chat-logs/` automatically.
3. Confirm the filename and path to the user.

---

## Brainstorm Protocol

Execute immediately — do not wait for additional instructions.

### With no arguments (`brainstorm`)

List all brainstorm files with their statuses:

1. Scan `.collab/brainstorms/` for all `.md` files (exclude `brainstorm-template.md`).
2. For each file, extract the `_Status:` value and the `# Title` heading.
3. Display a summary table:
   ```
   Status        | File
   --------------|------
   workshopping  | pypi-distribution.md — PyPI Distribution
   drafting      | my-idea.md — My Idea Title
   ```
4. If the directory is empty (no files besides the template), say so.

### With a title (`brainstorm <title>`)

Create a new brainstorm file and start workshopping it:

1. Convert the title to a filename: lowercase, hyphen-separated, `.md` extension (e.g. `brainstorm my cool idea` → `my-cool-idea.md`).
2. Check if `.collab/brainstorms/<filename>` already exists:
   - **Exists**: Read the file and resume workshopping (skip to step 4).
   - **Does not exist**: Create it from the template at `.collab/brainstorms/brainstorm-template.md`, filling in the title and today's date.
3. Confirm the file was created and its path.
4. Start workshopping — engage with the user collaboratively:
   - Ask what the idea is about — what problem it solves, what it would look like.
   - As the conversation develops, update the file: fill in **The Idea** section, append dated entries to **Discussion Log**, update **Next Steps / Open Questions**.
   - Assess honestly — identify gaps, ask clarifying questions, push back if something doesn't hold up.
   - Update the `Status` field as appropriate (`drafting` → `workshopping`).
5. Do **not** create tickets, tasks, or kanban entries from the brainstorm without explicit user approval.
6. If the user approves graduation: add `Graduated → Issue #__ on [date]` at the bottom, update status to `graduated`, and leave the file in place.

---

## Project Plan Protocol

Execute immediately — do not wait for additional instructions.

### With no arguments (`project plan`)

List all project plan files with their statuses:

1. Scan `.collab/project-plans/` for all `.md` files (exclude `project-plan-template.md`).
2. For each file, extract the `_Status:` value and the `# Title` heading.
3. Display a summary table:
   ```
   Status   | File
   ---------|------
   active   | api-redesign.md — API Redesign
   draft    | monitoring-setup.md — Monitoring Setup
   ```
4. If the directory is empty (no files besides the template), say so.

### With a title (`project plan <title>`)

Create a new project plan file and start workshopping it:

1. Convert the title to a filename: lowercase, hyphen-separated, `.md` extension (e.g. `project plan api redesign` → `api-redesign.md`).
2. Check if `.collab/project-plans/<filename>` already exists:
   - **Exists**: Read the file and resume workshopping (skip to step 4).
   - **Does not exist**: Create it from the template at `.collab/project-plans/project-plan-template.md`, filling in the title and today's date.
3. Confirm the file was created and its path.
4. Start workshopping — engage with the user collaboratively:
   - Clarify the goal — what does success look like?
   - Help define phases, tasks, risks, and dependencies.
   - As the conversation develops, update the file: fill in **Goal**, **Background**, **Phases**, **Risks & Dependencies**, and **Open Questions**.
   - Ask questions rather than assuming scope.
   - Update the `Status` field as appropriate (`draft` → `active`).
5. Do **not** promote tasks to the kanban board without explicit user approval.
6. When a phase is approved for execution: promote its tasks to `.collab/kanban-board.md`, note `Phase [N] promoted to kanban on [date]` at the bottom of the plan file, and leave the plan in place.

---

## Scaffold a new project

scaffy generates a `.collab/` multi-agent workspace into any project directory: collab contract, kanban board, context file, session summary templates, git governance templates, and agent instruction files (CLAUDE.md, AGENTS.md, GEMINI.md).

## Steps

1. **Find scaffy** — verify it's available:
   - Run `scaffy --help` to confirm
   - If not found, prompt the user to install: `pip install scaffy` or download from https://github.com/ColonelPanicX/scaffy/releases/latest

2. **Gather inputs** — ask the user for:
   - **Project name** — any valid folder name (lowercase hyphen-separated is conventional, e.g. `my-project`)
   - **Target path** — base directory where `.collab/` will be created
   - **Governance mode** — `lightweight`, `standard` (default), or `strict`
   - **Platform** — `github`, `gitlab`, `azure-devops`, or `none` (default)
   - **Description** — optional one-liner for `context.md`

3. **Run non-interactively:**
   ```bash
   scaffy --name <name> --path <path> --governance <mode> --platform <platform> [--description "<text>"]
   ```

4. **Report back** — confirm what was written, then print the contents of `<path>/.collab/prompts/initial-prompt.md` so the user can copy it into their agent on first launch.

## Upgrade an existing scaffold

```bash
scaffy --upgrade --path <path>
```

Diffs the existing `.collab/` against current templates and adds any missing files or directories. Does not overwrite existing files unless `--force` is added.

## Key flags

| Flag | Purpose |
|---|---|
| `--force` | Overwrite existing files |
| `--dry-run` | Preview planned actions without writing anything |
| `--governance MODE` | `lightweight`, `standard`, or `strict` |
| `--platform PLATFORM` | `github`, `gitlab`, `azure-devops`, or `none` |
| `--license LICENSE` | `mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense`, or `none` |
| `--ticket-prefix PREFIX` | Task ID prefix (e.g. `SCAF`); default: `TASK` |
| `--init-git` | Run `git init` in the project root after scaffolding |
| `--save-chat` | Export current agent session to `.collab/chat-logs/` |
| `--list-chats` | List recent agent sessions |
| `--session-id UUID` | Session UUID prefix to export (use with `--save-chat`) |
| `--cli {claude,codex,gemini}` | Agent CLI for `--save-chat` / `--list-chats`; auto-detected if omitted |
