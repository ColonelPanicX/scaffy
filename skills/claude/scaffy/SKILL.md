---
name: scaffy
description: Bootstrap a .collab/ multi-agent workspace, or run session protocols (initialize/open/save/close/save-chat/north-star/brainstorm/brainstorm-session/project-plan) for an existing scaffy project.
---

scaffy skill — bootstrap a `.collab/` workspace, or run session protocols for an existing one.

## Dispatch on $ARGUMENTS

Read $ARGUMENTS first and route accordingly:

- `initialize` → **Initialize Protocol** (see below)
- `open session` → **Session Open Protocol** (see below)
- `save session` → **Session Save Protocol** (see below)
- `close session` → **Session Close Protocol** (see below)
- `save chat` → **Chat Save Protocol** (see below)
- `north star` → **North Star Protocol** (see below)
- `brainstorm session` or `brainstorm session <topic>` → **Brainstorm Session Protocol** (see below; match this before `brainstorm <title>`)
- `brainstorm` or `brainstorm <title>` → **Brainstorm Protocol** (see below)
- `project plan` or `project plan <title>` → **Project Plan Protocol** (see below)
- anything else (project name, path, flags, or empty) → **Scaffold a new project** (see below)

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

1. Find and read the most recent 1–2 session summaries in `.collab/session-summaries/` (skip `session-summary-template.md`). Filenames start with `MM.DD.YYYY`, so don't sort them alphabetically (`01.05.2027` would come before `11.08.2026`). Order by year, then month, then day, then the same-day number (no number first, then `-02`, `-03`), newest first.
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md` if it exists.
4. Read `.collab/north-star.md` if its status is `agreed` (skip it while still `draft`).
5. Deliver a concise session resume covering:
   - What was accomplished last session
   - What is currently In Progress or Blocked on the board
   - What is up next
   - Any open questions or flags left from the last session
   - Any work on the board that seems to pull away from the North Star

Do not re-read `collab-contract.md` — focus on current state, not process rules.

---

## Session Save Protocol

Execute immediately — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` (always a new file — never overwrite):
   - First summary that day: `MM.DD.YYYY-claude-summary.md`
   - Additional same-day saves: `MM.DD.YYYY-02-claude-summary.md`, `MM.DD.YYYY-03-claude-summary.md`, etc.
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

1. Run from the project root: `scaffy --save-chat`
2. The tool saves the transcript to `.collab/chat-logs/` automatically.
3. Confirm the filename and path to the user.

---

## North Star Protocol

Execute immediately — do not wait for additional instructions.

`.collab/north-star.md` is the project's stable statement of direction: where it is headed, for whom, what success looks like, what it will not do, and how to make trade-offs. It changes rarely and only with the user's approval.

### Find the file

1. Look for `.collab/north-star.md`.
   - **Missing** (older scaffold): tell the user `scaffy --upgrade` adds it, or create it now with the section headings listed below. Then go to **Draft**.
   - **`_Status: draft_`** or the sections are still placeholder comments → **Draft**.
   - **`_Status: agreed_`** → **Review**.

### Draft (interview)

1. Read `.collab/context.md`, the kanban board, and any project plans first, so your questions build on what is already known.
2. **Show the agenda before the first question**, so the user knows what's coming: the six topics below, then the North Star sentence, about 10–15 minutes in all. Mention that they can give the sentence now if they already have it.
3. Interview the user **one topic at a time**, in this order. Offer a suggested answer from what you've read when you can, and keep each answer short:
   1. **Problem** — what is wrong or missing today, and for whom?
   2. **Who It's For** — primary users or beneficiaries.
   3. **What Success Looks Like** — observable outcomes, not features.
   4. **Non-Goals** — what this project deliberately will not do.
   5. **Guiding Principles** — 3–5 rules for trade-offs.
   6. **Off-Course Signals** — signs that work is drifting.
4. Write each answer into the file as you go, so nothing is lost if the session ends. When you fill a section, replace its `<!-- ... -->` placeholder comment with the answer.
5. Settle the one-sentence **North Star** last, from the answers. If the user gave one early, save it as a working draft right away and check it against the answers here; otherwise offer 2–3 options.
6. Read the whole document back. Push back on vague success criteria ("users love it") and on non-goals that contradict the rest.
7. When the user agrees: set `_Status: agreed_`, set `_Last revised:_` to today, remove the "Fill this in" comment under the header, and add a Revision Log row (`Agreed`, approved by the user).

### Review (already agreed)

1. Show a short summary of the current North Star and the date it was last revised.
2. Ask what prompted the review. If the user wants changes, draft the exact edits and show them **before** writing.
3. Write only what the user approves. Add a dated Revision Log row describing the change, and update `_Last revised:_`.
4. If nothing changes, say so and leave the file untouched.

### Rules

- Never edit `north-star.md` without the user's explicit approval of the exact change.
- Keep it to one page. Detail belongs in `context.md` or a project plan.
- Do not create tasks or kanban entries from it without approval.

---

## Brainstorm Session Protocol

Execute immediately — do not wait for additional instructions.

A facilitated session on one question that ends in a written brainstorm document. You are the facilitator: keep the session moving, add ideas of your own, and write everything down. The user decides.

### Setup

1. If no topic was given, ask for one in a single line.
2. Filename: topic in lowercase, hyphen-separated, plus `-session-MM.DD.YYYY.md` (e.g. `brainstorm session onboarding flow` → `onboarding-flow-session-11.05.2026.md`) in `.collab/brainstorms/`.
   - **Exists**: read it and resume at the first phase that is still empty.
   - **Does not exist**: create it from `.collab/brainstorms/brainstorm-session-template.md` (if the template is missing, use the section headings below). Fill in the title and today's date, set `_Status: in-session_`, and list participants (the user and you, by agent name).
3. Ask how deep to go: **quick** (~15 min, ~10 ideas), **standard** (~30 min, ~20 ideas), or **deep** (no cap). Default: standard.

### Phase 1 — Frame

1. Read `.collab/north-star.md` if it is `agreed`, and skim `context.md` for constraints.
2. Agree with the user on: the **question** (one sentence), **why now**, **constraints**, and **what a good outcome looks like**. Suggest a sharper wording if the question is vague or is really several questions.
3. Write **Framing**, including a **North Star check** (or `n/a`). Confirm it with the user before moving on.

### Phase 2 — Diverge

1. Rules, stated once: no judging yet, quantity over quality, build on each other's ideas, wild ideas welcome.
2. The user goes first. Then add your own ideas, a few at a time, from angles the user hasn't covered:
   - Who else is affected (users, maintainers, newcomers, admins)?
   - Invert it: how would we make this worse? Then flip each answer.
   - Drop a constraint: what if time, money, or compatibility didn't matter?
   - The smallest version that would still help.
   - What could go wrong, and what would prevent it?
   - What does it look like at 10x the scale?
3. Don't evaluate during this phase, including your own ideas. Don't let your ideas outnumber the user's by much; the point is to draw theirs out.
4. Append ideas to **Ideas** after each round, numbered, with the source `(user)` or `(agent)`.
5. Stop when the depth target is reached or the user says so.

### Phase 3 — Cluster

1. Propose 3–6 themes with the idea numbers in each. Name any idea that fits nowhere.
2. Let the user merge, split, or rename them. Write **Clusters**.

### Phase 4 — Converge

1. Agree on criteria. Default: fits the question, effort, risk, North Star fit (H/M/L each).
2. Rate the strongest ideas or clusters in **Evaluation**. Be honest: name weak spots and risks, and push back if a favorite doesn't hold up.
3. The user picks the **Shortlist** (usually 1–3). Record why.
4. Everything else worth noting goes to **Parked / Rejected**, each with a one-line reason.

### Phase 5 — Close

1. Fill in **Open Questions** and **Proposed Next Steps** (clearly marked as proposals).
2. Set `_Status: complete_`.
3. Give the user a short summary: the question, the shortlist, and the proposed next steps.
4. Offer, without doing it unasked: spin shortlisted ideas into their own brainstorm files (**Brainstorm Protocol**) or a project plan (**Project Plan Protocol**). List any you create under **Spin-offs**.

### Rules

- Write the file at the end of every phase, so an interrupted session can be resumed.
- Do **not** create tickets, tasks, or kanban entries without explicit user approval.
- Keep the session conversational: one question or one batch of ideas per turn.

---

## Brainstorm Protocol

Execute immediately — do not wait for additional instructions.

### With no arguments (`brainstorm`)

List all brainstorm files with their statuses:

1. Scan `.collab/brainstorms/` for all `.md` files (exclude `brainstorm-template.md` and `brainstorm-session-template.md`). Session files (`*-session-MM.DD.YYYY.md`) show status `in-session` or `complete`.
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
   - If not found, tell the user to install: `pip install scaffy` or download from https://github.com/ColonelPanicX/scaffy/releases/latest

2. **Gather inputs** — extract from $ARGUMENTS if present, otherwise ask:
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

Diffs the existing `.collab/` against current templates and adds any missing files or directories. Does not overwrite existing files unless `--force` is added; with `--force`, replaced files are backed up to `.collab/.upgrade-backups/`, and project state (kanban, context, north-star, project.yaml, initial-prompt, LICENSE) is never replaced.

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
