# scaffy

Initialize a project with a standard `.collab/` workspace scaffold for multi-agent collaboration.

## Install

```bash
pipx install scaffy-collab
```

That's it. `scaffy` is now available system-wide. Requires Python 3.10+ and [pipx](https://pipx.pypa.io).

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
- `.collab/agent-bridge/` — Shared-file channels between agents of different types (empty until you open one)
- `.collab/audit/` — Analysis reports and planning documents
- `.collab/project-plans/` — Long-form plans, architecture docs, and multi-phase roadmaps
- `.collab/skills/` — The scaffy skill for Claude, Codex and Gemini (copy one to where your CLI loads skills), plus any project-specific skills
- `.collab/inbox/` — Drop zone for files that might be useful; sort them out with your agent
- `.collab/prompts/` — Reusable agent prompts, including the agent instructions generator
- `.collab/playbooks/` — How-to guides: coding standards, git guidelines, the git playbook for your governance mode, agent bridges
- `.collab/templates/` — Starting points for session summaries, brainstorms, project plans, issues and pull requests
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
| `--platform PLATFORM` | `github`, `gitlab`, `azure-devops`, or `none` — writes platform-native issue and PR/MR templates | interactive (`none`) |
| `--license LICENSE` | `mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense`, or `none` — writes a `LICENSE` file | interactive (`none`) |
| `--ticket-prefix PREFIX` | Task ID prefix rendered in `kanban-board.md` (e.g. `SCAF`) | interactive (`TASK`) |
| `--init-git` | Run `git init` in the project root after scaffolding | off |
| `--description TEXT` | Short description injected into `context.md` | interactive (optional) |
| `--upgrade` | Upgrade an existing `.collab/` scaffold to the latest templates. Adds missing files only; with `--force` also refreshes scaffold-managed files, saving the old versions to `.collab/.upgrade-backups/<timestamp>/`. Kanban, context, north-star, project.yaml, initial-prompt and LICENSE are never replaced | off |
| `--save-chat` | Export the current agent session to `.collab/chat-logs/` | off |
| `--list-chats` | List recent agent sessions | off |
| `--session-id UUID` | Session UUID prefix to export (use with `--save-chat`) | most recent |
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
- **`SAVE SESSION`** — Mid-session checkpoint. Agent writes a summary, updates the kanban,
  and generates a **re-entry prompt** — a self-contained block you can paste into a new chat
  to resume exactly where you left off after clearing context. Then continues working.
- **`CLOSE SESSION`** — Agent writes a session summary and updates the kanban board.
  Use at the end of every session.
- **`SAVE CHAT`** — Exports the full session transcript to `.collab/chat-logs/` as a markdown
  file. Session UUID preserved in the header for traceability. Supported for Claude Code,
  Gemini CLI, and Codex CLI. scaffy auto-detects the running agent when invoked from inside
  a chat session. If run from a plain terminal after the session ends, auto-detection is not
  possible and scaffy will prompt you to select the agent (1/2/3). Use
  `scaffy --save-chat --cli <agent>` to skip the prompt.

## North Star

`.collab/north-star.md` is a one-page statement of where the project is headed: the problem,
who it's for, what success looks like, non-goals, guiding principles, and the signals that
work is drifting. Every scaffold ships it as a `draft`.

Run `/scaffy north star` and the agent interviews you one topic at a time, writes the answers
in as you go, and proposes the one-sentence North Star at the end. Once you mark it `agreed`:

- `OPEN SESSION` reads it and flags board items that pull away from it
- Agents check plans, brainstorms, and priorities against it, and say so when work conflicts
- It only changes with your explicit approval; each change is a dated Revision Log row
- `scaffy --upgrade` never overwrites it (older scaffolds get the draft added)

## Brainstorm Workflow

The `.collab/brainstorms/` directory is a persistent thinking space for ideas that aren't ready to
become formal tickets yet. It bridges the gap between "I had a thought" and "I opened an issue."

**How it works:**

1. Create a file for your idea: `.collab/brainstorms/my-idea-name.md`
2. Use `.collab/templates/brainstorm-template.md` as a starting point
3. Brain dump freely — no rules, no required format in the idea body
4. When ready, point your agent at the file: *"Hey, look at this idea — does it have legs?"*
5. The agent will engage honestly, then append a dated summary to the **Discussion Log** section
6. Ideas evolve over time. Status tracks the lifecycle: `drafting` → `workshopping` → `parked` or `graduated`
7. When an idea becomes a ticket, note the issue number at the bottom and leave the file in place

**Key property:** nothing in `brainstorms/` is required to go anywhere. Ideas can sit, evolve slowly,
or be parked indefinitely. The point is keeping them on paper so they aren't lost when a session closes.

### Brainstorm sessions

For a question with many possible answers, run `/scaffy brainstorm session <topic>`. The agent
facilitates five phases and writes `.collab/brainstorms/<topic>-session-MM.DD.YYYY.md` as it goes:

1. **Frame** — agree on the question, constraints, and what a good outcome looks like
   (checked against the North Star if you have one)
2. **Diverge** — you go first, then the agent adds ideas from new angles; nothing is judged yet
3. **Cluster** — group the ideas into themes
4. **Converge** — rate the strongest against agreed criteria; you pick the shortlist
5. **Close** — open questions and proposed next steps; status set to `complete`

The file is saved after every phase, so an interrupted session can be resumed. Shortlisted ideas
can be spun off into their own brainstorm files or a project plan. Nothing becomes a ticket
without your approval.

When scaffolding into an **existing project**, scaffy will print a reminder to migrate any ideas
you already have written down or in your head into the new directory.

## Inbox

`.collab/inbox/` is a drop zone. Put anything that might be useful to the project there (notes,
exports, screenshots, specs) before you know where it belongs, then ask your agent to go through
it with you. The agent proposes what to do with each item and moves or deletes nothing without
your approval. OPEN SESSION mentions it when items are waiting.

Upgrading from an older scaffold moves anything in `.collab/supporting-artifacts/` into the inbox.

## Agent Bridge

When one project uses agents of **different types** (say Claude and Codex), they can't message
each other directly. An agent bridge gives them a shared channel: two agents coordinate on one
problem through files in `.collab/agent-bridge/<name>/`, and you monitor instead of relaying
every message. Agents of the same type should use their CLI's own messaging instead.

- `/scaffy bridge open <name>`: the agent becomes the **initiator**. It agrees the two roles and
  the scope with you, writes `README.md`, the first message in `transcript.md`, and `status.md`,
  then gives you the path to hand to the other agent.
- `/scaffy bridge check`: the other agent (the **responder**) reads the bridge and replies;
  either side uses it to pick up new messages.
- `/scaffy bridge close`: the initiator posts a closing summary; the responder acknowledges.

Transcripts are append-only with UTC timestamps, and closed bridges are kept as a record.
Agents never commit, push, or change code because of a bridge message without your approval.
The full procedure is in `.collab/playbooks/agent-bridge-playbook.md`.

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

`.collab/playbooks/git-guidelines.md` is a reference guide explaining the governance modes,
branching strategy, label taxonomy, PR standards, and platform notes for GitHub and GitLab.

Each governance mode has a step-by-step playbook for starting work, committing, opening PRs,
merging, and handling hotfixes. scaffy writes only the one for your project's mode to
`.collab/playbooks/git-governance-<mode>.md` (none for mode `none`); if you change mode,
update `project.yaml` and run `scaffy --upgrade` to add the new one:

- `git-governance-lightweight.md` — prototypes and sandboxes
- `git-governance-standard.md` — active product development (default)
- `git-governance-strict.md` — compliance-sensitive or auditable work

Fill-in-the-blank issue and PR templates live in `.collab/templates/`.

### Agent Skills

scaffy ships a skill for each agent CLI: a slash command for Claude Code and Gemini CLI, and a passive skill for Codex CLI. Once installed, your agent knows how to run scaffy without you explaining it.

Every scaffold includes them in `.collab/skills/<agent>/scaffy/SKILL.md`, and the same files are in this repo's [`skills/`](skills/) directory if you want to install before scaffolding anything. scaffy doesn't install them for you: copy the one for your CLI to where it loads skills. `scaffy --upgrade --force` refreshes the copies in `.collab/skills/` (re-copy afterwards to pick up changes).

| Agent | File | Invocation |
|---|---|---|
| Claude Code | `skills/claude/scaffy/SKILL.md` | `/scaffy` |
| Gemini CLI | `skills/gemini/scaffy/SKILL.md` | `/scaffy` |
| Codex CLI | `skills/codex/scaffy/SKILL.md` | AI-activated |

**Install (global)**, from this repo or from any scaffolded project's `.collab/` (use `.collab/skills/...` in place of `skills/...`):

```bash
# Claude Code
mkdir -p ~/.claude/skills && cp -r skills/claude/scaffy ~/.claude/skills/scaffy

# Gemini CLI
mkdir -p ~/.gemini/skills && cp -r skills/gemini/scaffy ~/.gemini/skills/scaffy

# Codex CLI
mkdir -p ~/.codex/skills && cp -r skills/codex/scaffy ~/.codex/skills/scaffy
```

**Claude & Gemini:** type `/scaffy` to bootstrap a project — the agent gathers inputs and runs scaffy for you. Pass a project name or path as arguments to skip the prompts.

All three skills support session protocols and workspace commands. If you use scaffy's session conventions in your projects, invoke them via the skill:

```
/scaffy initialize          # First-session onboarding — reads workspace, does repo recon, seeds kanban
/scaffy open session        # Resume from latest session summary
/scaffy save session        # Mid-session checkpoint with re-entry prompt
/scaffy close session       # End-of-session summary and kanban update
/scaffy save chat           # Export transcript to .collab/chat-logs/
/scaffy north star          # Draft (interview) or review the project's North Star
/scaffy brainstorm          # List brainstorms with statuses
/scaffy brainstorm <title>  # Create or resume a brainstorm and start workshopping
/scaffy brainstorm session <topic>  # Facilitated session (frame → ideas → shortlist) that writes a brainstorm doc
/scaffy project plan        # List project plans with statuses
/scaffy project plan <title> # Create or resume a project plan and start workshopping
/scaffy bridge              # List agent bridges and who holds the ball
/scaffy bridge open <name>  # Open a bridge to an agent of a different type
/scaffy bridge check [name] # Read the bridge and reply if needed
/scaffy bridge close [name] # Close (initiator) or acknowledge the close (responder)
```

**Codex:** no slash command — Codex pulls the skill in automatically when it detects a scaffolding or session need.

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

**Requirements:** Python 3.10+. No external dependencies — same as `scaffy.py`.

Windows users: `scafrag.exe` is available in the [latest release](https://github.com/ColonelPanicX/scaffy/releases/latest) — no Python required. Run it from Command Prompt or PowerShell.

---

## Behavior

- If `--name` and `--path` are both provided, runs non-interactively.
- Otherwise launches an interactive wizard: at any prompt, type `b` to go back one step or `q` to quit.
- Existing `.gitignore` is not overwritten — template is written to `.collab/.gitignore.template` instead.
- Uses `America/New_York` and `MM.DD.YYYY` date formatting in generated templates.

## Tests

Tests use the standard library only (no install needed) and run scaffy/scafrag as real
CLI subprocesses inside temp directories:

```bash
python -m unittest discover -s tests -t .
```

CI runs them on every push and PR to `dev` and `main` (Python 3.10–3.13, plus Windows).

## See Also

Tools and resources that pair well with the structured approach scaffy promotes. None are required.

- **[GSD](https://github.com/gsd-build/gsd-2)** — Spec-driven development system for autonomous multi-phase agent work: research, planning, execution, and git management in a single pipeline.
- **[MemPalace](https://github.com/MemPalace/mempalace/tree/main)** — Local-first AI memory with semantic search. Complements scaffy's session summaries with queryable, persistent long-term recall.
- **[Caveman](https://github.com/JuliusBrussee/caveman)** — Claude Code skill that compresses agent output by ~75% using terse, technical language. Same accuracy, far fewer tokens.
- **[Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)** — Pattern for building a personal knowledge base where an LLM incrementally maintains a persistent wiki synthesized from source documents.
