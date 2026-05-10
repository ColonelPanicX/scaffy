---
name: scaffy
description: Use this skill when the user wants to bootstrap a new project workspace, initialize a .collab/ directory, scaffold a multi-agent collaboration setup, set up a new project with scaffy, or export a Codex session transcript via SAVE CHAT.
---

# scaffy — .collab/ Workspace Bootstrapper

scaffy generates a `.collab/` multi-agent workspace into any project directory: collab contract, kanban board, context file, session summary templates, git governance templates, and agent instruction files (CLAUDE.md, AGENTS.md, GEMINI.md).

## Save Chat (SAVE CHAT)

When the user types `SAVE CHAT`, export the current Codex session transcript:

```bash
# If scaffy is on PATH:
scaffy --save-chat --cli codex

# Otherwise:
python3 scaffy.py --save-chat --cli codex
```

The transcript is saved to `.collab/chat-logs/MM.DD.YYYY-codex-chat.md` in the current project directory. Confirm the filename and path to the user.

To list recent sessions:
```bash
scaffy --list-chats --cli codex
```

To export a specific session by UUID prefix:
```bash
scaffy --save-chat --cli codex --session-id <uuid-prefix>
```

---

## How to use

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
| `--governance MODE` | `lightweight`, `standard`, or `strict` |
| `--platform PLATFORM` | `github`, `gitlab`, `azure-devops`, or `none` |
| `--license LICENSE` | `mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense`, or `none` |
| `--ticket-prefix PREFIX` | Task ID prefix (e.g. `SCAF`); default: `TASK` |
| `--init-git` | Run `git init` in the project root after scaffolding |
| `--save-chat` | Export current agent session to `.collab/chat-logs/` |
| `--list-chats` | List recent agent sessions |
| `--session-id UUID` | Session UUID prefix to export (use with `--save-chat`) |
| `--cli {claude,codex,gemini}` | Agent CLI for `--save-chat` / `--list-chats`; auto-detected if omitted |
