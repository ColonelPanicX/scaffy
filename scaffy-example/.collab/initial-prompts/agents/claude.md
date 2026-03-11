# Claude Code — Agent Supplement

Read this in addition to the standard onboarding prompt for your session type
(`initial-prompts/new-project/00-onboard.md` or `existing-project/00-onboard.md`).

---

## Claude Code-Specific Setup

1. **`CLAUDE.md`** — If a `CLAUDE.md` exists at the project root, it is your primary
   project instruction file and takes precedence over generic guidance. Read it before
   or alongside `collab-contract.md`.

2. **Project memory** — Claude Code supports persistent memory. On your first session,
   use your memory tools to store stable project facts:
   - Project name and one-sentence purpose
   - Tech stack and key dependencies
   - Key file paths and entry points
   - Naming conventions and hard guardrails
   On subsequent sessions, `OPEN SESSION` is your fast-path to current state — memory
   gives you the stable foundation so you do not need to re-read everything from scratch.

3. **MCP servers** — If `.claude/` settings reference MCP servers, confirm they are
   available before starting work that depends on them. If a server is unavailable,
   report it to the user before proceeding.

4. **Hooks** — Claude Code hooks may run automatically on tool calls. If a hook blocks
   an action, investigate the cause before retrying. Do not use `--no-verify` or other
   bypass flags without explicit user approval.
