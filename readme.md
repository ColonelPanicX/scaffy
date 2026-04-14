# scaffy

Initialize a project with a standard `.collab/` workspace scaffold for multi-agent collaboration.

## Quickstart

### Windows — GUI (exe)

1. Download `scaffy.exe` from the [latest release](https://github.com/ColonelPanicX/scaffy/releases/latest)
2. Double-click to run — no install needed
3. Fill in **Project Name** and **Target Path**, adjust options, click **Build!**
4. When the build completes, a popup shows the initial prompt — copy it and paste into your AI agent to start your first session

<img width="642" height="750" alt="image" src="https://github.com/user-attachments/assets/ebaf4f61-7a5d-45de-8e01-378a531e9da3" />


---

### Python — CLI (Mac / Linux / Windows)

Requires Python 3.9+. No dependencies to install.

1. Download `scaffy.py` from the [latest release](https://github.com/ColonelPanicX/scaffy/releases/latest)
2. Run it — scaffy will walk you through the rest:

   ```bash
   python3 scaffy.py
   ```

3. Follow the prompts: project name, target path, governance level, platform, and an optional description
4. When scaffolding completes, the terminal prints the initial prompt — copy it and paste into your AI agent to start your first session

To skip the prompts entirely:

```bash
python3 scaffy.py --name my-project --path /path/to/base \
  --governance standard \
  --platform github
```

---

## Purpose

`scaffy.py` creates a collaboration scaffold with:

- `.collab/collab-contract.md` — Rules, guardrails, and session protocols (OPEN/CLOSE SESSION)
- `.collab/kanban-board.md` — Task tracking board
- `.collab/context.md` — Stable project facts: tech stack, key files, conventions
- `.collab/project.yaml` — Machine-readable project metadata
- `.collab/initial-prompt.md` — First-session onboarding prompt (paste on first launch)
- `.collab/agent-profile.md` — Fill-in questionnaire for generating agent instructions (CLAUDE.md, AGENTS.md, etc.)
- `.collab/brainstorm/` — Thinking space for pre-ticket concepts and proposals
- `.collab/session-summaries/` — Session summary directory with template
- `.collab/audit/` — Analysis reports and planning documents
- `.collab/supporting-artifacts/` — Diagrams, specs, research, and other project-adjacent materials
- `.collab/prompts/` — Reusable agent prompts, including the agent instructions generator
- `.collab/playbooks/` — Reference playbooks; includes a generic coding standards playbook
- `.collab/git-management/` — Git governance templates
- `.gitignore` — Sane defaults (`.collab/` and agent dirs excluded from version control)

## Usage

```bash
# Interactive
python3 scaffy.py

# Fully scripted (non-interactive)
python3 scaffy.py --name my-project --path /path/to/base

# With flags
python3 scaffy.py --name my-project --path /path/to/base \
  --governance strict \
  --platform github \
  --description "Automates AWS resource exports to Excel" \
  --init-git

# Preview without writing
python3 scaffy.py --dry-run
```

## Flags

| Flag | Description | Default |
|---|---|---|
| `--name NAME` | Project name (lowercase, hyphen-separated recommended) | interactive |
| `--path PATH` | Base directory for scaffold installation | interactive |
| `--force` | Overwrite existing files | off |
| `--dry-run` | Show planned actions without writing | off |
| `--governance MODE` | `lightweight`, `standard`, or `strict` | interactive (`standard`) |
| `--platform PLATFORM` | `github`, `gitlab`, or `none` — writes platform-native issue and PR/MR templates | interactive (`none`) |
| `--license LICENSE` | `mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense`, or `none` — writes a `LICENSE` file | interactive (`none`) |
| `--init-git` | Run `git init` in the project root after scaffolding | off |
| `--description TEXT` | Short description injected into `context.md` | interactive (optional) |

## Governance Modes

| Mode | Use when |
|---|---|
| `lightweight` | Prototypes, solo work, fast iteration |
| `standard` | Most active projects (recommended default) |
| `strict` | Compliance, regulated, or high-risk work |

## First Session

After scaffolding, the terminal prints the full onboarding prompt between separator lines — copy it and paste it directly into your agent on first launch. The same prompt is saved to `.collab/initial-prompt.md` as a backup.

The prompt orients the agent to the `.collab/` structure, initializes its memory with stable project facts, and installs the OPEN/CLOSE SESSION protocols for all future sessions.

## Session Protocols

The scaffold installs two trigger phrases into the agent contract and initial prompt:

- **`OPEN SESSION`** — Agent reads the latest session summary, kanban board, and context,
  then delivers a concise resume of where things stand. Use at the start of every session.
- **`CLOSE SESSION`** — Agent writes a session summary and updates the kanban board.
  Use at the end of every session.

## Brainstorm Workflow

The `.collab/brainstorm/` directory is a persistent thinking space for ideas that aren't ready to
become formal tickets yet. It bridges the gap between "I had a thought" and "I opened an issue."

**How it works:**

1. Create a file for your idea: `.collab/brainstorm/my-idea-name.md`
2. Use `.collab/brainstorm/brainstorm-template.md` as a starting point
3. Brain dump freely — no rules, no required format in the idea body
4. When ready, point your agent at the file: *"Hey, look at this idea — does it have legs?"*
5. The agent will engage honestly, then append a dated summary to the **Discussion Log** section
6. Ideas evolve over time. Status tracks the lifecycle: `drafting` → `workshopping` → `parked` or `graduated`
7. When an idea becomes a ticket, note the issue number at the bottom and leave the file in place

**Key property:** nothing in `brainstorm/` is required to go anywhere. Ideas can sit, evolve slowly,
or be parked indefinitely. The point is keeping them on paper so they aren't lost when a session closes.

When scaffolding into an **existing project**, scaffy will print a reminder to migrate any ideas
you already have written down or in your head into the new directory.

## Behavior

- If `--name` and `--path` are both provided, runs non-interactively.
- Otherwise prompts for: mode (new/existing), target directory, project name, governance mode,
  and description.
- Existing `.gitignore` is not overwritten — template is written to `.collab/.gitignore.template` instead.
- Uses `America/New_York` and `MM.DD.YYYY` date formatting in generated templates.

## Make `scaffy` Available Everywhere

```bash
mkdir -p ~/.local/bin
chmod +x path/to/scaffy/scaffy.py
ln -sf path/to/scaffy/scaffy.py ~/.local/bin/scaffy
```

Ensure `~/.local/bin` is on your `PATH` (Bash):

```bash
grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc \
  || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Verify:

```bash
which scaffy
scaffy --help
```

If you move the script later, update the symlink:

```bash
ln -sf /new/path/to/scaffy.py ~/.local/bin/scaffy
```
