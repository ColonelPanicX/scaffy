# scaffy

scaffy builds one self-contained `.collab/` directory in your project where you, your AI agents
(Claude Code, Codex CLI, Gemini CLI) and your working sessions hand off work without losing
context. One script, standard library only, no dependencies.

> **Coming from scaffy 1.x? Read this first.** v2.0.0 reorganizes `.collab/`. Your existing projects keep working,
> but run these in each one to move to the new layout and pick up the new protocols:
>
> ```bash
> scaffy --upgrade --dry-run --path /path/to/project   # 1. preview the moves
> scaffy --upgrade --path /path/to/project             # 2. move folders, add new files
> scaffy --upgrade --force --path /path/to/project     # 3. refresh the contract and playbooks
> ```
>
> Then **re-copy the scaffy skill** for your agent (see [Agent skills](#agent-skills)).
>
> - Step 2 moves files and never overwrites. If a file exists in both the old and new place, it's
>   left alone and reported so you can merge it by hand.
> - Step 3 is what brings in the North Star, Inbox and Agent Bridge rules. It replaces
>   `collab-contract.md`, `.collab/readme.md` and the playbooks, saving the old copies to
>   `.collab/.upgrade-backups/<timestamp>/` first. If you customized your contract, merge your
>   changes back from the backup.
> - Your kanban, context, North Star, project.yaml, initial prompt and LICENSE are never replaced.
> - On Windows, the GUI does the same: pick **Upgrade scaffold**, run it, then run it again with
>   **Force overwrite** checked.
>
> | 1.x | 2.0.0 |
> |---|---|
> | `supporting-artifacts/` | `inbox/` |
> | `guides/git-guidelines.md` | `playbooks/git-guidelines.md` |
> | templates in `playbooks/templates/`, `brainstorms/`, `project-plans/`, `session-summaries/` | `templates/` |
> | all three `git-governance-*.md` playbooks | only the one for your governance mode |
> | skills in this repo only | also in `.collab/skills/<agent>/scaffy/` |

---

## Install

```bash
pipx install scaffy-collab
scaffy --help
```

Requires Python 3.10+ and [pipx](https://pipx.pypa.io). To upgrade scaffy itself later:
`pipx upgrade scaffy-collab`.

No install option: download `scaffy.py` from the
[latest release](https://github.com/ColonelPanicX/scaffy/releases/latest) and run
`python3 scaffy.py`.

**Windows:** download `scaffy.exe` from the same release page. No Python needed.

---

## Quickstart

### CLI (Mac / Linux / Windows)

```bash
scaffy
```

The wizard asks whether this is a new project, an existing one, or an upgrade, then walks through
the options. Type `b` at any prompt to go back or `q` to quit. To skip the prompts:

```bash
scaffy --name my-project --path ~/code --governance standard --platform github
```

When it finishes, scaffy prints a first-session prompt. Paste it into your agent. (It's also saved
to `.collab/prompts/initial-prompt.md`.)

### Windows GUI

1. Run `scaffy.exe`
2. Fill in **Project Name** and **Target Path**, adjust the options, click **Build!**
3. Copy the first-session prompt from the popup into your agent

<img width="642" height="750" alt="scaffy GUI" src="https://github.com/user-attachments/assets/ebaf4f61-7a5d-45de-8e01-378a531e9da3" />

---

## What you get

```
.collab/
  collab-contract.md     rules your agent follows, including the session protocols
  kanban-board.md        the task board (source of truth for what's happening)
  context.md             stable project facts: stack, key files, commands, conventions
  north-star.md          where the project is headed, and what it won't do
  project.yaml           machine-readable settings (used by --upgrade)
  readme.md              a map of this directory
  prompts/               first-session prompt, agent profile, agent-instructions generator
  session-summaries/     one summary per session, written by the agent
  chat-logs/             full transcripts exported with SAVE CHAT
  brainstorms/           ideas that aren't tickets yet, and brainstorm session records
  project-plans/         long-form plans and multi-phase roadmaps
  inbox/                 drop zone for files you haven't sorted yet
  agent-bridge/          shared channels between agents of different types
  audit/                 reports, reviews and decision records
  playbooks/             how-tos: coding, git guidelines, your governance mode, agent bridges
  templates/             starting points for summaries, brainstorms, plans, issues, PRs
  skills/                the scaffy skill for Claude, Codex and Gemini
```

At the project root: a `.gitignore` (excludes `.collab/` and agent folders), an optional `LICENSE`,
and optional issue and PR templates for GitHub, GitLab or Azure DevOps.

`.collab/` is gitignored on purpose. Summaries, the board and half-formed ideas are working
material, not repo history.

---

## Working with your agent

### Session protocols

The contract defines trigger phrases. Type one and the agent runs a fixed procedure:

| Phrase | What happens |
|---|---|
| `OPEN SESSION` | Reads the latest summaries, the board, context and the North Star, then tells you what was done, what's in progress or blocked, and what's next. Flags work drifting from the North Star and items waiting in the inbox. |
| `SAVE SESSION` | Mid-session checkpoint: writes a summary, updates the board, and gives you a **re-entry prompt** to paste into a fresh chat. Then keeps working. |
| `CLOSE SESSION` | Writes the session summary and updates the board. |
| `SAVE CHAT` | Exports the full transcript to `.collab/chat-logs/`. |

`SAVE CHAT` works for Claude Code, Codex CLI and Gemini CLI. scaffy detects the agent when run from
inside a session; from a plain terminal, pass `--cli claude|codex|gemini`.

### Agent skills

scaffy ships a skill for each agent CLI so the agent knows how to run scaffy and every protocol
without you explaining it. Every scaffold includes them in `.collab/skills/<agent>/scaffy/SKILL.md`;
the same files are in this repo's [`skills/`](skills/) folder if you want to install before
scaffolding anything.

scaffy doesn't install skills for you. Copy the one for your CLI:

```bash
# from a scaffolded project (or use skills/... from a clone of this repo)
mkdir -p ~/.claude/skills && cp -r .collab/skills/claude/scaffy ~/.claude/skills/   # Claude Code
mkdir -p ~/.gemini/skills && cp -r .collab/skills/gemini/scaffy ~/.gemini/skills/   # Gemini CLI
mkdir -p ~/.codex/skills  && cp -r .collab/skills/codex/scaffy  ~/.codex/skills/    # Codex CLI
```

After upgrading scaffy, run `scaffy --upgrade --force` and copy the skill again.

In Claude Code and Gemini CLI the skill is `/scaffy`. Codex has no slash command: it picks the
skill up when you ask for one of these in plain words.

```
/scaffy                              scaffold a new project (asks for name, path, options)
/scaffy initialize                   first session: read the workspace, scan the repo, seed the board
/scaffy open session                 resume
/scaffy save session                 checkpoint with a re-entry prompt
/scaffy close session                summary and board update
/scaffy save chat                    export the transcript
/scaffy north star                   draft the North Star (interview) or review it
/scaffy brainstorm                   list brainstorms
/scaffy brainstorm <title>           create or resume one and workshop it
/scaffy brainstorm session <topic>   run a facilitated brainstorm session
/scaffy project plan                 list project plans
/scaffy project plan <title>         create or resume one and workshop it
/scaffy bridge                       list agent bridges and who holds the ball
/scaffy bridge open <name>           open a bridge to an agent of a different type
/scaffy bridge check [name]          read the bridge and reply if needed
/scaffy bridge close [name]          close it (initiator) or acknowledge (responder)
```

The plain trigger phrases (`OPEN SESSION` and so on) still work without the skill.

### First session

With the skill installed, run `/scaffy initialize`. Without it, paste the prompt scaffy printed.
Either way the agent reads the workspace and, in an existing repo, does a read-only scan and
reports what it found. Then run `/scaffy north star` to fill in the North Star.

---

## North Star

`.collab/north-star.md` is one page on where the project is headed: the problem, who it's for,
what success looks like, non-goals, guiding principles, and the signs that work is drifting,
ending in a one-sentence North Star. Every scaffold ships it as a `draft`.

`/scaffy north star` interviews you for it. The agent shows the agenda first (six topics plus the
sentence, about 10 to 15 minutes), asks one topic at a time, and writes each answer into the file
as you go. Once you mark it `agreed`:

- `OPEN SESSION` reads it and points out board items that pull away from it
- agents check plans, brainstorms and priorities against it, and say so when work conflicts
- it changes only with your explicit approval, each change logged with a date
- `scaffy --upgrade` never overwrites it

---

## Brainstorms

`.collab/brainstorms/` holds ideas that aren't ready to be tickets. Nothing in it has to go
anywhere, and the agent never turns one into a task without your approval.

- **One idea:** `/scaffy brainstorm <title>` creates a file from the template and workshops it
  with you. Status moves `drafting` → `workshopping` → `parked` or `graduated`.
- **An open question with many answers:** `/scaffy brainstorm session <topic>` runs a facilitated
  session in five phases, saving after each one so you can resume:
  1. **Frame:** the question, constraints, and what a good outcome looks like (checked against
     the North Star)
  2. **Diverge:** you go first, then the agent adds ideas from new angles; nothing is judged yet
  3. **Cluster:** group ideas into themes
  4. **Converge:** rate the strongest against agreed criteria; you pick the shortlist
  5. **Close:** open questions and proposed next steps

  The record is `.collab/brainstorms/<topic>-session-MM.DD.YYYY.md`.

## Project plans

`.collab/project-plans/` is for work too big for the board alone: a redesign, a migration, a
multi-phase feature. `/scaffy project plan <title>` creates a plan from the template and works
through goals, phases, tasks and risks with you. Status: `draft` → `active` → `complete` or
`archived`.

## Inbox

`.collab/inbox/` is a drop zone. Put anything that might be useful there (notes, exports,
screenshots, specs) before you know where it belongs, then ask your agent to go through it with
you. The agent proposes what to do with each item and moves or deletes nothing without your
approval. `OPEN SESSION` mentions how many items are waiting but doesn't sort them on its own.

## Agent bridge

When a project uses agents of **different types** (say Claude and Codex), they can't message each
other. A bridge gives them a shared channel in `.collab/agent-bridge/<name>/`, so they coordinate
on one problem while you watch instead of relaying every message. Agents of the same type should
use their CLI's own messaging instead.

1. In one agent, `/scaffy bridge open <name>`. It becomes the **initiator**: it agrees the two
   roles and the scope with you, writes `README.md`, the first message in `transcript.md`, and
   `status.md`, and gives you the full path.
2. In the other agent, hand it that path and run `/scaffy bridge check`. It becomes the
   **responder** and replies.
3. Either side runs `/scaffy bridge check` to pick up new messages.
4. The initiator runs `/scaffy bridge close` with a summary; the responder acknowledges.

Transcripts are append-only with UTC timestamps, and closed bridges are kept as a record. Agents
never commit, push or change code because of a bridge message without your approval. The full
procedure is in `.collab/playbooks/agent-bridge-playbook.md`.

---

## Governance modes

| Mode | Use when |
|---|---|
| `none` | You want the workspace without any process rules |
| `lightweight` | Prototypes, solo work, fast iteration |
| `standard` | Most active projects (the default) |
| `strict` | Compliance, regulated or high-risk work |

The mode shapes the contract and decides which git playbook ships:
`.collab/playbooks/git-governance-<mode>.md` covers starting work, commits, PRs, merging and
hotfixes for that mode (`none` gets no playbook). `.collab/playbooks/git-guidelines.md` explains
the reasoning behind all of them. To change mode, edit `governance_mode` in `project.yaml` and run
`scaffy --upgrade --force`.

Other things in the scaffold worth knowing about:

- **Agent instructions generator:** fill in `.collab/prompts/agent-profile.md`, then paste
  `.collab/prompts/agent-md-prompt.md` into your agent. It writes a tailored `AGENTS.md`,
  `CLAUDE.md` or equivalent for your project root.
- **Coding playbook:** `.collab/playbooks/coding-playbook.md` is a general best-practices
  reference. Trim it to what matters for your project.

---

## Upgrading

When a new scaffy version comes out, upgrade the tool and then each project:

```bash
pipx upgrade scaffy-collab
scaffy --upgrade --dry-run --path ~/code/my-project   # preview
scaffy --upgrade --path ~/code/my-project             # add new files and folders, move old ones
scaffy --upgrade --force --path ~/code/my-project     # also refresh scaffy-managed files
```

Plain `--upgrade` adds what's missing and never changes an existing file. `--force` also replaces
scaffy-managed files (contract, `.collab/readme.md`, playbooks, templates, skills) and backs up
each one to `.collab/.upgrade-backups/<timestamp>/`. Your kanban, context, North Star,
project.yaml, initial prompt and LICENSE are never replaced. Upgrade reads your original settings
from `.collab/project.yaml`, so don't delete it.

---

## Flags

| Flag | Description | Default |
|---|---|---|
| `--name NAME` | Project name | interactive |
| `--path PATH` | Parent folder for a new project; project root for an existing one or an upgrade | interactive |
| `--governance MODE` | `none`, `lightweight`, `standard` or `strict` | interactive (`standard`) |
| `--platform PLATFORM` | `github`, `gitlab`, `azure-devops` or `none`: writes issue and PR/MR templates | interactive (`none`) |
| `--license LICENSE` | `mit`, `apache-2.0`, `gpl-3.0`, `agpl-3.0`, `bsd-2-clause`, `bsd-3-clause`, `mpl-2.0`, `unlicense` or `none` | interactive (`none`) |
| `--description TEXT` | Short description saved to `context.md` and `project.yaml` | interactive (optional) |
| `--ticket-prefix PREFIX` | Task ID prefix on the board, e.g. `SCAF` | `TASK` |
| `--init-git` | Run `git init` after scaffolding | off |
| `--dry-run` | Show what would happen without writing | off |
| `--force` | Overwrite existing files. With `--upgrade`: refresh scaffy-managed files, with backups | off |
| `--upgrade` | Bring an existing `.collab/` up to the current version | off |
| `--save-chat` | Export an agent session to `.collab/chat-logs/` | off |
| `--list-chats` | List recent agent sessions | off |
| `--session-id UUID` | Session UUID prefix to export with `--save-chat` | most recent |
| `--cli CLI` | `claude`, `codex` or `gemini` for `--save-chat` / `--list-chats` | auto-detect |

If `--name` and `--path` are both given, scaffy runs without prompts. An existing `.gitignore` is
never overwritten; scaffy writes its version to `.collab/.gitignore.template` for you to merge.
Dates use `MM.DD.YYYY` in `America/New_York`.

More detail on every flag, mode and file is in the [wiki](https://github.com/ColonelPanicX/scaffy/wiki).

---

## scafrag (optional)

`scafrag.py` indexes the `.collab/` workspaces across all your projects so you can search past
decisions, check status across projects, or dump one project's full context. Nothing in scaffy
needs it.

```bash
python3 scafrag.py index --root ~/code               # build the index
python3 scafrag.py query "authentication middleware" # search everything
python3 scafrag.py context my-project                # one project's full context
python3 scafrag.py status                            # every project with board counts
python3 scafrag.py projects                          # list indexed projects
```

Every command takes `--format text|json|markdown` and writes to stdout, so you can pipe it straight
into an agent. Python 3.10+, no dependencies. Windows: `scafrag.exe` is on the release page.

---

## Tests

Standard library only. The tests run scaffy and scafrag as real subprocesses in temp folders:

```bash
python3 -m unittest discover -s tests -t .
```

CI runs them on every push and PR to `dev` and `main` (Python 3.10–3.13 on Linux, plus Windows).

## See also

Tools that pair well with scaffy. None are required.

- **[GSD](https://github.com/gsd-build/gsd-2):** spec-driven system for autonomous multi-phase agent work (research, planning, execution, git) in one pipeline.
- **[MemPalace](https://github.com/MemPalace/mempalace/tree/main):** local-first AI memory with semantic search; adds queryable long-term recall alongside session summaries.
- **[Caveman](https://github.com/JuliusBrussee/caveman):** Claude Code skill that compresses agent output with terse, technical language. Pairs well with agent bridges.
- **[Karpathy's LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f):** pattern for a personal knowledge base an LLM maintains from your source documents.
