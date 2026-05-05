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

1. Find and read the most recent 1-2 session summaries in `.collab/session-summaries/`
   (sort by filename date, newest first).
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md` if it exists.
4. Deliver a concise session resume to the user covering:
   - What was accomplished last session
   - What is currently In Progress or Blocked on the board
   - What is up next
   - Any open questions or flags left from the last session

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
   - Use the template at `.collab/session-summaries/session-summary-template.md`.
2. Update `.collab/kanban-board.md` to reflect current task state:
   - Move completed tasks to **Done**.
   - Update statuses of in-progress tasks.
   - Add newly discovered tasks to **Inbox** or **Backlog**.
3. Confirm the checkpoint was saved. **Do not end the session** — continue working.

> Use `SAVE SESSION` as a mid-session checkpoint. If the session is interrupted
> unexpectedly, the last save can be used to reconstruct context on next `OPEN SESSION`.

### CLOSE SESSION

When the user types exactly:

    CLOSE SESSION

Immediately execute the Session Close Protocol — do not wait for additional instructions:

1. Write a session summary to `.collab/session-summaries/` using:
   - `MM.DD.YYYY-agentname-summary.md` for the first summary that day.
   - `MM.DD.YYYY-##-agentname-summary.md` for additional same-day summaries
     (use zero-padded sequence like `02`, `03`, etc.).
   - Use the template at `.collab/session-summaries/session-summary-template.md`.
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

## Brainstorm Directory

- **Location**: `.collab/brainstorm/`
- **Purpose**: Persistent thinking space for ideas that aren't ready to become tickets.
  Use this directory to capture, workshop, and evolve ideas collaboratively before they
  enter the formal task pipeline.
- **One file per idea cluster** — name files descriptively (lowercase, hyphen-separated).
- **Use the template** at `.collab/brainstorm/brainstorm-template.md` as a starting point.
- **Nothing in `brainstorm/` is required to go anywhere.** Ideas can sit, evolve, or be parked
  indefinitely. The value is keeping them on paper so they aren't lost between sessions.

### Agent Behavior in `brainstorm/`

When the user points you at a file in `.collab/brainstorm/`:

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
- Leave the file in `brainstorm/` as a record — do not delete it.
