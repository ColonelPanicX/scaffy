# Kanban Board

<!--
Format:
- [ ] TASK-###: Description (@owner) [p?] [area:?] [type:?]
Examples:
- [ ] TASK-001: Draft project plan (@user) [p1] [area:planning] [type:doc]
- [ ] TASK-002: Implement exporter refactor (@claude) [p2] [area:exporters] [type:feature]
-->

## Working Rules
- The board is the source of truth.
- Don't move items to **Done** unless there is a tangible artifact (merged code / written doc / completed checklist).
- Keep **In Progress** to ~3 items max (soft WIP limit).
- If blocked, move to **Blocked** and add a short reason.
- Track one active sprint at a time (optional). Move committed sprint work into **Sprint Backlog**.
- Only move items to **To Do** if they are in the active sprint scope.

## Active Sprint (optional)
- Sprint ID: `SPRINT-YYYYMMDD`
- Dates: `MM.DD.YYYY` -> `MM.DD.YYYY`
- Goal: _one sentence_
- Exit criteria: _what must be true at sprint end_

---

## Inbox (untriaged)

## Backlog (approved, not scheduled)

## Sprint Backlog (committed scope for active sprint)

## To Do (next up)

## In Progress (doing now)

## Blocked

## In Review (awaiting user/PR review)

## Done
