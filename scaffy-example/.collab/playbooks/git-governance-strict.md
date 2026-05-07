---
title: Git Governance Playbook — Strict
description: Step-by-step procedures for compliance-sensitive or high-risk projects
governance_mode: strict
---

# Git Governance Playbook — Strict

**When to use:** Compliance requirements, auditable work, high-risk or high-visibility systems.
**Reference:** `.collab/guides/git-guidelines.md` explains the *why* behind each mode.

---

## Starting Work

1. Work item must exist, be approved, and have clear acceptance criteria before work begins.
2. Assign yourself and move to **In Progress**. Do not start without an approved item.
3. Create a branch:
   - `feature/<slug>`, `fix/<slug>`, or `issue-<number>-<slug>`.
   - No direct commits to protected branches (`main`, `develop`, release branches).
4. If scope is unclear, resolve it before writing code — not during review.

## Committing

- Conventional commit format required: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`.
- Each commit must be coherent, atomic, and buildable.
- Reference issue numbers in every non-trivial commit.
- No "WIP" commits on shared branches.

## Opening a PR / MR

1. Use the full template at `.collab/playbooks/templates/pull-request-template.md`.
2. All sections required: **Summary**, **Why**, **Linked Work Item(s)**, **Scope**, **Validation**, **Risk Assessment**, **Rollout and Rollback**.
3. Risk assessment must be completed — do not leave fields blank.
4. PR must pass all CI/CD checks before review is requested.
5. `Closes #<number>` required in description.

## Merging

1. Minimum two approvals required (or one if only two contributors exist).
2. All required status checks must pass.
3. Reviewer checklist in the PR template must be completed by at least one reviewer.
4. No force pushes to protected branches.
5. Delete branch after merge.
6. Update work item to **Done** and note any follow-up items.

## Exceptions and Fast Paths

If a process bypass is unavoidable (incident response, build-break):

1. Document the reason in the commit message or PR description.
2. Tag the PR/commit with an exception label.
3. Create a follow-up issue within 24 hours for governance cleanup.
4. Note the exception in the next review cadence.

Never skip exceptions silently — the audit trail must show the bypass and the reason.

## Hotfixes

1. Create `fix/<slug>` branch from `main` (or current release branch).
2. Open a PR immediately — do not wait for work to be complete to create the PR.
3. Use the PR template with at minimum: Summary, Risk Assessment, Rollback Plan.
4. Expedited review by one qualified reviewer. Post-hoc second review within 48 hours.
5. Create post-hoc issue documenting root cause and prevention plan.

## Governance Review

Review this playbook and the project's governance posture:

- At each sprint retrospective.
- When team composition changes.
- After any incident or near-miss.
- Before entering a compliance audit period.

---
