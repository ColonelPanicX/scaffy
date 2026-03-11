---

# Git Platform Governance & AI Agent Operating Guidelines

**Version: v1.2.0 (Unified Template)**

---

## 1. Purpose and Scope

This document defines a baseline operating model for teams and AI agents working in a Git-backed project.
It includes a platform-agnostic core plus GitHub and GitLab implementation notes in one place.

Use it as a template, not a one-size-fits-all policy.

- For highly regulated or high-risk work, use stricter controls.
- For prototypes or early discovery, use lightweight controls.

If this document conflicts with repository settings (labels, protections, automation),
treat repository settings as current truth and open a governance issue to reconcile.

---

## 2. Governance Modes

Pick one mode for the repository (or per milestone):

### Strict Mode

Use when reliability, compliance, or auditability are critical.

- Work starts only from approved work items.
- Change request-only updates to protected branches.
- Required reviews and status checks.
- Structured labels and board hygiene enforced.

### Standard Mode (Recommended default)

Use for most active product development.

- Most work starts from work items.
- Change request workflow is expected for shared branches.
- Labeling and board updates are required for meaningful work.
- Small docs/chore changes can be streamlined.

### Lightweight Mode

Use for prototypes, sandboxes, and early ideation.

- Work items are encouraged but not required for every small change.
- Minimal label policy.
- Faster iteration with fewer process gates.
- Upgrade to Standard/Strict before release hardening.

Record the active mode in README or project board notes.

---

## 3. Core Working Principle

Track work in a way that is visible and reviewable across tools.

Recommended default:

- Use work items (issues/tickets) as the planning source of truth.
- Link all non-trivial change requests (PR/MR) to a work item.
- Keep board status and labels current enough for handoff.

Minimum expectation in any mode:

- No unreviewed high-risk changes.
- No hidden work that bypasses team visibility.

---

## 4. Work Item Lifecycle

Recommended lifecycle:

`idea -> triaged work item -> assigned work -> change request -> merged -> closed`

For Standard/Strict mode, confirm before implementation starts:

1. Scope is clear and single-concern.
2. Priority and type are set.
3. Ownership is set.
4. Acceptance criteria are testable.

Approval authority should be defined by repository owners (maintainers or delegated leads).

If approval state is unclear for high-impact work, pause and ask.

---

## 5. Labels (Configurable Taxonomy)

Use labels to support planning, triage, and reporting.

Recommended composition in Standard/Strict mode:

- Exactly 1 Priority label
- Exactly 1 Type label
- 1+ Area/domain labels

Suggested defaults (customize per project):

### Priority

- `p0-critical`
- `p1-high`
- `p2-medium`
- `p3-low`

### Type

- `feature`
- `bug`
- `refactor`
- `docs`
- `test`
- `chore`

### Area (examples)

- `backend`
- `frontend`
- `infra`
- `ci-cd`
- `security`
- `performance`
- `documentation`

Label policy recommendation:

- Avoid near-duplicate labels.
- Prefer a small stable taxonomy.
- If a new label is needed, propose it in an issue first.

---

## 6. Branching and Merge Strategy

Branch strategy should match release model.

Common options:

- `main` only (trunk-based)
- `main` + `develop`
- release branches for stabilization windows

Recommended baseline:

- Use feature/fix branches for non-trivial work.
- Open change requests (PR/MR) into the primary integration branch.
- Require at least one reviewer in Standard/Strict mode.

Suggested branch names:

- `issue-<number>-<slug>`
- `feature/<slug>`
- `fix/<slug>`
- `refactor/<slug>`
- `chore/<slug>`

---

## 7. Pull Request Standards

Every change request (PR/MR) should include:

- What changed
- Why it changed
- How it was tested
- Linked work item(s)
- Risk notes (if relevant)

For higher-risk changes, include rollout and rollback notes.

Do not merge when:

- Required checks fail
- Review requirements are unmet
- Scope materially diverges from work item intent without updates

---

## 8. Project Board Usage

Board policy can be minimal or structured depending on mode.

Recommended columns:

- Inbox
- Backlog
- To Do
- In Progress
- Blocked
- In Review
- Done

If using sprints, add:

- Active Sprint metadata
- Sprint Backlog (committed scope)

Keep board updates lightweight but current enough for async coordination.

---

## 9. Exceptions and Fast Paths

Allow explicit exceptions for operational speed when needed.

Examples:

- Hotfixes
- Incident response
- Build-break recovery

When using a fast path:

1. Document why process was bypassed.
2. Link post-hoc tracking issue.
3. Follow up with normal governance cleanup.

---

## 10. Automation and Policy-as-Code

Where practical, enforce standards in platform configuration:

- Branch protection rules
- Required status checks
- CODEOWNERS
- Work item/change request templates
- Label sync automation

Keep automation aligned with the selected governance mode.

---

## 11. Platform Notes (GitHub and GitLab)

Use the core policy above as authoritative. Platform notes below define mechanics.

### GitHub Terms and Mechanics

- Work item: GitHub Issue
- Change request: Pull Request (PR)
- Recommended settings:
  - Protect primary branches (for example `main`)
  - Require pull request before merge
  - Require at least one approval (Standard/Strict mode)
  - Require status checks where CI exists
  - Restrict force pushes on protected branches
- Automation:
  - Use `Closes #<issue-number>` in PR descriptions for auto-close behavior
  - Configure templates in `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md`
  - Keep labels aligned to the core taxonomy (priority/type/area)
- Tracking:
  - If using GitHub Projects, keep item status synchronized with board columns

### GitLab Terms and Mechanics

- Work item: GitLab Issue
- Change request: Merge Request (MR)
- Recommended settings:
  - Protect primary branches (for example `main`)
  - Require merge request before merge (Standard/Strict mode)
  - Require at least one approval (Standard/Strict mode)
  - Require successful pipeline status where CI exists
  - Restrict force pushes on protected branches
- Automation:
  - Use `Closes #<issue-number>` in MR descriptions for auto-close behavior
  - Configure templates in `.gitlab/issue_templates/` and `.gitlab/merge_request_templates/`
  - Keep labels aligned to the core taxonomy (priority/type/area)
- Tracking:
  - If using GitLab Issue Boards, keep item status synchronized with board columns

In all cases, keep `.collab/kanban-board.md` synchronized as an internal fallback snapshot.

---

## 12. Review Cadence

Revisit this governance template at least quarterly or when:

- Team size changes materially
- Release process changes
- Compliance/risk posture changes
- Repeated workflow friction appears

Treat governance as maintainable system design, not static doctrine.

---

## 13. 5-Minute Adoption Checklist (New Repo)

Use this to bootstrap quickly without over-engineering.

1. Choose a governance mode:
- `Lightweight` for prototyping.
- `Standard` for normal team delivery.
- `Strict` for high-risk or compliance-heavy work.

2. Create a minimal label set:
- Priority: `p0-critical`, `p1-high`, `p2-medium`, `p3-low`
- Type: `feature`, `bug`, `refactor`, `docs`, `test`, `chore`
- Area: pick 4-8 project-relevant domains (for example `backend`, `frontend`, `infra`, `security`).

3. Configure branch protections on your primary branch:
- Require pull request before merge.
- Require at least one approval (Standard/Strict).
- Require status checks for CI where available.

4. Enable work item and change request templates:
- Use `issue-template.md` from this directory as your baseline.
- Add a PR/MR template with summary, test evidence, and linked work item.

5. Set up a basic board:
- Columns: `Inbox`, `Backlog`, `To Do`, `In Progress`, `Blocked`, `In Review`, `Done`.
- If sprint-based, also track `Active Sprint` metadata and `Sprint Backlog`.

6. Define ownership signals:
- Document who can approve/merge.
- Add CODEOWNERS for critical paths if your team is larger than one maintainer.

7. Run a lightweight governance check at end of first week:
- Are labels being used consistently?
- Are change requests linked to work items for non-trivial work?
- Are protections too strict or too loose for current velocity?

This checklist is intentionally minimal. Expand controls only where risk or team size justifies it.

---
