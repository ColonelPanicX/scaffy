# First Session — New Project

Paste the block below when starting your first agent session in this project.

---

You are working in a newly initialized project with a structured `.collab/` collaboration
directory. Before doing anything:

1. Read `.collab/collab-contract.md` for rules, naming conventions, and logging requirements.
2. Read `.collab/kanban-board.md` for current task status.
3. Read `.collab/context.md` for stable project facts (fill in what you can from context).
4. Check `.collab/session-summaries/` for any prior session summaries.
5. The kanban board is empty — this is a newly initialized project. Wait for the user to
   describe goals before drafting plans or tasks.

If your agent type has a supplement in `.collab/initial-prompts/agents/`, read it now.

---

## Session Protocols

### OPEN SESSION

When the user types exactly:

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

When the user types exactly:

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
3. Confirm completion to the user.
