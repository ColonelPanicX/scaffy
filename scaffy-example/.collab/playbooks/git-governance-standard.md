---
title: Git Governance Playbook — Standard
description: Step-by-step procedures for active product development (recommended default)
governance_mode: standard
---

# Git Governance Playbook — Standard

**When to use:** Most active projects — team delivery, side products, anything shipping to users.
**Reference:** `.collab/guides/git-guidelines.md` explains the *why* behind each mode.

---

## Starting Work

1. Confirm a work item (issue/ticket) exists. Create one if not.
2. Assign yourself and move the item to **In Progress** on the board.
3. Create a branch from the primary integration branch:
   - `feature/<slug>` or `issue-<number>-<slug>`
   - Keep branches short-lived — one concern per branch.

## Committing

- Use conventional commit format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Each commit should be coherent and buildable.
- Reference issue numbers in commits when relevant: `fix: resolve race condition (#42)`.

## Opening a PR / MR

1. Use the template at `.collab/playbooks/templates/pull-request-template.md`.
2. Required sections: **Summary**, **Why**, **Linked Work Item(s)**, **Validation**.
3. Link to the work item with `Closes #<number>` for auto-close.
4. Keep scope tight — one concern per PR.

## Merging

- **Solo maintainer:** No reviewer required. PR serves as a change record. Merge when CI passes (if applicable).
- **Multi-contributor:** One approval required before merge.
- Do not merge if required checks fail.
- Delete the branch after merge.
- Move the work item to **Done** on the board.

## Hotfixes

1. Create a `fix/<slug>` branch directly from `main`.
2. Open a PR with a minimal description — note it is a hotfix.
3. Merge with expedited review (or self-merge if solo).
4. Create a post-hoc tracking issue if one doesn't exist.

## Blocked Work

- Move the work item to **Blocked** on the board with a brief reason.
- Unblock or reassign before end of sprint/week.

---
