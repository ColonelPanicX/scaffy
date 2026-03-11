# project-initialize

Initialize a project with a standard `.collab/` workspace scaffold for multi-agent collaboration.

## Purpose

`proj_init.py` creates a collaboration scaffold with:

- `.collab/collab-contract.md` — Rules, guardrails, and session protocols (OPEN/CLOSE SESSION)
- `.collab/kanban-board.md` — Task tracking board
- `.collab/context.md` — Stable project facts: tech stack, key files, conventions
- `.collab/project.yaml` — Machine-readable project metadata
- `.collab/initial-prompts/` — Onboarding prompt sequences for new and existing projects
- `.collab/session-summaries/` — Session summary directory with template
- `.collab/audit/` — Analysis reports and planning documents
- `.collab/git-management/` — Git governance templates
- `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` — Agent instruction files (root-level, tracked in git)
- `.gitignore` — Sane defaults (per-machine agent dirs excluded; agent instruction files tracked)

## Usage

```bash
# Interactive
python3 proj_init.py

# Fully scripted (non-interactive)
python3 proj_init.py --name my-project --path /path/to/base

# With flags
python3 proj_init.py --name my-project --path /path/to/base \
  --governance strict \
  --agent claude --agent codex \
  --description "Automates AWS resource exports to Excel" \
  --init-git

# Preview without writing
python3 proj_init.py --dry-run
```

## Flags

| Flag | Description | Default |
|---|---|---|
| `--name NAME` | Project name (lowercase, hyphen-separated) | interactive |
| `--path PATH` | Base directory for scaffold installation | interactive |
| `--force` | Overwrite existing files | off |
| `--dry-run` | Show planned actions without writing | off |
| `--governance MODE` | `lightweight`, `standard`, or `strict` | interactive (`standard`) |
| `--agent AGENT` | Agent(s) to generate root files for: `claude`, `codex`, `gemini`, `all`. Repeatable. | `all` |
| `--init-git` | Run `git init` in the project root after scaffolding | off |
| `--description TEXT` | Short description injected into `context.md` and agent files | interactive (optional) |

## Governance Modes

| Mode | Use when |
|---|---|
| `lightweight` | Prototypes, solo work, fast iteration |
| `standard` | Most active projects (recommended default) |
| `strict` | Compliance, regulated, or high-risk work |

## Session Protocols

The scaffold installs two trigger phrases into all agent contracts:

- **`OPEN SESSION`** — Agent reads the latest session summary, kanban board, and context,
  then delivers a concise resume of where things stand. Use at the start of every session.
- **`CLOSE SESSION`** — Agent writes a session summary and updates the kanban board.
  Use at the end of every session.

## Behavior

- If `--name` and `--path` are both provided, runs non-interactively.
- Otherwise prompts for: mode (new/existing), target directory, project name, governance mode,
  and description.
- Existing `.gitignore` is not overwritten — template is written to `.collab/.gitignore.template` instead.
- Agent instruction files (`CLAUDE.md`, etc.) are written to the project root and are **not** gitignored
  by default — they are intended to be tracked in version control.
- Uses `America/New_York` and `MM.DD.YYYY` date formatting in generated templates.

## Make `proj_init` Available Everywhere

```bash
mkdir -p ~/.local/bin
chmod +x path/to/project-initialize/proj_init.py
ln -sf path/to/project-initialize/proj_init.py ~/.local/bin/proj_init
```

Ensure `~/.local/bin` is on your `PATH` (Bash):

```bash
grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc \
  || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
which proj_init
proj_init --help
```

If you move the script later, update the symlink:

```bash
ln -sf /new/path/to/proj_init.py ~/.local/bin/proj_init
```
