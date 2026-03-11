---

# Work Item Template (Platform-Agnostic)

> Use this template for non-trivial issues/work items.
> Teams can keep all sections for Standard/Strict governance, or trim sections for Lightweight mode.

---

## Title

Recommended format:

`[<area>] <imperative, outcome-based summary>`

Examples:

- `[backend] Add pagination to report endpoint`
- `[infra] Enable branch protection for main`
- `[docs] Document release workflow`

---

## Description

Describe the problem or goal clearly.

Include:

- Current behavior (if applicable)
- Desired behavior
- Why this matters (impact, risk, user value, technical debt)

---

## Proposed Solution

Describe the intended approach.

Include when useful:

- Components/files likely affected
- Architectural considerations
- Backward compatibility or migration concerns
- Security, performance, and operational considerations

If multiple approaches are viable, list tradeoffs and preferred option.

---

## Acceptance Criteria

Use specific, testable criteria.

Example format:

- [ ] API returns paginated results with stable ordering
- [ ] Validation errors return clear messages
- [ ] Existing behavior remains unchanged for unaffected endpoints
- [ ] Documentation updated for new usage

---

## Test Plan

Describe how the change will be validated.

Include as applicable:

- Unit tests
- Integration/end-to-end tests
- Manual verification steps
- Monitoring/observability checks

If tests are intentionally deferred, explain why and add a follow-up issue.

---

## Risks and Mitigations

Document notable risks:

- Functional regressions
- Security exposure
- Performance impact
- Deployment/rollback risk

Mitigation and rollback notes:

- _Add specific rollback path if relevant_

If none, state `None`.

---

## Definition of Done

Mark complete when applicable:

- [ ] Implementation finished
- [ ] Tests added/updated (or justified)
- [ ] Docs updated (if needed)
- [ ] PR opened and linked to this issue
- [ ] Review complete
- [ ] Merged into target branch

---

## Labels and Tracking (Optional but Recommended)

Suggested label composition (Standard/Strict mode):

- 1 Priority label (e.g., `p0-critical` ... `p3-low`)
- 1 Type label (e.g., `feature`, `bug`, `refactor`, `docs`, `test`, `chore`)
- 1+ Area labels (project-specific)

Also include as relevant:

- Milestone
- Project board item
- Assignee/owner

For Lightweight mode, apply only the labels your repo actively uses.

---
