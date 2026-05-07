---
title: Git Governance Playbook — Lightweight
description: Step-by-step procedures for prototypes, sandboxes, and early-stage projects
governance_mode: lightweight
---

# Git Governance Playbook — Lightweight

**When to use:** Prototypes, sandboxes, personal projects, early ideation.
**Reference:** `.collab/guides/git-guidelines.md` explains the *why* behind each mode.

> Upgrade to Standard before shipping to production or onboarding a second contributor.

---

## Starting Work

1. No issue required for small changes — commit directly to `main` or a short-lived branch.
2. For anything taking more than a session, create a branch: `feature/<slug>` or `fix/<slug>`.
3. Keep a rough record of intent in the commit message — that's your audit trail.

## Committing

- Commit early and often. No minimum quality gate.
- Use conventional commit format when practical: `feat:`, `fix:`, `chore:`, `docs:`.
- No required reviewer. Self-merge is fine.

## Opening a PR / MR

- Optional at this mode. Use when you want a change record or are unsure about a change.
- No required sections — a one-line summary is enough.

## Merging

- Merge when the work is done. No approval gate.
- Squash or merge commit — your preference.
- Delete the branch after merge if using feature branches.

## Hotfixes

- Commit directly to `main`. Document what broke and why in the commit message.

## When to Upgrade

Upgrade to Standard mode when:

- A second contributor joins.
- The project ships to a real user or production system.
- You find yourself losing track of what changed and why.

---
