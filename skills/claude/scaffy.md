scaffy skill — bootstrap a `.collab/` workspace, or run session protocols for an existing one.

## Dispatch on $ARGUMENTS

Read $ARGUMENTS first and route accordingly:

- `open session` → **Session Open Protocol** (see below)
- `save session` → **Session Save Protocol** (see below)
- `close session` → **Session Close Protocol** (see below)
- `save chat` → **Chat Save Protocol** (see below)
- anything else (project name, path, flags, or empty) → **Scaffold a new project** (see below)

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
   - First summary that day: `MM.DD.YYYY-claude-summary.md`
   - Additional same-day saves: `MM.DD.YYYY-02-claude-summary.md`, `MM.DD.YYYY-03-claude-summary.md`, etc.
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
   - If scaffy is on PATH: `scaffy --save-session`
   - Otherwise: `python3 scaffy.py --save-session`
2. The tool saves the transcript to `.collab/chat-logs/` automatically.
3. Confirm the filename and path to the user.

---

## Scaffold a new project

scaffy generates a `.collab/` multi-agent workspace into any project directory: collab contract, kanban board, context file, session summary templates, git governance templates, and agent instruction files (CLAUDE.md, AGENTS.md, GEMINI.md).

## Steps

1. **Find scaffy** — check in order:
   - `scaffy --help` (installed globally via symlink)
   - `python3 scaffy.py --help` (in current directory or project root)
   - If not found, tell the user to download from https://github.com/ColonelPanicX/scaffy/releases/latest

2. **Gather inputs** — extract from $ARGUMENTS if present, otherwise ask:
   - **Project name** — lowercase, hyphen-separated (e.g. `my-project`)
   - **Target path** — base directory where `.collab/` will be created
   - **Governance mode** — `lightweight`, `standard` (default), or `strict`
   - **Platform** — `github`, `gitlab`, `azure-devops`, or `none` (default)
   - **Description** — optional one-liner for `context.md`

3. **Run non-interactively:**
   ```bash
   python3 scaffy.py --name <name> --path <path> --governance <mode> --platform <platform> [--description "<text>"]
   ```

4. **Report back** — confirm what was written, then print the contents of `<path>/.collab/prompts/initial-prompt.md` so the user can copy it into their agent on first launch.

## Upgrade an existing scaffold

```bash
python3 scaffy.py --upgrade --path <path>
```

Diffs the existing `.collab/` against current templates and adds any missing files or directories. Does not overwrite existing files unless `--force` is added.

## Key flags

| Flag | Purpose |
|---|---|
| `--force` | Overwrite existing files |
| `--dry-run` | Preview planned actions without writing anything |
| `--init-git` | Run `git init` in the project root after scaffolding |
| `--license LICENSE` | Write a LICENSE file (`mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense`) |
