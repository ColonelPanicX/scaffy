# Gemini — Agent Supplement

Read this in addition to the standard onboarding prompt for your session type
(`initial-prompts/new-project/00-onboard.md` or `existing-project/00-onboard.md`).

---

## Gemini-Specific Setup

1. **`GEMINI.md`** — If a `GEMINI.md` exists at the project root, it is your primary
   project instruction file. Read it before or alongside `collab-contract.md`.

2. **Memory** — Rely on session summaries in `.collab/session-summaries/` and
   `.collab/context.md` to reconstruct project context at the start of each session.

3. **Tool use** — Follow the permissions and guardrails in `collab-contract.md` for all
   function/tool calls. Prefer safe, local tools (e.g., file reads, grep) over network
   calls unless explicitly required.

4. **Session hygiene** — Write thorough session summaries at close so subsequent agents
   or sessions can resume with full context.
