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
scaffy --save-session --cli codex

# Otherwise:
python3 scaffy.py --save-session --cli codex
```

The transcript is saved to `.collab/chat-logs/MM.DD.YYYY-codex-chat.md` in the current project directory. Confirm the filename and path to the user.

To list recent sessions:
```bash
scaffy --list-sessions --cli codex
```

To export a specific session by UUID prefix:
```bash
scaffy --save-session --cli codex --session-id <uuid-prefix>
```

---

## How to use

1. **Find scaffy** — check in order:
   - `scaffy --help` (installed globally via symlink)
   - `python3 scaffy.py --help` (in current directory or project root)
   - If not found, prompt the user to download from https://github.com/ColonelPanicX/scaffy/releases/latest

2. **Gather inputs** — ask the user for:
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
