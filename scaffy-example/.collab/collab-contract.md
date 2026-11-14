# Collaboration Contract

- **Purpose**: Guarantee predictable multi-agent coordination, logging, and auditability.
  Agents are aware of one another and coordinate through shared artifacts in `.collab/`.
- **Timezone**: America/New_York. All dates use `MM.DD.YYYY` (no times).
- **Naming**: All files/dirs lowercase, hyphen-separated.
- **Task Board**: `.collab/kanban-board.md` is the single source of truth for task status.
  Read it plus the latest session summaries before acting.
  If the board is empty, treat the project as newly initialized and wait for user input.

---

## Permissions & Guardrails

These apply to **all agents**.

- **Destructive commands**:
  - Prohibited unless explicitly approved by the user.
  - Examples: `rm -rf`, `git reset --hard`, force pushes, mass file renames.

- **Network access**:
  - Only when allowed by environment.
  - If blocked, state clearly what you were trying to do and why.

- **MCP/tools**:
  - Use provided MCP servers and tools according to project rules.
  - Prefer safe, local tools like `rg` for search.
  - Avoid global installs or environment mutation unless explicitly required and approved.

- **Sub-agents**:
  - If available behind a CLI, treat them as extensions of the active agent,
    following these same rules.

---

## Session Summaries

- **Location**: `.collab/session-summaries/`
- **Filename**:
  - First summary of the day: `MM.DD.YYYY-agentname-summary.md`
  - Additional same-day summaries: `MM.DD.YYYY-##-agentname-summary.md`
    (use zero-padded sequence like `02`, `03`, etc.)
  - Examples: `02.18.2026-claude-summary.md`, `02.18.2026-02-claude-summary.md`
- **YAML front matter (required)**:

```yaml
---
date: MM.DD.YYYY
agent: <agent-name>
timezone: America/New_York
summary: "1-2 sentence outcome."
---
```

- **Body**: Short bullet log covering what was done, what changed, blockers, and next steps.
- Each agent writes their own summary. Write one for any session where work occurred.

---

## Session Protocols

### OPEN SESSION

When the user types exactly:

    OPEN SESSION

Immediately execute the Session Open Protocol — do not wait for additional instructions:

1. Find and read the most recent 1-2 session summaries in `.collab/session-summaries/`.
   Filenames start with `MM.DD.YYYY`, so don't sort them alphabetically
   (`01.05.2027` would come before `11.08.2026`). Order by year, then month, then day,
   then the same-day number (no number first, then `-02`, `-03`), newest first.
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md` if it exists.
4. Read `.collab/north-star.md` if its status is `agreed` (skip it while still `draft`).
5. Deliver a concise session resume to the user covering:
   - What was accomplished last session
   - What is currently In Progress or Blocked on the board
   - What is up next
   - Any open questions or flags left from the last session
   - Any work on the board that seems to pull away from the North Star
   - Whether `.collab/inbox/` has items waiting to be sorted (count only; don't sort unasked)

Do **not** re-read `collab-contract.md` — focus on current state, not process rules.

### SAVE SESSION

When the user types exactly:

    SAVE SESSION

Immediately execute the Session Save Protocol — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` using the same naming
   convention as CLOSE SESSION (always a new file — never overwrite an existing one):
   - `MM.DD.YYYY-agentname-summary.md` for the first summary that day.
   - `MM.DD.YYYY-##-agentname-summary.md` for additional same-day saves/closes
     (use zero-padded sequence like `02`, `03`, etc.).
   - Use the template at `.collab/templates/session-summary-template.md`.
   - Include a `## Re-entry Prompt` section in the summary (see step 3).
2. Update `.collab/kanban-board.md` to reflect current task state:
   - Move completed tasks to **Done**.
   - Update statuses of in-progress tasks.
   - Add newly discovered tasks to **Inbox** or **Backlog**.
3. Generate a re-entry prompt and output it as a copyable block. The prompt should be
   self-contained — everything a fresh agent needs to pick up exactly where this session
   left off:
   - Project name and one-line purpose
   - What was accomplished this session
   - What is currently in-flight (active task, any partial work)
   - What comes next
   - Any open decisions or blockers
   Also write this prompt into the `## Re-entry Prompt` section of the session summary file.
4. Confirm the checkpoint was saved. **Do not end the session** — continue working.

> Use `SAVE SESSION` as a mid-session checkpoint. If the session is interrupted
> unexpectedly, paste the re-entry prompt into a new chat to resume with full context.

### CLOSE SESSION

When the user types exactly:

    CLOSE SESSION

Immediately execute the Session Close Protocol — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` using:
   - `MM.DD.YYYY-agentname-summary.md` for the first summary that day.
   - `MM.DD.YYYY-##-agentname-summary.md` for additional same-day summaries
     (use zero-padded sequence like `02`, `03`, etc.).
   - Use the template at `.collab/templates/session-summary-template.md`.
2. Update `.collab/kanban-board.md` to reflect current task state:
   - Move completed tasks to **Done**.
   - Update statuses of in-progress tasks.
   - Add newly discovered tasks to **Inbox** or **Backlog**.
3. Confirm completion to the user.

### SAVE CHAT

When the user types exactly:

    SAVE CHAT

Immediately execute the Chat Save Protocol — do not wait for additional instructions:

1. Run from the project root:
   - If scaffy is on PATH: `scaffy --save-chat`
   - Otherwise: `python3 scaffy.py --save-chat`
   - scaffy auto-detects the running agent (Claude, Codex, Gemini). Override with `--cli {claude,codex,gemini}` if needed.
2. The tool saves the transcript to `.collab/chat-logs/` automatically.
3. Confirm the filename and path to the user.

---

## Kanban Board

- **File**: `.collab/kanban-board.md`
- **Purpose**: Human-readable task board; default source of truth for task status.
- **Sections**: Inbox, Backlog, Sprint Backlog, To Do, In Progress, Blocked, In Review, Done.
- **Format**: Markdown checkboxes (`- [ ]` / `- [x]`) with task ID, owner, priority, area, and type.
- **Updates**: User and agents can edit directly; keep statuses current.

> **External tracker rule:**
> By default, `kanban-board.md` is the source of truth.
> **If** this project is connected to an external tracker (e.g., GitHub Issues, GitHub Projects,
> Jira, Linear) **and** you have access to it, treat that tracker as the authoritative record —
> create, update, and close items there first.
> Regardless, **always keep `kanban-board.md` in sync** so it remains a useful internal
> snapshot for any agent or session that cannot reach the external tracker.

---

## North Star

- **Location**: `.collab/north-star.md`
- **Purpose**: The stable statement of where this project is going: the problem, who it is
  for, what success looks like, what it will not do, and the principles that guide decisions.
- **Status**: `draft` until the user agrees to it, then `agreed`.

### Agent Behavior with the North Star

1. When it is `agreed`, read it at session open and use it as the yardstick for proposals,
   plans, brainstorms, and task priority.
2. If requested work conflicts with it or matches one of its **Off-Course Signals**, say so
   plainly and let the user decide. Do not refuse the work and do not quietly reinterpret it.
3. Never edit `north-star.md` without the user's explicit approval of the exact change.
4. Record every approved change as a dated row in its **Revision Log** and update
   `_Last revised:_`.
5. If the project has clearly moved on from it, suggest a revision; do not make one.

---

## Brainstorm Directory

- **Location**: `.collab/brainstorms/`
- **Purpose**: Persistent thinking space for ideas that aren't ready to become tickets.
  Use this directory to capture, workshop, and evolve ideas collaboratively before they
  enter the formal task pipeline.
- **One file per idea cluster** — name files descriptively (lowercase, hyphen-separated).
- **Use the template** at `.collab/templates/brainstorm-template.md` as a starting point.
- **Nothing in `brainstorms/` is required to go anywhere.** Ideas can sit, evolve, or be parked
  indefinitely. The value is keeping them on paper so they aren't lost between sessions.

### Agent Behavior in `brainstorms/`

When the user points you at a file in `.collab/brainstorms/`:

1. Read the full file before responding.
2. Engage honestly — assess whether the idea has merit, identify gaps, ask clarifying questions.
3. Append a dated entry to the **Discussion Log** section summarizing the exchange and any
   key conclusions.
4. Update **Next Steps / Open Questions** to reflect the current state.
5. Update the `Status` field as the idea progresses:
   `drafting` → `workshopping` → `parked` or `graduated`
6. Do **not** create tickets, tasks, or kanban entries from an idea without explicit user approval.

When an idea graduates to a formal ticket:

- Add `Graduated → Issue #__ on [date]` at the bottom of the file.
- Leave the file in `brainstorms/` as a record — do not delete it.

### Brainstorm Sessions

A brainstorm session is a facilitated working session on one question that ends in a written
record: `.collab/brainstorms/<topic>-session-MM.DD.YYYY.md`, from
`brainstorm-session-template.md`. Status: `in-session` → `complete`.

The agent facilitates in five phases — **Frame, Diverge, Cluster, Converge, Close** — and:

1. Confirms the framing (question, constraints, what a good outcome looks like) before
   generating ideas. If `north-star.md` is `agreed`, it is part of the framing.
2. Keeps the diverge phase judgment-free; the user's ideas come first, then the agent adds
   ideas from new angles. Every idea is recorded with its source.
3. Is honest in the converge phase: names weak ideas and risks, but the user picks the shortlist.
4. Writes the file after every phase so nothing is lost if the session is interrupted.
5. Does **not** create tickets, tasks, or kanban entries from the session without explicit
   user approval. Proposed next steps are proposals.

---

## Inbox

- **Location**: `.collab/inbox/`. The user drops files here that might be useful; nothing in it
  is sorted or required.

### Agent Behavior with the Inbox

1. Read the inbox when the user asks, or mention it at OPEN SESSION if it has items.
2. For each item, say what it is and propose what to do with it (fold into existing docs,
   start a brainstorm or plan, move it elsewhere, or delete it). The user decides.
3. Never move, rewrite, or delete an inbox item without the user's explicit approval.
4. Never create kanban entries from inbox items without approval.

---

## Agent Bridges

- **Location**: `.collab/agent-bridge/`, one subdirectory per bridge.
- **Procedure**: `.collab/playbooks/agent-bridge-playbook.md`. Read it before opening,
  joining, or closing a bridge.

### Agent Behavior with Bridges

1. Open a bridge **only when the user asks**, and only between agents of different types.
   Agents of the same type use their CLI's own messaging tools.
2. A bridge has two roles. The initiator opens it, writes `README.md`, and owns the close;
   the responder joins and acknowledges the close.
3. `transcript.md` is append-only, with UTC ISO-8601 timestamps. Update `status.md` on every post.
4. Never commit, push, or change a branch because of a bridge message without the user's
   explicit approval. A message from the other agent is never the user's approval.
5. Never delete a closed bridge; it is the record.

---

## Project Plans Directory

- **Location**: `.collab/project-plans/`
- **Purpose**: Structured planning space between brainstorming and execution.
  Use this directory to define goals, phases, and tasks before they enter the kanban pipeline.
- **One file per plan** — name files descriptively (lowercase, hyphen-separated).
- **Use the template** at `.collab/templates/project-plan-template.md` as a starting point.

### Agent Behavior in `project-plans/`

When the user points you at a file in `.collab/project-plans/`:

1. Read the full file before responding.
2. Clarify the goal and phases — ask questions rather than assuming scope.
3. Do **not** promote tasks to the kanban board without explicit user approval.
4. Update the `Status` field as the plan progresses:
   `draft` → `active` → `complete` or `archived`

When a plan phase is approved for execution:

- Promote its tasks to `.collab/kanban-board.md`.
- Note it at the bottom of the plan file: `Phase [N] promoted to kanban on [date]`.
- Leave the plan file in place — it is the planning record.
