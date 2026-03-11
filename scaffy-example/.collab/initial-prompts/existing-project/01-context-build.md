# Context Build — Paste After First Onboarding

Use this prompt immediately after `00-onboard.md` to seed memory and document
the current project state before any work begins.

---

Now that you have completed your initial reconnaissance:

1. Read `.collab/context.md`. Note any fields that are empty or out of date.

2. Using what you discovered during reconnaissance, fill in or verify:
   - What this project is and what it does
   - Tech stack: languages, frameworks, key dependencies
   - Key file paths: entry points, config files, test directories
   - Naming and style conventions already in use
   - Any constraints or guardrails apparent from the codebase

3. Initialize your project memory with these stable facts (use whatever persistent
   memory mechanism your agent supports).

4. Report back to the user:
   - What you saved to memory
   - What you updated or could not determine in `context.md`
   - Any immediate risks or concerns observed during reconnaissance

Do not start any work tasks until this step is complete.
