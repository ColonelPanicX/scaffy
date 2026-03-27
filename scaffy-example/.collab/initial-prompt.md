You are working in a newly initialized project with a structured `.collab/` collaboration
directory. Before doing anything:

1. Read `.collab/collab-contract.md` for rules, naming conventions, and logging requirements.
2. Read `.collab/kanban-board.md` for current task status.
3. Read `.collab/context.md` for stable project facts (fill in what you can from context).
4. Check `.collab/session-summaries/` for any prior session summaries.
5. The kanban board is empty — this is a newly initialized project. Wait for me to
   describe goals before drafting plans or tasks.

---

Now initialize your memory with these stable facts (use whatever persistent memory
mechanism your agent supports):
- Project name and one-sentence description
- Tech stack: languages, frameworks, key dependencies
- Key file paths: entry points, config files, test directories
- Naming and style conventions
- Hard constraints or guardrails (e.g., "never commit credentials")

Report back:
- What you saved to memory
- Which fields in `context.md` are empty and should be filled in before work begins

Do not start any work tasks until these steps are complete.

---

## Session Protocols

### OPEN SESSION

When I type exactly:

    OPEN SESSION

Immediately execute the Session Open Protocol:

1. Read the most recent 1-2 session summaries in `.collab/session-summaries/`.
2. Read `.collab/kanban-board.md` for current task state.
3. Read `.collab/context.md`.
4. Deliver a concise session resume:
   - What was accomplished last session
   - What is currently In Progress or Blocked
   - What is up next
   - Any open questions or flags from the last session

Do not re-read `collab-contract.md`. Focus on current state, not process rules.

### CLOSE SESSION

When I type exactly:

    CLOSE SESSION

Immediately execute the Session Close Protocol:

1. Write a session summary to `.collab/session-summaries/`:
   - First of the day: `MM.DD.YYYY-agentname-summary.md`
   - Additional same-day: `MM.DD.YYYY-##-agentname-summary.md` (zero-padded: `02`, `03`, …)
   - Use the template at `.collab/session-summaries/session-summary-template.md`
2. Update `.collab/kanban-board.md`:
   - Move completed tasks to **Done**
   - Update in-progress task statuses
   - Add newly discovered tasks to **Inbox** or **Backlog**
3. Confirm completion to me.
