# Codex — Agent Supplement

Read this in addition to the standard onboarding prompt for your session type
(`initial-prompts/new-project/00-onboard.md` or `existing-project/00-onboard.md`).

---

## Codex-Specific Setup

1. **`AGENTS.md`** — If an `AGENTS.md` exists at the project root, it is your primary
   project instruction file. Read it before or alongside `collab-contract.md`.

2. **Memory** — Codex does not have a built-in persistent memory system. Rely on
   session summaries in `.collab/session-summaries/` and `.collab/context.md` to
   reconstruct project context at the start of each session. Keep both up to date.

3. **Handoff board** — If a `.collab/handoff-board.yaml` exists, check it for
   cross-agent task assignments before acting. Do not modify files owned by other agents
   without explicit instruction.

4. **Session hygiene** — Because you have no memory persistence, your session summaries
   are especially important. Write detailed `## What Happened` and `## Next Steps`
   sections so the next agent (or your own next session) can resume without ambiguity.
