---
name: scaffy
description: Use this skill when the user wants to bootstrap a new project workspace, initialize a .collab/ directory, scaffold a multi-agent collaboration setup, set up a new project with scaffy, or run session protocols (open/save/close/save-chat) for an existing scaffy project.
---

# scaffy — .collab/ Workspace Bootstrapper

Route based on the user's request:

- `open session` → **Session Open Protocol**
- `save session` → **Session Save Protocol**
- `close session` → **Session Close Protocol**
- `save chat` → **Chat Save Protocol**
- anything else (project name, path, flags, or empty) → **Scaffold a new project**

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
   - Include a `## Re-entry Prompt` section in the summary (see step 3).
2. Update `.collab/kanban-board.md` to reflect current task state.
3. Generate a re-entry prompt and output it as a copyable block. The prompt should be self-contained — everything a fresh agent needs to pick up exactly where this session left off:
   - Project name and one-line purpose
   - What was accomplished this session
   - What is currently in-flight (active task, any partial work)
   - What comes next
   - Any open decisions or blockers
   Also write this prompt into the `## Re-entry Prompt` section of the session summary file.
4. Confirm the checkpoint was saved. Do not end the session — continue working.

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
