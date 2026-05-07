# scaffy

Initialize a project with a standard `.collab/` workspace scaffold for multi-agent collaboration.

## Install

```bash
pipx install scaffy-collab
```

That's it. `scaffy` is now available system-wide. Requires Python 3.9+ and [pipx](https://pipx.pypa.io).

```bash
scaffy --help
```

> **Windows users:** grab the GUI instead — see below.

---

## Quickstart

### Windows — GUI (exe)

1. Download `scaffy.exe` from the [latest release](https://github.com/ColonelPanicX/scaffy/releases/latest)
2. Double-click to run — no install needed
3. Fill in **Project Name** and **Target Path**, adjust options, click **Build!**
4. When the build completes, a popup shows the initial prompt — copy it and paste into your AI agent to start your first session

<img width="642" height="750" alt="image" src="https://github.com/user-attachments/assets/ebaf4f61-7a5d-45de-8e01-378a531e9da3" />


---

### Python — CLI (Mac / Linux / Windows)

**Recommended:** install via pipx (see above), then run:

```bash
scaffy
```

**Alternative:** download `scaffy.py` from the [latest release](https://github.com/ColonelPanicX/scaffy/releases/latest) and run directly — no install needed:

```bash
python3 scaffy.py
```

Either way, scaffy walks you through the rest. Follow the prompts — at any step, type `b` to go back or `q` to quit. When scaffolding completes, the terminal prints the initial prompt — copy it and paste into your AI agent to start your first session.

To skip the prompts entirely:

```bash
scaffy --name my-project --path /path/to/base \
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
- `.collab/prompts/initial-prompt.md` — First-session onboarding prompt (paste on first launch)
- `.collab/prompts/agent-profile.md` — Fill-in questionnaire for generating agent instructions (CLAUDE.md, AGENTS.md, etc.)
- `.collab/brainstorms/` — Thinking space for pre-ticket concepts and proposals
- `.collab/session-summaries/` — Session summary directory with template
- `.collab/audit/` — Analysis reports and planning documents
- `.collab/supporting-artifacts/` — Diagrams, specs, research, and other project-adjacent materials
- `.collab/prompts/` — Reusable agent prompts, including the agent instructions generator
- `.collab/guides/` — Reference docs: git governance modes, branching strategy, label taxonomy
- `.collab/playbooks/` — Step-by-step procedures: coding standards, per-mode git governance playbooks
- `.collab/playbooks/templates/` — Fill-in-the-blank forms: issue and pull request templates
- `.gitignore` — Sane defaults (`.collab/` and agent dirs excluded from version control)

## Usage

```bash
# Interactive
scaffy

# Fully scripted (non-interactive)
scaffy --name my-project --path /path/to/base

# With flags
scaffy --name my-project --path /path/to/base \
  --governance strict \
  --platform github \
  --description "Automates AWS resource exports to Excel" \
  --init-git

# Preview without writing
scaffy --dry-run
```

## Flags

| Flag | Description | Default |
|---|---|---|
| `--name NAME` | Project name | interactive |
| `--path PATH` | Base directory for scaffold installation | interactive |
| `--force` | Overwrite existing files | off |
| `--dry-run` | Show planned actions without writing | off |
| `--governance MODE` | `lightweight`, `standard`, or `strict` | interactive (`standard`) |
| `--platform PLATFORM` | `github`, `gitlab`, or `none` — writes platform-native issue and PR/MR templates | interactive (`none`) |
| `--license LICENSE` | `mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense`, or `none` — writes a `LICENSE` file | interactive (`none`) |
| `--init-git` | Run `git init` in the project root after scaffolding | off |
| `--description TEXT` | Short description injected into `context.md` | interactive (optional) |
| `--upgrade` | Upgrade an existing `.collab/` scaffold to the latest templates | off |
| `--cli CLI` | Agent CLI for `--save-chat` / `--list-chats`: `claude`, `codex`, `gemini` | auto-detect |

## Governance Modes

| Mode | Use when |
|---|---|
| `lightweight` | Prototypes, solo work, fast iteration |
| `standard` | Most active projects (recommended default) |
| `strict` | Compliance, regulated, or high-risk work |

## First Session

After scaffolding, the terminal prints the full onboarding prompt between separator lines — copy it and paste it directly into your agent on first launch. The same prompt is saved to `.collab/prompts/initial-prompt.md` as a backup.

The prompt orients the agent to the `.collab/` structure, initializes its memory with stable project facts, and installs the OPEN/CLOSE SESSION protocols for all future sessions.

## Session Protocols

The scaffold installs four trigger phrases into the agent contract and initial prompt:

- **`OPEN SESSION`** — Agent reads the latest session summary, kanban board, and context,
  then delivers a concise resume of where things stand. Use at the start of every session.
- **`SAVE SESSION`** — Mid-session checkpoint. Agent writes a summary and updates the kanban,
  then continues working. Use any time you want to preserve progress without closing.
- **`CLOSE SESSION`** — Agent writes a session summary and updates the kanban board.
  Use at the end of every session.
- **`SAVE CHAT`** — Exports the full session transcript to `.collab/chat-logs/` as a markdown
  file. Session UUID preserved in the header for traceability. Supported for Claude Code,
  Gemini CLI, and Codex CLI. scaffy auto-detects the running agent when invoked from inside
  a chat session. If run from a plain terminal after the session ends, auto-detection is not
  possible and scaffy will prompt you to select the agent (1/2/3). Use
  `scaffy --save-chat --cli <agent>` to skip the prompt.

## Brainstorm Workflow

The `.collab/brainstorms/` directory is a persistent thinking space for ideas that aren't ready to
become formal tickets yet. It bridges the gap between "I had a thought" and "I opened an issue."

**How it works:**

1. Create a file for your idea: `.collab/brainstorms/my-idea-name.md`
2. Use `.collab/brainstorms/brainstorm-template.md` as a starting point
3. Brain dump freely — no rules, no required format in the idea body
4. When ready, point your agent at the file: *"Hey, look at this idea — does it have legs?"*
5. The agent will engage honestly, then append a dated summary to the **Discussion Log** section
6. Ideas evolve over time. Status tracks the lifecycle: `drafting` → `workshopping` → `parked` or `graduated`
7. When an idea becomes a ticket, note the issue number at the bottom and leave the file in place

**Key property:** nothing in `brainstorms/` is required to go anywhere. Ideas can sit, evolve slowly,
or be parked indefinitely. The point is keeping them on paper so they aren't lost when a session closes.

When scaffolding into an **existing project**, scaffy will print a reminder to migrate any ideas
you already have written down or in your head into the new directory.

## Additional Enhancements

The scaffold includes two optional tools in `.collab/prompts/` to help you get more out of your agent setup:

### Agent Instructions Generator

`.collab/prompts/agent-profile.md` is a fill-in questionnaire that captures your project's
tech stack, key commands, conventions, and guardrails — the things an agent needs to collaborate
well with you. Once filled out, paste `.collab/prompts/agent-md-prompt.md` into your agent
and it will generate a tailored `CLAUDE.md`, `AGENTS.md`, or equivalent instructions file
for the project root.

### Coding Playbook

`.collab/playbooks/coding-playbook.md` is a pre-populated reference covering general software
development best practices — code quality, testing, security, documentation, and more.
It's a starting point: edit it down to what matters for your project, or leave it as a
general reference for your agent to consult.

### Git Governance

`.collab/guides/git-guidelines.md` is a reference guide explaining the governance modes,
branching strategy, label taxonomy, PR standards, and platform notes for GitHub and GitLab.

Three matching execution playbooks in `.collab/playbooks/` give each governance mode a
concrete step-by-step procedure for starting work, committing, opening PRs, merging, and
handling hotfixes:

- `git-governance-lightweight.md` — prototypes and sandboxes
- `git-governance-standard.md` — active product development (default)
- `git-governance-strict.md` — compliance-sensitive or auditable work

Fill-in-the-blank issue and PR templates live in `.collab/playbooks/templates/`.

### Agent Skills

The [`skills/`](skills/) directory contains installable slash commands for Claude Code and Gemini CLI, and a passive skill for Codex CLI. Once installed, your agent knows how to run scaffy without you explaining it.

| Agent | File | Type |
|---|---|---|
| Claude Code | `skills/claude/scaffy.md` | `/scaffy` slash command |
| Gemini CLI | `skills/gemini/scaffy.toml` | `/scaffy` slash command |
| Codex CLI | `skills/codex/scaffy/` | AI-activated (no slash command) |

**Install (global):**

```bash
# Claude Code
cp skills/claude/scaffy.md ~/.claude/commands/scaffy.md

# Gemini CLI
cp skills/gemini/scaffy.toml ~/.gemini/commands/scaffy.toml

# Codex CLI
cp -r skills/codex/scaffy ~/.codex/skills/scaffy
```

**Claude & Gemini:** type `/scaffy` to bootstrap a project — the agent gathers inputs and runs scaffy for you. Pass a project name or path as arguments to skip the prompts.

The Claude skill also handles session protocols. If you use scaffy's session conventions in your projects, you can invoke them via the skill as a more reliable alternative to the plain-text trigger:

```
/scaffy open session
/scaffy save session
/scaffy close session
/scaffy save chat
```

**Codex:** no slash command — Codex pulls the skill in automatically when it detects a scaffolding need.

---

## scafrag — Optional Companion Tool

`scafrag.py` is a completely optional companion script that lives alongside `scaffy.py`. Nothing
in scaffy requires it, and you won't miss anything by skipping it. But if you end up using
scaffy across multiple projects, it becomes useful.

**What it does:** indexes the `.collab/` workspaces across all your projects and lets you query
them — searching for past decisions, checking cross-project status, or dumping full context for
a project in one command.

```bash
# Build the index (point it at your projects root)
python3 scafrag.py index --root ~/code

# Search across all projects
python3 scafrag.py query "authentication middleware"

# Full context dump for one project
python3 scafrag.py context my-project

# Portfolio view — all projects with kanban lane counts
python3 scafrag.py status

# List all indexed projects
python3 scafrag.py projects
```

All commands support `--format text` (default), `--format json`, and `--format markdown`.
Output goes to stdout — pipe it wherever you want, including directly into an AI agent.

**Requirements:** Python 3.9+. No external dependencies — same as `scaffy.py`.

Windows users: `scafrag.exe` is available in the [latest release](https://github.com/ColonelPanicX/scaffy/releases/latest) — no Python required. Run it from Command Prompt or PowerShell.

---

## Behavior

- If `--name` and `--path` are both provided, runs non-interactively.
- Otherwise launches an interactive wizard: at any prompt, type `b` to go back one step or `q` to quit.
- Existing `.gitignore` is not overwritten — template is written to `.collab/.gitignore.template` instead.
- Uses `America/New_York` and `MM.DD.YYYY` date formatting in generated templates.

## See Also

Tools and resources that pair well with the structured approach scaffy promotes. None are required.

- **[GSD](https://github.com/gsd-build/gsd-2)** — Spec-driven development system for autonomous multi-phase agent work: research, planning, execution, and git management in a single pipeline.
- **[MemPalace](https://github.com/MemPalace/mempalace/tree/main)** — Local-first AI memory with semantic search. Complements scaffy's session summaries with queryable, persistent long-term recall.
- **[Caveman](https://github.com/JuliusBrussee/caveman)** — Claude Code skill that compresses agent output by ~75% using terse, technical language. Same accuracy, far fewer tokens.
- **[Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** — Pattern for building a personal knowledge base where an LLM incrementally maintains a persistent wiki synthesized from source documents.
